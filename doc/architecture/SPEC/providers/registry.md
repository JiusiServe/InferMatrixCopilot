# providers/registry.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~107 · backend resolution (the one table) · refactor-status: ok`

## Responsibility
The single table of ways to reach a model, and the only resolution path from
configuration to a transport.

## Functionality
Declares `PROVIDERS` (five `ProviderSpec` entries: `api`, `cursor`,
`claude-code`, `codex`, `deepseek`), resolves the selected one from
`Settings.strict_backend`, and hands back a `HarnessTransport` for harness
kinds. Declared-but-unshipped backends live in `_UNSHIPPED` and raise a
milestone pointer instead of returning a transport that cannot work.

## Public contract
`PROVIDERS`, `resolve_provider(settings)`, `transport_for(settings)`,
`transport_for_id(settings, provider_id)`.

## Invariants (**C2**, **B1**)
- **One resolution path.** The pre-existing raw-API path is provider `api`
  inside this same table — not a parallel branch. With `api`, behaviour is
  byte-identical to before the registry existed (the parity ratchet).
- **Unknown ids never resolve silently.** `resolve_provider` raises listing the
  legal set; `Settings` rejects them upfront as well. Two layers, because a
  typo in `.env` must not start a doomed run.
- **`api` has no transport.** `transport_for_id` raises for it by design:
  resolution for the API path stays with `Settings.tier_target`/`llm.LLM`.
- **Unshipped ≠ broken.** An id in `_UNSHIPPED` raises `NotImplementedError`
  naming its milestone, so `strict_readiness`/doctor report "not yet shipped"
  rather than failing mid-flight.
- `transport_for_id` resolves an EXPLICIT id independent of the run's
  `STRICT_BACKEND` — the seam MoA harness members use to ride a harness inside
  an api-backed run.

## Scope — not here
No transport implementation (each `providers/<id>.py` owns its own); no
credential handling; no model selection (that is `Settings.tier_target`).

## Dependencies (allowed)
`.base` only. Transport modules are imported lazily inside `transport_for_id`
so that installing one backend's SDK is never a precondition for another.

## Extension points
Add a `ProviderSpec` + a `HarnessTransport` subclass + one branch in
`transport_for_id`. Register in `_UNSHIPPED` first if the transport is not
ready.

## Tests
`test_providers.py`; per-backend `test_provider_{cursor,claude_code,codex,deepseek}.py`.

## Refactor notes
The `transport_for_id` if-chain is the one place that grows per backend; a dict
of id → import path would remove the branching but obscure the lazy-import
intent. Keep the chain until it exceeds ~8 entries.
