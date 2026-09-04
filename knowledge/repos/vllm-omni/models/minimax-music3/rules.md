---
title: "MiniMax Music3 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #6640", vllm_omni/model_executor/models/minimax_music3/acoustic.py, vllm_omni/model_executor/models/minimax_music3/weights.py, tests/model_executor/models/test_minimax_music3_repo_root.py]
confidence: high
---

# MiniMax Music3 规则

## MM3-1a — composite checkpoint 的直接组件必须与 AR snapshot 同 revision 且完整

- 触发：MiniMax-Music3 从 Hub/cache/root/`language_model/` 初始化 AR 或 acoustic stage、恢复 repo
  identity/revision，或加载 root checkpoint component。
- 强制：`language_model/` 由 vLLM stage loader 所有；`rvq_depth_decoder/`、
  `condition_encoder/`、`transformer/` 与 `vocoder/` 是从同一 composite repo root 直接 strict-load 的
  必需组件。root markers 只能用于发现 candidate，不能代替四组件 completeness；进入任一直接加载前，
  每个组件都必须有可加载的单文件 safetensors，或完整的 numeric `-N-of-M` shard run。若从 cached
  `language_model/` 进入，必须恢复 Hub repo identity 与 `snapshots/<sha>` revision，并将该 revision/
  `download_dir` 传给 cache repair，使直接组件与 AR snapshot 对齐。非标准 shard 名只有在
  `load_component_state` 本身可加载时才接受；component `state_dict` 保持 `strict=True`。
- 禁止：stage 0 只下载 language model/tokenizer 后就把 root components 当作 ready；以 marker、目录、
  index 或单个 numeric shard 证明完整；遗漏不在 marker set 中的 `condition_encoder`；从 cached
  subdir 回退到 `main`，或把 model-specific root recovery 误写成独立 tokenizer revision 传播。
- 验收：覆盖 Hub ID、repo root 与 cached `language_model/` 三种入口，cold/partial/complete offline cache、
  缺 `condition_encoder`、缺一个 numeric indexed shard、snapshot revision recovery、custom loadable
  shard naming 与 strict-load failure；真实 checkpoint/audio E2E、音质、吞吐和跨平台仍需独立证据。
  ^[PR #6640]
