---
name: fix-hunyuanimage3-moe-weight-loading-keyerror
description: Fix KeyError during HunyuanImage3 expert weight loading after upstream MoE refactoring — return MoERunner directly with forward pre-hooks, NOT skip weights
trigger: KeyError containing 'layers.N.mlp.experts.routed_experts.w13_weight' or 'w2_weight' in HunyuanImage3 tests
modules: [model_executor]
status: active
created_at: 2026-06-09
last_used_at: 2026-07-11
run_count: 29
---

## Diagnose

1. The error `KeyError: 'layers.N.mlp.experts.routed_experts.w13_weight'` occurs in `HunyuanModel.load_weights` because `named_parameters()` cannot find the MoE runner's expert weights.

2. Root cause: Upstream vLLM (dc68bd8c41) refactored `FusedMoE` from a class (`nn.Module`) to a **factory function** returning a `MoERunner` instance. The expert weights live in a `routed_experts` submodule (`...experts.routed_experts.w13_weight` / `...w2_weight`). If the MoE runner is wrapped in a plain (non-`nn.Module`) object, `named_parameters()` cannot see the runner's parameters, causing `load_weights` to raise `KeyError`.

3. Additionally, after vLLM 0.18.0, `FusedMoE` requires `ForwardContext.num_tokens` to be set before each forward — without it, MoE expert routing is **silently incorrect**.

## Anti-pattern (DO NOT DO THIS)

```python
# WRONG: silently skips unmapped weights → uninitialized parameters → silent inference errors
if name_mapped not in params_dict:
    continue
```

## Fix

The MoE adapter's `__new__` must return the `MoERunner` **directly** (not wrapped) so its parameters are visible to `named_parameters()`. Two pre-hooks handle kernel init and forward-context setup.

Reference: `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_fused_moe.py` — `HunyuanFusedMoEDefault.__new__`.

```python
def __new__(cls, *, prefix: str = "", **kwargs: Any) -> Any:
    from vllm.model_executor.layers.fused_moe import FusedMoE as _FusedMoE

    moe_runner = _FusedMoE(prefix=prefix, **kwargs)

    # Hook 1: Set ForwardContext.num_tokens before each forward.
    # Required by vLLM 0.18.0 FusedMoE; without it MoE routing is silently incorrect.
    def _num_tokens_pre_hook(module: Any, args: Any, kwargs: Any) -> None:
        hidden_states = kwargs.get("hidden_states")
        if hidden_states is None and args:
            hidden_states = args[0]
        if hidden_states is not None:
            _set_forward_context_num_tokens(hidden_states.shape[0])

    moe_runner.register_forward_pre_hook(_num_tokens_pre_hook, with_kwargs=True)

    # Hook 2: One-shot lazy kernel initialisation on the first forward.
    # No-op unless the runner exposes an uninitialised quant_method.
    # Mirrors the prior wrapper behaviour exactly, just bound to the runner module.
    init_handle: Any = None

    def _kernel_init_pre_hook(module: Any, args: Any, kwargs: Any) -> None:
        nonlocal init_handle
        quant_method = getattr(module, "quant_method", None)
        if quant_method is not None and getattr(quant_method, "moe_kernel", None) is None:
            quant_method.process_weights_after_loading(module)
        if init_handle is not None:
            init_handle.remove()

    init_handle = moe_runner.register_forward_pre_hook(_kernel_init_pre_hook, with_kwargs=True)

    return moe_runner  # returned directly — must be a real nn.Module
```

The `make_expert_params_mapping` static method should also delegate to the upstream standalone function `fused_moe_make_expert_params_mapping` (the classmethod was moved to a standalone function during the refactoring).

## Verification

- `python3 -c "from vllm_omni.diffusion.models.hunyuan_image3.hunyuan_fused_moe import HunyuanFusedMoE; print('OK')"`
- `python3 -m pytest tests/diffusion/models/hunyuan_image3/ -x -v 2>&1 | tail -20`

## Watch Out

- The runner MUST be returned directly from `__new__` — wrapping it in a plain object hides its parameters from `named_parameters()` and causes the exact `KeyError` this skill addresses.
- `quant_method.moe_kernel` may already be initialized in some runner configurations; the `_kernel_init_pre_hook` checks `moe_kernel is None` before calling `process_weights_after_loading`, so the hook is a safe no-op when initialization has already happened.
- If `_set_forward_context_num_tokens` doesn't exist, define it (see the existing implementation in `hunyuan_fused_moe.py`).
