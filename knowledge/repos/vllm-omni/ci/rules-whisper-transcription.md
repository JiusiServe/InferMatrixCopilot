---
title: "vLLM-Omni Whisper 转写 CI 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, ci]
sources: ["PR #5675", .buildkite/cuda/test-merge.yml, .buildkite/cuda/test-ready.yml, tests/helpers/media.py, tests/helpers/tests/test_media.py]
confidence: high
---

# Whisper 转写 CI 规则

这是 [CI 入口](_index.md) 下的专项规则；Qwen3-TTS ready/merge 的其余收集边界见
[TTS CI 规则](rules-tts.md)。

## OMNI-CI-3e — Whisper 转写设备选择必须以容量首个命中和对应 lane 路由共同约束

- 触发：修改 `tests/helpers/media.py` 的 Whisper 转写设备选择、显存门槛或 CPU fallback，或修改其
  CUDA ready/merge `source_file_dependencies`。
- 必须：从最高可见设备索引向下探测，并在第一个可用显存不少于 16 GiB 的设备立即停止、设为
  Whisper 设备；无设备满足时回退 CPU。保留该门槛保护单卡 server-plus-Whisper OOM 的说明；单元测试
  必须覆盖等于门槛、低 1 byte、最高索引优先、遇到不足设备后的继续探测、全不足回退，以及 probe
  顺序/early break。凡调用该 helper 的 CUDA TTS lane，ready/merge 的 source dependency 都必须显式
  包含 `tests/helpers/media.py`。
- 禁止：恢复无条件的 `n > 1` 选择；为寻找 most-free 设备扫描全部卡；把 16 GiB 当作已预留显存；或
  让 helper-only diff 绕过其调用的 CUDA TTS gate。
- 验收：`tests/helpers/tests/test_media.py::test_select_whisper_device_by_available_memory` 覆盖上述边界和
  probe order；`.buildkite/cuda/test-ready.yml` 的 Qwen3-TTS CustomVoice、以及
  `.buildkite/cuda/test-merge.yml` 的 Qwen3-TTS CustomVoice 与 Base，均将
  `tests/helpers/media.py` 列为 source dependency。与 TTS ready/merge oracle 的其余收集边界同时遵守
  [OMNI-CI-1d](rules-tts.md#omni-ci-1d-qwen3-tts-base-的-dummy-ready-oracle-与-real-weight-merge-coverage-必须分离)。^[PR #5675]
