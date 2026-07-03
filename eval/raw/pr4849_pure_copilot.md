- **Correctness**: The change correctly adapts the bridge to the new single-request-per-output contract.  
  - `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:97‑229`: The loop over `source_outputs` is removed; only the parent output (`source_outputs[0]`) is processed. This matches the orchestrator’s new behaviour (`[parent, *cfg_companions]`).  
  - Return type changed from `list[dict]` to `dict | None`, aligning with the contract that a list now represents the banned list‑prompt API.  

- **Scope**: The change is isolated to the HunyuanImage3 AR‑to‑diffusion bridge and its tests. No other models or core code are affected.  

- **Risk**: Low. The bridge now returns exactly one payload (or `None`) per invocation, which is the expected interface. Genuine multi‑request batching remains unsupported, as intended.  

- **Edge cases**:  
  - `ar_output.outputs` empty → `IndexError` (same as before, not introduced).  
  - `prompt` passed as a list with multiple elements → only the first prompt is used, which is correct because CFG companions share the same prompt.  
  - `prompt` is a list containing `None` → could cause `AttributeError` later, but this scenario was already fragile in the old code and is not expected in normal usage.  

- **Test updates**:  
  - `tests/model_executor/stage_input_processors/test_hunyuan_image3_bridge.py:48‑118`: New tests for single‑payload contract, parent‑first logic, and empty input → `None`.  
  - `tests/diffusion/models/hunyuan_image3/test_multi_resolution.py:527‑636`: Updated assertions from list to dict, no functional regression.  

- **No unintended behaviour**: The function no longer creates multiple independent diffusion requests, which is exactly what the error in #4832 demanded.