# providers/json_session.py — 只读 JSON 会话

<!-- verified-against: 2026-10-08 -->

`run_readonly_json` 为 Direct 评审、知识候选生成及 bot 分类复用 Codex/Cursor 会话。
调用方提供 cwd、完整 command、模型、schema、结果验证器及时间上限；返回 payload、
原正文、session_id、served_model、usage 和原始 stdout。`JSONSessionError`
表示启动、超时、退出或结果验证失败，不把失败当成通过审核。它保留
`failure_class`，并以 `timeout`、`returncode` 区分超时和进程退出；调用方可保留
自己的诊断与重试政策，不解析错误正文推断失败类型。

Codex 固定 `--ephemeral --ignore-user-config --strict-config --sandbox read-only`，
通过 schema 与 last-message 文件读取结果；`skip_git_repo_check` 是显式选项。
Cursor 固定 ask/trust profile；`output_format` 区分知识的 buffered JSON 与评审的
stream-json，buffered 模式禁止 wrap-up。调用方仍负责业务证据、知识适用版本和
最终发布政策；本模块不选择仓库或模型。

`readonly_environment` 保留模型认证配置，移除 GitHub、SSH agent、askpass 与
Git config 注入，禁用全局/系统 Git 配置及交互凭据。它与 Strict 订阅 CLI 的
`sanitized_env` 白名单用途不同，不能互相替代。

流式执行复用 `base.stream_cli`；stdout 活动重置 idle，absolute 截止时间独立。
Cursor wrap-up 仅在已有 session_id 时续接同会话，仍受原绝对截止时间限制。
格式或 schema 错误最多修复一次；有 session_id 时要求保持原结论仅修格式，
无 session_id 时按 `allow_sessionless_retry` 最多完整重试一次。修复有单独的短时限。
`max_repair_attempts` 只接受 0 或 1，默认 1；设为 0 时无效结果立即失败，
既不续接修复，也不完整重试。分类器使用 0，维持一次预算对应一次模型调用。
Codex 不静默换成 Cursor profile 或无 schema 调用。

每个实际进程调用（含续接、修复和重试）独立经过 `budgeting.call_budget`，
在发送前预留，保留已观察到的 usage；账本、额度、未知费用结算由显式绑定的
领域预算负责。该层不把缺失 usage 当成免费，也不替代领域恢复记录。

测试：`test_json_session.py`（离线假 CLI，权限、凭据隔离、buffered/stream、
超时、修复和重试）与 `test_provider_process.py`（共享进程生命周期）。
