---
title: "上游 API 漂移模式（权重加载 / 显存 / 运行时侧）"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, rebase]
sources: ["vllm-omni-rebase-agent@122a9468:agent/skills/fix-hunyuanimage3-moe-weight-loading-keyerror/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/fix-diffusion-fp8-meta-tensor-weight-loading/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/fix-cumem-cuda-double-free-gc-atexit/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/resolve-moss-tts-nano-load-weights-conflict/SKILL.md"]
---

# 上游 API 漂移模式（权重加载 / 显存 / 运行时侧）

serving/调度/测试侧的漂移在[姊妹页](upstream-api-drift.md)。运营 runbook 以
rebase-agent 仓库为准，本页是知识树沉淀快照（2026-07-16，agent @122a9468；
skills 工作树含未提交遥测更新，快照以工作树为准）。

## 1. FusedMoE 类 → 工厂函数：adapter 必须直接返回 MoERunner

skill 元数据：`fix-hunyuanimage3-moe-weight-loading-keyerror`，
modules=[model_executor]，status=active，run_count=29，2026-06-09 创建 / 07-11
最后使用。

- 症状：HunyuanImage3 测试
  `KeyError: 'layers.N.mlp.experts.routed_experts.w13_weight'`（或 `w2_weight`），
  位置 `HunyuanModel.load_weights`——`named_parameters()` 找不到 MoE runner 的
  expert 权重。
- 根因：upstream `dc68bd8c41` 把 `FusedMoE` 从 `nn.Module` 类重构为返回
  `MoERunner` 的**工厂函数**；expert 权重住在 `routed_experts` 子模块。若 adapter
  把 runner 包进普通（非 `nn.Module`）对象，`named_parameters()` 看不见其参数 →
  `load_weights` KeyError。另：vLLM 0.18.0 起 `FusedMoE` 每次 forward 前必须设
  `ForwardContext.num_tokens`——不设则 MoE 专家路由**静默错误**。
- 反模式（禁止）：`if name_mapped not in params_dict: continue`——静默跳过未映射
  权重 → 参数未初始化 → 静默推理错误。
- 修法（参照 `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_fused_moe.py`
  `HunyuanFusedMoEDefault.__new__`）——skill 原文代码：

  ```python
  def __new__(cls, *, prefix: str = "", **kwargs: Any) -> Any:
      from vllm.model_executor.layers.fused_moe import FusedMoE as _FusedMoE

      moe_runner = _FusedMoE(prefix=prefix, **kwargs)

      # Hook 1: 每次 forward 前设 ForwardContext.num_tokens（vLLM 0.18.0 必需；
      # 不设则 MoE 路由静默错误）。hidden_states 兼容 kwargs 与位置参数。
      def _num_tokens_pre_hook(module: Any, args: Any, kwargs: Any) -> None:
          hidden_states = kwargs.get("hidden_states")
          if hidden_states is None and args:
              hidden_states = args[0]
          if hidden_states is not None:
              _set_forward_context_num_tokens(hidden_states.shape[0])

      moe_runner.register_forward_pre_hook(_num_tokens_pre_hook, with_kwargs=True)

      # Hook 2: 首次 forward 的一次性懒 kernel 初始化——仅当 runner 暴露未初始化
      # quant_method 时生效（镜像旧 wrapper 行为，只是绑定到 runner 模块本身）。
      init_handle: Any = None

      def _kernel_init_pre_hook(module: Any, args: Any, kwargs: Any) -> None:
          nonlocal init_handle
          quant_method = getattr(module, "quant_method", None)
          if quant_method is not None and getattr(quant_method, "moe_kernel", None) is None:
              quant_method.process_weights_after_loading(module)
          if init_handle is not None:
              init_handle.remove()

      init_handle = moe_runner.register_forward_pre_hook(_kernel_init_pre_hook, with_kwargs=True)

      return moe_runner  # 直接返回——必须是真正的 nn.Module
  ```
  另：`make_expert_params_mapping` 改为委托 upstream 独立函数
  `fused_moe_make_expert_params_mapping`（重构中 classmethod 被移出为独立函数）。
