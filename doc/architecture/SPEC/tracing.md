# tracing.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~652 · 可移植的 span 树记录器 · refactor-status: oversized`

## 职责
把一次 run 记录成一棵计时 span 树，**零外部依赖**。

## 功能
OpenTelemetry **形状**的 span（`trace_id`、`span_id`、`parent`、`start`、`end`、
`attributes`）追加进一个 JSONL 文件，**一行一个 span，在 span 关闭时写出**。

## 公开契约
`span(...)`（上下文管理器）、模块级 tracer 访问器，以及那套 JSONL 记录形状。

## 不变量（**E1**、**E3**）
- **在 span 关闭时写、仅追加。** 被杀掉的 run 会保留**每一个已完成**的 span ——
  这正是它不是"内存里建树、退出时冲刷"的原因。
- **同步与 asyncio 双安全。** `span()` 是可以裹在 `await` 外面用的普通上下文管理器；
  父子嵌套经 `contextvars` 承载并**按 task 复制**，因此**并行的 agent 会得到各自独立
  且正确的树**，而不是交错成一棵。
- **零外部依赖** —— **刻意不用** OTel SDK。形状是兼容的，依赖不引入。
- `create()` 被裹在 `span("llm")` 里，用于记录 TTFT、token 和并发。
- 与 `run_trace.py` 不同：这里是**计时**，那里是**事实**。两者默认都不进 prompt。

## 边界 —— 不属于这里
不记录事实（`run_trace.py`）；不计算指标（`metrics.py`）；不含导出协议。

## 依赖（允许）
仅 stdlib（`contextvars`、`json`、`time`、`threading`）。

## 测试
`test_tracing.py`、`test_trace_pack.py`。

## 重构备注
约 652 行，是最大的叶子模块。如果继续增长，span 模型、JSONL 写入器、进程级 tracer
管道是三个可分离的关注点。
