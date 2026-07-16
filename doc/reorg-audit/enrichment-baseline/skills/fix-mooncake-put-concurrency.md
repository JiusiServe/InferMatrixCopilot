---
name: fix-mooncake-put-concurrency
description: Fix thread-safety issue in MooncakeTransferEngineConnector.put() by adding a per-connector serialization lock
trigger: MD5 mismatch, data corruption, or assertion error in test_concurrent_put_get_integrity or similar concurrent put/get stress tests for MooncakeTransferEngineConnector
modules: [scheduler, distributed]
status: active
created_at: 2026-06-12
last_used_at: 2026-07-11
run_count: 23
---

## Diagnose
1. Check if the failing test involves concurrent put() calls on the same MooncakeTransferEngineConnector instance
2. Look for MD5 mismatch errors (data integrity issues) that are non-deterministic (pass on some runs, fail on others)
3. Verify no code changes were made to the connector between passing and failing runs
4. The root cause is that put() is not thread-safe for concurrent calls

## Fix
1. Add `self._put_lock = threading.Lock()` in `MooncakeTransferEngineConnector.__init__`
2. Extract the put() method body into `_put_impl()` (private method with same signature minus from_stage/to_stage)
3. In put(), wrap the call with `with self._put_lock: return self._put_impl(...)`

## Verification
- Import check: `from vllm_omni.distributed.omni_connectors.connectors.mooncake_transfer_engine_connector import MooncakeTransferEngineConnector`
- The scheduler module imports transitively depend on this connector, verify: `from vllm_omni.core.sched.omni_ar_scheduler import OmniARScheduler`