- 验证：`python3 -c "from vllm_omni.diffusion.models.hunyuan_image3.hunyuan_fused_moe
  import HunyuanFusedMoE; print('OK')"`；
  `python3 -m pytest tests/diffusion/models/hunyuan_image3/ -x -v 2>&1 | tail -20`。
- Watch out：runner 必须从 `__new__` 直接返回——包一层就复现本 KeyError；
  `_set_forward_context_num_tokens` 不存在时需定义（见现实现）。
  ^[SK-fix-hunyuanimage3-moe-weight-loading-keyerror]

## 2. FP8 在线量化 meta-tensor：加载器要按 upstream base_loader 合同分路

skill 元数据：`fix-diffusion-fp8-meta-tensor-weight-loading`，
modules=[diffusion_model_loader, quantization, worker_runner]，status=active，
run_count=5，2026-07-08 创建 / 07-11 最后使用。

- 症状：diffusion FP8 测试（`test_single_stage_qwen_image_fp8`、
  `test_bagel_fp8_generates_image`、fp8 vae_patch_parallel serving）pytest 层报
  `RuntimeError: Server processes exited with code 1 before becoming ready`；
  真实崩溃在 spawn 的 `DiffusionWorker` 子进程——job 日志里
  `NotImplementedError: Cannot copy out of meta tensor; no data! Please use
  torch.nn.Module.to_empty()`，位置 `diffusers_loader.py`
  `_process_weights_after_loading`（~416 行）`module.to(target_device)`；父进程
  随后 `multiproc_executor ... reader.recv() -> EOFError` +
  `Orchestrator initialization failed`。**只在 rebase 到新 upstream 后出现**——
  同测试在 main 的 nightly（老 vLLM）通过（用 Buildkite API 对比：main nightly
  pipeline `vllm-omni` source=schedule NIGHTLY=1 vs align 的 `vllm-omni-rebase`）。
- 根因：新 upstream 在线量化 linear method 设 `uses_meta_device = True`
  （`vllm/model_executor/layers/quantization/online/fp8.py`），权重先分配在
  `meta` 设备、经 layerwise 在线处理（`initialize_online_processing`）逐层
  即时物化；"掉队"层（padding/部分加载）留在 meta。omni 的
  `_process_weights_after_loading` 做全递归 `module.to(target_device)`——meta
  张量不可 move。模型相关：Z-Image FP8 全物化（过）；Qwen-Image/BAGEL FP8 留
  掉队层（崩）。注意该循环遍历所有 `quant_method isinstance QuantizeMethodBase`
  的模块（含 `UnquantizedLinearMethod`），但只有 meta（在线量化）参数触发崩溃。
- 修法（`diffusers_loader.py::_process_weights_after_loading`，镜像 upstream
  `base_loader` 合同）：
  1. 循环前，仅当 `self._has_online_quant(model)` 时调
     `finalize_layerwise_processing(model, model_config=None)`（懒 import
     `vllm.model_executor.model_loader.reload.layerwise`；`model_config=None`
     可行——只有 vLLM Attention/MLA 层用到它，DiT 没有）。helper 原文：

  ```python
  @staticmethod
  def _has_online_quant(model):
      for m in model.modules():
          if getattr(getattr(m, "quant_method", None), "uses_meta_device", False):
              return True
      return False
  ```
  2. **把 meta-safe 的逐参数搬运 gate 在在线量化上**——skill 原文代码
     （`has_online_quant` 在循环前算一次）：

  ```python
  for _, module in model.named_modules():
      quant_method = getattr(module, "quant_method", None)
      if quant_method is None or not isinstance(quant_method, QuantizeMethodBase):
          continue
      if has_online_quant:
          original_devices = {}
          for name, param in module.named_parameters():
              if param.device.type != "meta" and param.device != target_device:
                  original_devices[name] = param.device
                  param.data = param.data.to(target_device)
          quant_method.process_weights_after_loading(module)
          for name, param in module.named_parameters():
              if name in original_devices:
                  param.data = param.data.to(original_devices[name])
      else:
          # 原 FSDP/HSDP-aware 路径（此处不可能有 meta 参数）
          module_device = next(module.parameters(), None)
          module_device = module_device.device if module_device is not None else None
          needs_move = module_device != target_device
          if needs_move:
              module.to(target_device)
          quant_method.process_weights_after_loading(module)
          if needs_move:
              module.to(module_device)
  ```
