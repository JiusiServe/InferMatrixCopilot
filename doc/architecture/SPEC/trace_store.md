# trace_store.py —— 规范

<!-- verified-against: 2026-10-02 -->

`LOC ~260 · trace/1：Copilot 与 RB 共用的模型调用/判定/结果记录 · refactor-status: stable`

## 职责
- `TraceStore(root)`：追加式 `records/<日期>.jsonl`（事实来源）+ 内容寻址 blob
  （`blobs/<aa>/<sha256>.gz`，gzip，读取时复核哈希）+ SQLite 索引 `index.db`
  （按 kind、run、仓库、变更集、PR、规则 ID、角色、模型、结果查询；`rebuild_index` 可从 JSONL 重建）。
- 记录（`schema: trace/1`）：`kind` ∈ `model_call`/`decision`/`outcome`/`replay`；`context`（run_id、
  playbook、step、repo、changeset_id、pr、rule_ids…）、`model`（role、provider、model、effort、served_model）、
  `usage`、`seconds`、`inputs`/`outputs`（只存 blob 引用，从不内联正文）、`result`、`error`、`env`
  （copilot 版本与 SHA）。`outcome` 是事后金标（merged、closed_unmerged、head_changed、rule_retired）。
- `trace_context(**fields)`：用 contextvars 绑定上下文，嵌套叠加，线程/协程安全。
- `begin_call(entry)`：在模型派发前保存输入 blob 及独立的
  `attempts/<UUID>/attempt.json`。`NativeCallArchive.event` 逐条脱敏、追加并 fsync
  `native-events.jsonl`，保留原生会话、输出、错误与调度等待事件。结束时绑定唯一的
  `model_call` 回执及输出、用量、耗时与状态；journal 不是另一笔调用，不能重复计费。
  中断未完成的 journal 保留输入和已收到的事件，未报告用量及费用保持未知。

## 不变量
- 写入前统一脱敏：已知令牌形态（GitHub、Anthropic、OpenAI、AWS、Slack、Bearer、私钥块）以及名字表明是
  密钥的环境变量的值（路径形式的值除外）。脱敏发生在哈希之前，blob 与 JSONL 中都不会出现密钥。
- 只依赖标准库；经 `sdk.v1` 导出（`TraceStore`、`TRACE_SCHEMA`、`trace_context`、`redact`）时不加载私有模块。

## 测试
`test_trace_store.py`（schema 与去重 blob、索引与重建、脱敏、网关记录成功与失败调用、回放、导出的判定/结果
关联与校准集泄漏过滤、SDK 导出、知识服务的 decision/outcome 记录、派发前输入留档、原生事件及中断保留）。
