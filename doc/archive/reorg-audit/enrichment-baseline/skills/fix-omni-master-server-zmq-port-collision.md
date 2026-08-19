---
name: fix-omni-master-server-zmq-port-collision
description: Fix flaky multi-stage startup where two stages draw the same ZMQ port — OmniMasterServer allocated route ports per-call without cross-route dedup, so a later stage could reuse an earlier one and die on bind with EADDRINUSE.
trigger: Flaky (passes on retry / one shard passes, another fails) "RuntimeError: Orchestrator initialization failed: Address already in use (addr='tcp://127.0.0.1:PORT')" or "zmq.error.ZMQError: Address already in use" during stage startup, "Stage N replica M exited with code 1 before API server became ready". Hits multi-stage models most (Qwen3-Omni thinker/talker/code2wav). Test passes on main but flakes on the rebase branch.
modules: [online_serving, engine]
status: active
created_at: 2026-07-10
last_used_at: 2026-07-10
run_count: 0
---

## Diagnose

1. Confirm the failure is a ZMQ bind collision, not a real crash: stage log tail shows
   `zmq.error.ZMQError: Address already in use (addr='tcp://127.0.0.1:<port>')` wrapped as
   `RuntimeError: Orchestrator initialization failed: Address already in use`.
2. Confirm it is **flaky**, not deterministic: check Buildkite for the same job passing on a
   parallel shard or on retry, and passing on the `main` baseline build. One shard PASS + one
   shard FAIL on the same commit ⇒ a port race, not a code regression.
3. It concentrates on **multi-stage** models. Each `(stage_id, replica_id)` route allocates 3
   ports (handshake/input/output) via a separate `get_open_ports_list(count=3)` call in
   `vllm_omni/engine/stage_engine_startup.py::OmniMasterServer._allocate_route_locked`.
   `get_open_ports_list` (upstream `vllm.utils.network_utils`) only dedups **within one call** —
   it binds port 0, reads the port, closes. Across separate calls the OS can hand back a
   recently-closed ephemeral port, so two routes get the same number; whichever engine subprocess
   binds it second dies with EADDRINUSE.

## Fix

Make `OmniMasterServer` dedup every port it hands out across all routes.

1. In `__init__`, add `self._allocated_ports: set[int]` seeded with the registration port
   (`master_port`) and, if present, the coordinator ROUTER port parsed from
   `coordinator_router_address` (they are already bound on the same host).
2. Add a module helper `_port_from_zmq_address(addr)` that extracts the port from a
   `tcp://host:port` address (returns `None` for `ipc://`/`inproc://`/unparsable).
3. Add `OmniMasterServer._alloc_unique_ports(count)`: draw from `get_open_ports_list`, skip any
   port already in `self._allocated_ports`, register the winners, and redraw collisions with a
   bounded retry budget (raise `RuntimeError` on exhaustion — never spin forever).
4. Replace `hs_port, inp_port, out_port = get_open_ports_list(count=3)` in
   `_allocate_route_locked` with `self._alloc_unique_ports(3)`.

This eliminates the intra-server cross-route self-collision deterministically. A cross-process
steal by an unrelated process on the box is still theoretically possible but is far rarer and out
of this server's control.

## Verification

CPU-only, no GPU/model needed:

```bash
cd /rebase/vllm-omni
/rebase/.venv/bin/python -m pytest tests/engine/test_async_omni_engine_stage_init.py \
  -k "unique_route_ports or port_from_zmq" -q
```

Expected: the two regression tests pass. `test_omni_master_server_allocates_globally_unique_route_ports`
feeds a colliding port stream (`get_open_ports_list` monkeypatched to repeat ports + the master
port) and asserts all 9 route ports across 3 stages are distinct and none equals the master port.
Also run the whole file to confirm no regression: `... test_async_omni_engine_stage_init.py -q`
(26 passed).

## Anti-patterns

- **Do NOT** treat this as a real regression and start patching the model / generation code — it
  is a port race. Check for a passing parallel shard / retry / main baseline first.
- **Do NOT** just add a blind retry loop around the engine subprocess `bind()` — the bind address
  is shared with the connect side (peer), so re-picking a port there needs re-coordination with
  the master; fix it at allocation time instead.
- **Do NOT** rely on `get_open_ports_list` for global uniqueness across multiple calls — it only
  dedups within a single call.
- **Do NOT** make the redraw loop unbounded — cap the retries and raise on exhaustion so port
  exhaustion fails loudly instead of hanging.
