# config.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~418 · 配置 · refactor-status: oversized`

## 职责
从 env / `.env` 加载的 `Settings`（pydantic-settings），以及把本次 run 的档位与后端
选择变成具体目标的那些推导 helper。

## 功能
为 LLM 端点与逐档模型、仓库、引擎预算、推送安全、PR debug、外部 rebase、agent 运行时、
ensemble、MoA、评审深度与按 pass 路由、Strict 后端选择、profile、patch 触发器、
metrics 与升级，提供带类型字段和安全默认值。

## 公开契约
带全部可调项的 `Settings`；`reviewer` / `intent`（回退到 `agent_model`）；
`repo_path(name)`；`model_for(mode)`；`tier_target(role)` → `ResolvedTarget`；
以及 `strict_backend` 校验器。

## 不变量（**A5**、**C2**、**B1**）
- 密钥只经 env / `.env`（被 git 忽略，**绝不提交**）。
- 仓库专属默认值（`default_repo`、`rebase_agent_root`、`high_risk_modules`、
  `cost_ref_*`）**只是兜底**；adapter/profile 会覆盖它们。它们是这里**唯一被允许**的
  仓库字面量，泄漏上限为 3，并由 `test_v2_p0.py::test_repo_neutral_core` 钉住。
- **`STRICT_BACKEND` 在前面就被校验**，失败时列出合法集合。未知后端**绝不能**到达
  `providers.resolve_provider` —— 两层，因为 `.env` 里的一个拼写错误不该启动一次注定
  失败的 run。
- **`tier_target` 对 harness provider 返回空 key。** harness 的认证住在厂商 CLI 自己的
  状态里，本代码库从不接触。**唯一例外是 `deepseek`**：它是 API-keyed 的，凭据在它自己的
  transport 内部解析 —— 见 `providers/deepseek.md`。
- **fail-closed 的 served-model 守卫**：实际服务的模型与请求不符是**错误**，
  而不是静默替换。
- **推理模型需要 token 留白。** 灰区评审 planner 曾在两个战役里对每一个灰区条目静默
  失败，因为思考在任何 JSON 出现之前就吃完了 400-token 上限 —— 对推理模型调用的上限
  是**正确性设置，不是成本旋钮**。

## 边界 —— 不属于这里
除推导 helper 外无逻辑；除加载 env 外无 I/O；不含 provider transport（`providers/`）；
不调模型。

## 依赖（允许）
仅 `pydantic-settings`。

## 扩展点
新可调项 → 一个带安全默认值的类型字段，并用一行注释写明含义与单位。
新后端 → 注册表条目 + 本文件的校验器集合，**绝不是这里的一条新分支**。

## 测试
`test_llm_providers.py`、`test_tier_split.py`、`test_providers.py`；
全套测试间接覆盖（fixture 会构造 `Settings(_env_file=None, ...)`）。

## 重构备注
在 v3 后端工作中从约 116 行长到约 418 行，现在**确实偏大**，但仍是单一关注点。
如果再增长，请分组成嵌套 settings 模型（`LLMSettings` / `PushSettings` /
`ReviewSettings` / `BackendSettings`），**而不是拆文件** —— 调用点依赖"一个 `Settings`
对象到达每个 `StepContext`"。