- 验证：单元层——一个 cpu 参数 + 一个 `torch.empty(..., device="meta")` 参数的
  模块走逐参数循环无 `NotImplementedError`、真实参数 move+还原、对 meta 参数
  `module.to()` 仍会 raise（证明旧路径就是 bug）；端到端——重跑 nightly
  `Quantization Test`（H100+L4）与 `Diffusion ... Qwen-Image`
  （fp8 vae_patch_parallel_2）变绿，**且**测试自身的图像断言（有效 PIL/SSIM）
  必须过——"用垃圾物化"的错修只救 crash、救不了精度断言。
- 禁止：把逐参数 `.data.to()` **无条件**用于所有 quant 模块——FSDP/HSDP 路径下
  参数是 sharded DTensor，跨设备 `.data` 重指存储直接
  `RuntimeError: Attempted to set the storage ...`（曾回归 nightly
  `test_zimage[layerwise_hsdp]`）；用 `module.to_empty(device=...)` "修"——分配
  **未初始化**内存，静默产出垃圾权重/图像（crash 检查过、精度挂）；把
  Dockerfile.ci 的 cu130/torch-2.11.0 环境回退到 main 版本换取通过——main 跑老
  vLLM（v0.24.0 tag），align 分支的目标就是新 upstream（领先 585 提交），回退
  环境等于放弃 rebase 目标，修复属于 loader 代码；顶层无条件 import
  `finalize_layerwise_processing`——老 vLLM 没有 `reload.layerwise`，须在
  `_has_online_quant` guard 内懒 import。
  ^[SK-fix-diffusion-fp8-meta-tensor-weight-loading]

## 3. cumem 双重释放：ROCm-only guard 是根因（canonical + 退役史）

skill 元数据：`fix-cumem-cuda-double-free-gc-atexit`（**canonical**），
modules=[online_serving]，status=active，run_count=5，2026-07-08 创建 / 07-11
最后使用。

- 症状：`CUDA Error: invalid argument at /workspace/csrc/cumem_allocator.cpp:235`
  在引擎关停时出现（`test_llm_sleep_ack` 或任何 `enable_sleep_mode=True` 测试后）；
  **所有单测 PASS** 但 watchdog rc=143；错误发生在 EngineCore 子进程
  （StageEngineCoreProc）的 atexit 清理；此前可见 `CuMemAllocator: sleep freed`。
- 根因：`CuMemAllocator._python_free_callback`
  （`vllm/device_allocator/cumem.py:206`）的
  `if data.is_asleep and current_platform.is_rocm():`——upstream `68afd78897`
  只给 ROCm 加了安全空 handle 返回；CUDA 上回调对已 asleep 的条目返回**陈旧**
  handle → C 扩展对已释放内存 `cuMemRelease`。链路：worker `allocator.sleep()`
  → `unmap_and_release(handle)`、`is_asleep=True` → 子进程退出 atexit
  `_shutdown_singleton` → `release_pools()` → GC → `_python_free_callback` →
  CUDA 返回陈旧 handle → 报错。
- 修法：`vllm_omni/patch.py` 增 `_patch_cumem_free_callback_cuda()` 并**在模块内
  显式调用**——skill 原文代码（本质就是去掉 `and current_platform.is_rocm()`，
  两平台行为一致，因为 `sleep()` 在两平台都走 `unmap_and_release()`）：

  ```python
  def _patch_cumem_free_callback_cuda() -> None:
      from vllm.device_allocator.cumem import CuMemAllocator

      def _patched_free_callback(self, ptr: int) -> tuple:
          data = self.pointer_to_data.pop(ptr)
          if data.cpu_backup_tensor is not None:
              data.cpu_backup_tensor = None
          if data.is_asleep:
              device, size, d_mem, _ = data.handle
              return (device, size, d_mem, [])
          torch.accelerator.synchronize(data.handle[0])
          return data.handle

      CuMemAllocator._python_free_callback = _patched_free_callback

  _patch_cumem_free_callback_cuda()
  ```

