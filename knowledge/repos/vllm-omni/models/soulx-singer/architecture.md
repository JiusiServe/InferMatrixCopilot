---
title: "SoulX-Singer 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/soulx_singer/pipeline_soulx_singer_base.py, vllm_omni/diffusion/models/soulx_singer/pipeline_soulx_singer_svs.py, vllm_omni/diffusion/models/soulx_singer/pipeline_soulx_singer_svc.py, vllm_omni/diffusion/models/soulx_singer/utils.py]
---

# SoulX-Singer 架构

事实在 `main @ 5d44868e` 复核;入口/命名陷阱速览见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- 共享基类 `FlowMatchingAudioPipeline`：24 kHz,`_DEFAULT_RESCALE_CFG 0.75`;
  DiT 估计器是 NAR Llama 变体（`DiffLlama`/`LlamaNARDecoderLayer`）+ CFM
  解码器;Vocos 系声码器。**自管权重**：`weights_sources=()` 完全绕开框架
  diffusers loader,`.pt` 在 `__init__` 里 strict 加载;fp16 部署内 mel+
  vocoder 强制 fp32（`_build_fp32_audio_modules`）。
- SVS 专有:note 三编码器（音素/音高/类型）+ preflow ConvNeXtV2 + f0
  编码器;条件经 `mel2note` gather 扩到 mel 帧（溢出 warn+clamp）。
- SVC 专有:冻结 **Whisper 编码器**特征（prompt+target）+ 粗 F0 嵌入
  （361 bin,`f0_to_coarse`）。
- 神经预处理栈（`modules/preprocess/`,注意与同级的非神经 `preprocess/`
  helper 目录区分）：funasr、NeMo Parakeet（带 CUDA-graph 禁用
  workaround）、BS-RoFormer pip 包这些外部依赖**只被预处理使用**;
  `VocalSegmenter` 是规则式(非 NN)。
- 共享框架面：[Diffusion 组件](../../components/diffusion/_index.md)
  （CFGParallelMixin——guidance 可跨卡分片,默认单卡）。

## 配置、checkpoint 和兼容范围

- kind 判定：checkpoint config.json `architectures` ==
  `["SoulXSingerPipeline"]`（SVS）或 `["SoulXSingerSVCPipeline"]`（SVC）
  （`utils.py::resolve_soulx_kind`）;extra_args 按 kind 白名单校验。
- 权重根:`resolve_preprocess_weights_root`（双仓布局）;
  `phoneme/phone_set.json` 必须手工从 GitHub 拷入。deploy YAML **不含
  checkpoint ID**,离线 README 要求分别建 SVS/SVC 的 "view" 目录。
- 两个模块各定义同名 `get_soulxsinger_post_process_func`——registry 按各自
  模块解析,但重名对 `_DIFFUSION_MODELS` 映射改动脆弱（评审注意）。

## 从输入到输出的主要流程

1. **三层输入分级**（`pre_process_func`）：原始音频（首见时懒建预处理栈,
   按变体内联跑——分离是 `vocal_sep` 可选;SVS 加 ASR+MIDI,SVC 加 RMVPE
   F0）产出音频/F0 载荷 / 预计算载荷（`has_precomputed`）/ warmup 哑载荷;
   产物统一挂在 `prompt.additional_information["soulx_preprocessed"]`。
2. 条件构建:SVS 走乐谱/音素路径;**SVC 在此阶段用冻结 Whisper 提特征**
   （强制关 `midi_transcribe`）。
3. **prompt 拼接 inpainting**：prompt（参考）与 target 沿时间轴在条件空间
   拼接,CFM 解码器在给定 prompt mel 的条件下生成 target 区段——**无说话人
   嵌入的音色迁移**。
4. 声码器出音频;SVC 输出按 target 长度修剪/补齐;post-process 仅
   tensor→numpy。

## 怎样验证功能、精度和性能

自动化测试仅覆盖离线 e2e,另有一个可复跑基准;本次调查未发现在线链路的
CI 覆盖——精度/性能结论需另行实测。

- e2e：`tests/e2e/offline_inference/test_soulxsinger.py`（快照双仓、建
  SVS/SVC view 目录、校验 phone_set.json;资产
  `tests/assets/soulxsinger/`）;示例
  `examples/offline_inference/text_to_speech/soulxsinger/end2end.py` 与
  `benchmark.py`（RTF+分段计时）;在线
  `examples/online_serving/text_to_speech/soulxsinger/`（未被 CI 覆盖）。
- 已知未决：`audio_sample_rate` ClassVar 与 checkpoint `config.yaml` 的
  优先级未追;在线服务链路无测试佐证。
