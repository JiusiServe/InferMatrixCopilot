---
title: "Aura-Omni 规则"
created: 2026-09-23
updated: 2026-09-23
type: rule
tags: [vllm-omni, models, model-executor, serving]
sources:
  [
    "PR #7633",
    vllm_omni/model_executor/models/aura_omni/duplex/plugin.py,
    vllm_omni/model_executor/models/aura_omni/duplex/history.py,
    vllm_omni/model_executor/models/aura_omni/duplex/capabilities.py,
    vllm_omni/model_executor/models/aura_omni/pipeline.py,
    vllm_omni/model_executor/stage_input_processors/aura_omni.py,
    vllm_omni/engine/duplex/session/runner.py,
    vllm_omni/config/environment_variable_inventory.py,
    vllm_omni/deploy/aura_omni.yaml,
    docs/user_guide/examples/online_serving/aura_omni.md,
    tests/engine/duplex/test_session_runner.py,
    tests/model_executor/stage_input_processors/test_aura_omni.py,
    tests/model_executor/models/aura_omni/test_aura_omni_duplex_history.py,
    tests/config/test_environment_variables.py,
  ]
confidence: high
---

# Aura-Omni 规则

只有 `AURA-<数字字母>` 是可审计规则 ID。共享 duplex serving 生命周期见
[Serving session lifecycle](../../components/serving/rules-session-lifecycle.md)；
Talker/Code2Wav 共享行为见 [Qwen3-TTS](../qwen3-tts/rules.md)。

## Direct 代码快速入口

| PR / 审查信号 | 规则组 | 第一批源码 |
|---|---|---|
| `aura_omni` pipeline、四段 stage、deploy pin | AURA-1a | `config/pipeline_registry.py`；`model_executor/models/aura_omni/pipeline.py`；`deploy/aura_omni.yaml` |
| duplex `/v1/realtime?duplex=1`、`AuraDuplexPlugin` | AURA-1b / 1c / 1d / 1e | `models/aura_omni/duplex/plugin.py` → `engine/duplex/session/runner.py` |
| `<\|silent\|>` stop id、v1 vs v2 checkpoint | AURA-1f | `duplex/plugin.py::AURA_SILENT_TOKEN_ID`；streaming Omni 侧 silent env |
| OmniInteract / Stage1 TTFT·TPOT 报表 | AURA-1c / 1g | `runner._stash_stage_metrics`；`test_projected_stage1_metrics_reach_the_spoken_audio_event` |
| barge-in、draining Stage2/3、cancel fence | AURA-1d | `runner` barge-in / `older_abort_ids`；`capabilities` / concurrent turn |
| `VLLM_AURA_SENTENCE_TTS*` | AURA-1h | `environment_variable_inventory.py`；`stage_input_processors/aura_omni.py` |

## AURA-1a — 四段组合管线不得把 AURA 当成单 stage 模型

- 触发：注册、部署或审查 `aura_omni` / AURA 语音助手入口。
- 强制：正式拓扑是 Stage0 Qwen3-ASR → Stage1 AURA（Thinker）→ Stage2 Qwen3-TTS
  Talker → Stage3 `Qwen3TTSCode2Wav`。家族自有桥是 `asr2aura` / `aura2tts`
  （`stage_input_processors/aura_omni.py`）；Stage2→3 复用 qwen3_tts 的
  `talker2code2wav_*`。Realtime full-duplex 入口是 `/v1/realtime?duplex=1`，由
  `AuraDuplexPlugin` 承接，不是把 AURA 伪装成单模型 chat completion。
- 禁止：按单 stage LLM 改 sampling / history；或把 MiniCPM native duplex adapter
  合同直接套到 AURA。
