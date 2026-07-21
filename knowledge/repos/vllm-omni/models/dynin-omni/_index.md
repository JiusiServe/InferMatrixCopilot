---
title: "Dynin-Omni（三 stage 全 LLM_GENERATION,远程代码为主）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/dynin_omni/, vllm_omni/deploy/dynin_omni.yaml, vllm_omni/config/pipeline_registry.py]
---

# Dynin-Omni

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 Dynin-Omni,代码/pipeline 标识 `dynin_omni`,无其他别名
  （checkpoint 组织为 snu-aidas,`snu-aidas/Dynin-Omni` 来自 examples
  README,YAML 不 pin）。AR registry:
  `DyninOmniForConditionalGeneration` →（`dynin_omni`, `dynin_omni`,同名类）;
  **无 diffusion registry 入口**。
- 入口路径：拓扑 `model_executor/models/dynin_omni/pipeline.py`（注册于
  `config/pipeline_registry.py`）;stage 分发壳 `dynin_omni.py`;三个 stage
  实现 `dynin_omni_token2{text,image,audio}.py` + 共享设施
  `dynin_omni_common.py`;桥
  `model_executor/stage_input_processors/dynin_omni.py`;deploy
  `vllm_omni/deploy/dynin_omni{,_ci,_multiconnector}.yaml`。
- pipeline key `dynin_omni`：三 stage 链 token2text → token2image →
  token2audio,**全部 LLM_GENERATION、全部 `engine_output_type="latent"`、
  全部 `final_output=True`**（各 stage 可按模态终止输出）。**唯一冻结拓扑,
  无 think/单 stage 变体**——变化只来自按请求任务路由与三份 deploy。
- 依赖共享模块：worker-connector 全载荷数据面
  （`OmniConnectorModelRunnerMixin`）、
  [Config 组件](../../components/config/architecture.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| detok_id 协议、远程代码机器、IPC 陷阱 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- 模型逻辑几乎全是 **checkpoint 内远程代码**（LLaDA 系 LM、采样函数、
  MAGVITv2 图像 VQ、EMOVA speech tokenizer、s2u vendor 树）——树内只是编排 +
  兼容 shim（pin 上 token2text 侧 4 个 transformers≥5 shim,token2audio 侧
  另有 tied-weights shim）;`trust_remote_code: true` 是承重配置。
- 三份 deploy：默认（单卡,显存 0.5/0.1/0.1——stage 0 持 LM,stage 1/2 只
  懒加载各自的 VQ/语音解码模型）;
  `dynin_omni_ci.yaml`（**显式 pin `pipeline: dynin_omni`,防 model_type
  自动探测失配**;L4 级显存）;`dynin_omni_multiconnector.yaml`
  （定义 Mooncake/Yuanrong/SHM 三种连接器,但 stage 间 output/input 链接
  显式指到 `mooncake_connector`——另两种只是备选定义;此文件
  `trust_remote_code: false` 与家族要求矛盾,pin 上无解释——评审改这份
  YAML 时先澄清）。

## 什么时候查这里

- 审查 dynin_omni 的 stage 交接、远程代码加载或 transformers 升级兼容;
  transformers 升级 PR 把本家族当高危回归点。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
