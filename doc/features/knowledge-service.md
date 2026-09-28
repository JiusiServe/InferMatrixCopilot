# 知识服务 —— Copilot 全权负责知识库

> **一览**
> | | |
> |---|---|
> | **状态** | 🚧 分阶段落地。已合并：Direct 路由多仓库化与按请求知识视图（#203）、Knowledge Ops API 2.0 与 L1（#204）、generated-baseline 发版审计（#205）、服务核心（#206）；本 PR 加入 intake、质量门与校准；本页随后续 PR 更新 |
> | **做什么** | 知识的创建、维护、退役、删除与发版巡检全部在 Copilot；每次变更经质量门，通过即经合并队列自动合并；ReviewBot 只读消费 |
> | **怎么开关** | 每个仓库在 `adapters/<repo>/manifest.yaml` 的 `knowledge_lifecycle`（人工审阅的高风险段）中设置 `enabled` 与 `mode: shadow\|auto_merge` |
> | **设计** | 经 GPT-6 sol 评审批准的设计文档（知识库管理重构设计，多仓库，v7） |
> | **硬边界** | bot 主机不持有任何 GitHub 写凭据；所有 GitHub 写动作由 GPU 盒上的发布器以 owner 账号执行，且只执行服务签名、未过期、代际有效的 outbox 项；私有上游仓库只能 shadow，不产生任何公开产物 |

## 组成

| 部分 | 位置 | 职责 |
|---|---|---|
| 仓库配置与注册表 | `kb_service/config.py` | 解析每个 adapter 的 `knowledge_lifecycle`；`general/` 由服务配置 |
| 账本 | `kb_service/ledger.py` | 单个 SQLite（`$KB_STATE_DIR/kb.db`），所有表按 `repo` 分区；单实例租约；代际号 |
| 签名 | `knowledge_service/signing.py` | Ed25519 信封，按用途（判定、outbox、控制记录、暂停清单、回执）隔离签名 |
| outbox | `kb_service/outbox.py` | 服务写签名项、控制记录与暂停清单；发布器执行前用 `check_item` 复核 |
| CLI | `infermatrix-copilot kb …` | `keygen`、`status`、`pause`、`resume`、`control` |

## 代际与暂停

任何暂停、熔断、回滚或切回 `shadow` 都会使该仓库（或全局 `*`）代际 +1，并立即重签
控制记录与暂停清单。发布器只执行代际与当前一致、未过期（`enqueue`/`post_verdict`
30 分钟，其余 24 小时）且控制记录签发不超过 10 分钟的项；`pause` 与 `close` 总是可执行。
只有 `auto_merge` 仓库会产生非停止类写动作：`shadow` 只记录“将要做什么”，不开 PR、
不发评论；模式变化本身也会使代际 +1。
暂停清单发布在服务的公开 HTTP 端点，kb-gate 在合并队列中读取它，过期或不可达即失败。

## 运维

```bash
infermatrix-copilot kb keygen --out /etc/infermatrix-kb/service.pem   # 公钥提交到 .github/kb-gate.pub
export KB_SIGNING_KEY=/etc/infermatrix-kb/service.pem KB_STATE_DIR=/var/lib/infermatrix-kb
infermatrix-copilot kb status
infermatrix-copilot kb pause --repo vllm-omni --reason "rollback drill"
infermatrix-copilot kb resume --repo vllm-omni
```

依赖：`pip install "infermatrix-copilot[kb]"`（cryptography）。

## Intake 与质量门

```bash
infermatrix-copilot kb run --playbook kb-intake --repo vllm-omni   # 一次 intake（shadow 下只记录）
infermatrix-copilot kb calibrate --repo vllm-omni                  # 评审模型校准；不达标不得切 auto_merge
```

模型：`KB_GENERATOR`（默认 `claude-code:claude-opus-5-5`）、`KB_JUDGE`（默认
`codex:gpt-6-sol:medium`）。每次模型调用写入 `$KB_STATE_DIR/traces/model_calls.jsonl`。