- 验证（skill 原文可执行片段，期望输出 `OK: Patched correctly`）：

  ```python
  import vllm_omni.patch
  from vllm.device_allocator.cumem import CuMemAllocator
  import inspect
  src = inspect.getsource(CuMemAllocator._python_free_callback)
  assert "is_rocm" not in src, "ROCm-only guard still present"
  print("OK: Patched correctly")
  ```
- 禁止：只在引擎关停调用点把 `allocator.sleep()` 换成 `release_pools()`（退役的
  旧修法）——`release_pools()` 仍驱动 GC → 回调在 CUDA 返回陈旧 handle，
  atexit 路径照样双重释放。**回调补丁是覆盖全部路径（显式 sleep、
  release_pools、atexit GC）的唯一根修。**
  ^[SK-fix-cumem-cuda-double-free-gc-atexit]
- 退役史（保留供追溯）：skill `fix-cumem-allocator-sleep-double-free`
  （modules=[online_serving, worker_runner]，**status=retired**，run_count=2，
  2026-07-07 创建 / 07-07 最后使用；retired 状态**不会向 agent 展示**，仅存档）主张在 `async_omni_engine.py`（~1536 行）换调用点——其原理陈述
  有误（声称 `release_pools()` 是设计好的清理路径——释放 MemPool 引用并触发 GC，
  回调对 asleep 条目返回空 handle『CUDA 上 0、ROCm 上 []』、由 C 扩展的
  `p_memHandle != nullptr` 空指针检查跳过双重释放；实际 CUDA 上回调返回**陈旧**
  handle），修法不完整、已被 canonical skill 取代；其诊断细节（cpp:235 对应
  `unmap_and_release()` 的 `cuMemRelease(*p_memHandle)`、`sleep()` 非幂等：
  首次 sleep C 侧 `free(p_memHandle)` 后 `data.handle[3]` 仍持旧指针整数值、
  回归测试 `test_llm_sleep_ack` + `test_duplicate_wake_is_idempotent`，验收含
  stderr 无 CUDA 错误、全部测试通过且 watchdog 不杀进程）仍有效。
  同事件的 debug-memory #437（key=`allocator_sleep_double_free_shutdown`，
  module=online_serving，status=active，run_count=1）记录同一诊断链，其修法
  即被取代的调用点替换；其 watch-out 仍适用：排查是否还有别的代码路径对已
  asleep 的 allocator 重复调 `allocator.sleep()`——upstream `cumem.py` 的
  `sleep()` 理想上应幂等，但那是 upstream 代码、不能本地改。
  ^[SK-fix-cumem-allocator-sleep-double-free] ^[DM-437]

## 4. rebase 冲突：drain-only vs 全量 from_pretrained（moss_tts_nano 模式）

skill 元数据：`resolve-moss-tts-nano-load-weights-conflict`，
modules=[model_executor]，status=active，run_count=24，2026-06-10 创建 / 07-11
最后使用。

- 触发：`modeling_moss_tts_nano.py` 的 `load_weights()` 出现
  `<<<<<<< HEAD ... >>>>>>>` 冲突——HEAD 侧是 drain-only
  （`for _ in weights: pass`），omni 侧是带
  `_transformers_keys_to_ignore_compat()` 包装的全量 `from_pretrained` 加载。
- 判定：查 `__init__` 是否已经通过 `from_pretrained` **急切加载**了模型——
  是则 `load_weights` 只需要清空迭代器。
- 修法：1) load_weights **取 HEAD**（drain-only），签名保持
  `def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]`
  ——注释注明权重在 `__init__` 已加载、`load_format=dummy` 下不会调用本函数
  （DummyModelLoader 原地随机化参数），`for _ in weights: pass` 后返回
  `{name for name, _ in self.named_parameters()}`；
  2) 把 `_transformers_keys_to_ignore_compat()` 包装**移进 `__init__`**，
  包住两处 `from_pretrained`（`AutoModelForCausalLM` 的 LM 加载 +
  `AutoModel` 的 audio tokenizer 加载）；3) 核对无冲突标记、语法与 import 正常。
  ^[SK-resolve-moss-tts-nano-load-weights-conflict]

## 相关

- serving/调度/测试侧漂移：[姊妹页](upstream-api-drift.md)；
  波次与失败路由：[workflow](workflow.md)；FusedMoE/权重案例的模型页：
  [hunyuan-image3](../models/hunyuan-image3/_index.md)。