- 验收：deploy / registry 仍展开四段；duplex smoke 走 realtime path；qwen3_tts
  Talker/Code2Wav 回归仍影响本家族尾段。^[PR #7633]

## AURA-1b — Stage1 中间投影不得消费 TTS 路径

- 触发：修改 `AuraDuplexPlugin.project_intermediate_output`、`decide_output`、或
  duplex runner 对 projected stage 输出的消费/截断。
- 强制：AURA 对 **Stage1** 返回 `project_intermediate_output=True`，把 Thinker
  文本投影到 WS，但 **不消费、不截短** 后续 Talker/Code2Wav。Silent 决策走
  `decide_output`（含 stop id / `<|silent|>` 文本），listening 不得误开 spoken
  audio turn。
- 禁止：为了「省一次投影」把 Stage1 当 pass-through 吃掉；或因投影而 `consume`
  掉本应进入 Stage2 的 token。
- 验收：有文本 delta 的 spoken turn 仍产生 Stage2/3 音频；silent turn 不产生
  错误 TTS。^[PR #7633]

## AURA-1c — 投影的 Stage1 仍必须 stash engine stage metrics

- 触发：修改 `engine/duplex/session/runner.py` 的 `on_stage_output` /
  `_stash_stage_metrics`，或任何把 Stage1 TTFT/TPOT 挂到 spoken 事件的报表路径。
- 强制：当 `project and not consume`（AURA Stage1）时，runner 仍须
  `_stash_stage_metrics`。否则 OmniInteract / duplex 报表会丢 Stage1
  `vllm_ttft_ms` / `vllm_tpot_ms`，只剩 client 侧假 TTFT。
- 禁止：只在纯 pass-through（`not project`）分支 stash；或把 Stage0 ASR 指标
  标成 Stage1 Thinker。
- 验收：`test_projected_stage1_metrics_reach_the_spoken_audio_event`；spoken
  事件带 Stage1 engine metrics，且数值量级是 Thinker request 时钟而非
  Stage0。^[PR #7633]

## AURA-1d — barge-in 必须清理 cancel fence，并仍 abort 旧 draining TTS

- 触发：修改 duplex barge-in、`cancel_fence`、`abort_ids`、或 AURA concurrent
  turn（Stage1 结束后不立刻 abort 旧 Stage2/3）的资源释放。
- 强制：barge-in 对 **当前 cancel fence** 必须走完整 cleanup（含
  `abort=True` 弹出 orchestrator `request_states`），不能只 abort 不 cleanup。
  Concurrent / draining 旧 Stage2/3 的 request id 仍须 abort；对资源释放使用
  **旧 fence 的** `older_abort_ids`（不在本次 `cancelled_ids` 内的 abort 集合），
  避免把新 turn 刚绑定的 id 一并 `release_resources`。
- 禁止：为修 leak 而 `release_resources_for_request_ids(全部 abort_ids)`；或
  去掉对 draining 旧请求的 abort（会复活「取消后旧 TTS 仍占用座位」）。
- 验收：stale-epoch drop 与 forwarded stage barge-in 测试；有 draining TTS 时
  barge-in 后旧请求离开 `request_states`，新 turn 不被误 release。^[PR #7633]

## AURA-1e — SessionHistory 裁剪默认对齐 Native，旋钮不得另发明一套

- 触发：修改 `aura_omni/duplex/history.py`、`commit_model_context`、vision-follow
  / OmniInteract proactive（无声 + frames）入史，或暴露 history 长度旋钮。
- 强制（不可改硬核）：两帧视觉合成一轮 video、单一 `<|video_pad|>`；**空 user
  transcript + assistant `<|silent|>`** 成对丢弃。Silent vision-follow（空
  transcript **但有 clip** + silent）**会入** history 并占 video 名额；无 clip、
  无 user 字、又 silent 的整轮不入。
- 强制（长度政策）：裁剪 **默认** 对齐 Native Gateway
  （`MAX_VIDEO_ROUNDS` / `NUM_VIDEO_ROUNDS_TO_REMOVE` / `MAX_ROUNDS_CONVERSATIONS`，
  Native 默认 45 / 30 / 999）。数字是 default，不是唯一合法值。Native 用同名
  env 可调；Omni 当前把 default 写成 `SessionHistory` 常量／字段，**尚未**接线。
  日后 AURA 补旋钮时必须 **镜像同名语义**（超过 `MAX_VIDEO_ROUNDS` 再剥最旧
  `NUM_VIDEO_ROUNDS_TO_REMOVE` 条 video payload，文字留下），禁止另起一套阈值名
  或「一次清光」语义。
- 禁止：把每帧当独立 history 轮；把 45/30 写成不可配置合同；或把「连续 VF
  silent」默认诊断成 abort/座位回归（先查 Stage1 决策偏压与入史名额）。
- 验收：`test_aura_omni_duplex_history` 覆盖入史／silent pair／默认裁剪；若接线
  env／config，断言默认仍等于 Native、改旋钮后阈值随之变。^[PR #7633]

## AURA-1f — `<|silent|>` stop id 必须与 checkpoint 家族一致

- 触发：配置 AURA stop / silent token、迁移 AURA v1↔v2 checkpoint、或复用
  duplex plugin 常量到另一套权重。
- 强制：合并后的 duplex plugin 常量是 **v1** `AURA_SILENT_TOKEN_ID = 151669`
  （与 `151645` 等 companion stop 一起配置时不得混用 v2 id）。**AURA_v2**
  streaming Omni 路径使用另一套 id（公开约定：`248070` / `248046` 等），必须
  跟 checkpoint / tokenizer 对齐，不能把 v1 duplex 常量抄到 v2 serve。
- 禁止：silent id 配错导致 silent 无法 stop、pad 到 `max_tokens`（表现为每轮
  异常长的「假思考」）。
- 验收：对应权重下 silent turn 在 stop id 处结束；错配回归会拉长到 max_tokens。^[PR #7633]

## AURA-1g — OmniInteract（及同类）streaming 精度 / latency 报表必须以完整 0001 session 暖机

- 触发：跑 AURA duplex / Omni streaming 的 OmniInteract（或同构 annotation-inject）
  精度、spoken ASR 对照、Stage1 TTFT/TPOT 中位数。
- 强制：在**同一 server 进程、同一 attention backend**上，量测片之前先跑完视频
  **`0001` 的完整 streaming session** 做 warmup；片单可含 `0001,...`，但报表 /
  GT / median **必须排除 `0001`**。
- 禁止：只用 HTTP `--num-warmups` 空转代替真实 `0001` session；或把 `0001`
  计入与 Native 对齐的 spoken QA / ASR 统计（cold-start silent 长锁会造成假阴，
  例如首条量测片丢 annotation wav）。
- 验收：暖机后首条量测片的首 silent 量级回到短延迟；排除 `0001` 后 spoken 计数
  与 Native 对照不再系统性少一轮。^[PR #7633]

## AURA-1h — 新增 `VLLM_AURA_*` 模型内化 env 必须进入 inventory 与 snapshot 计数

- 触发：引入或重命名 AURA 专用环境变量（例如 `VLLM_AURA_SENTENCE_TTS`、
  `VLLM_AURA_SENTENCE_TTS_MIN_CHARS`）。
- 强制：变量加入 `environment_variable_inventory` 的模型内化集合，并同步
  `tests/config/test_environment_variables.py` 的分类计数；sentence TTS 经
  plugin / `aura2tts` 路径喂 Talker，不得假设「只有 SHM Stage1→2」才会触发。
- 禁止：只在代码读取 env、不登记 inventory（CI 会报未分类变量）。
- 验收：inventory 测试与 env 快照计数绿；开关 sentence TTS 时 Stage2 仍收到句级
  条件。^[PR #7633]
