---
name: fix-mooncake-tcp-deserialize-leading-byte
description: Fix non-fast-path object deserialization failure in MooncakeTransferEngineConnector when Mooncake TCP/memcpy transport prepends a leading protocol byte
trigger: test_object_e2e test fails with msgspec.DecodeError: trailing characters (byte 1). Only the object (non-fast-path) transfer fails; all bytes/tensor (fast-path) tests pass.
modules: [scheduler, distributed]
status: active
created_at: 2026-06-17
last_used_at: 2026-07-11
run_count: 15
---

## Diagnose
1. Check the failing test is `test_mooncake_transfer_engine_rdma.py::TestEndToEnd::test_object_e2e`
2. Verify the error is "msgspec.DecodeError: MessagePack data is malformed: trailing characters (byte 1)"
3. Confirm all fast-path tests (tensor, bytes, zero-copy) pass
4. The error means the received data has a leading 0x01 byte (fixint=1) before the serialized payload, causing msgpack.Decoder to consume it as a single-byte value and treat the rest as trailing

## Root Cause
Mooncake TransferEngine's TCP/memcpy fallback (`MC_STORE_MEMCPY`) prepends a protocol byte (0x01) before the actual data payload during `batch_transfer_sync_write`. The receiver only reads `data_size` bytes (the expected payload size), getting `0x01` + first `data_size-1` bytes of the actual payload.

## Fix
In `mooncake_transfer_engine_connector.py`, `get()` method:

### Step 1: Padding allocation
For `is_fast_path=False`, allocate `data_size + 4` bytes instead of `data_size`:
```python
_MOONCAKE_TCP_PADDING = 4 if not is_fast_path else 0
alloc_size = data_size + _MOONCAKE_TCP_PADDING
offset = self.allocator.alloc(alloc_size)
recv_buffer = ManagedBuffer(self.allocator, offset, alloc_size, self.pool)
```

### Step 2: Retry deserialization with offset
Try offset 0 first. On DecodeError, retry from offset 1:
```python
payload = raw_bytes[:data_size]
try:
    val = OmniSerializer.deserialize(payload)
except msgspec.DecodeError:
    payload = raw_bytes[1:data_size + 1]
    val = OmniSerializer.deserialize(payload)
```

## Verification
Run the full mooncake connector test suite:
```
pytest -sv tests/distributed/omni_connectors/test_mooncake_transfer_engine_rdma.py
```
Expected: 24 passed, 0 failed.

## Watch outs
- The padding is only applied for non-fast-path (serialized objects), not for fast-path (bytes/tensor/ManagedBuffer).
- The retry is defensive: try offset 0 first (works when Mooncake doesn't prepend the byte), then offset 1.
- If Mooncake fixes the TCP protocol byte upstream, the padding and retry can be removed.
