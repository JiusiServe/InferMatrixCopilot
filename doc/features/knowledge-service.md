# 知识服务 —— Copilot 全权负责知识库

> **一览**
> | | |
> |---|---|
> | **状态** | 🚧 分阶段落地。已合并：Direct 路由多仓库化与按请求知识视图（#203）、Knowledge Ops API 2.0 与 L1（#204）、generated-baseline 发版审计（#205）、服务核心（#206）、intake 与质量门（#207）；本 PR 加入合并流程、快照激活、发版巡检与调度器；本页随后续 PR 更新 |
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

## 调度、合并、激活与巡检

```bash
infermatrix-copilot kb serve                 # 常驻调度器（systemd），持有单写入租约
infermatrix-copilot kb activate              # 立即激活知识仓库 main 的快照
infermatrix-copilot kb rollback --to <sha>   # 回指到较早的快照（下一请求生效）
```

合并流程：`open_pr` 回执 → 为该 PR 的精确 head 签发判定并发布评论 → PR 阶段 `kb-gate`
通过后入合并队列（每仓库至多 1 个）→ 合并后激活新快照。发版巡检在上游新 release 后运行
T1/T2/T3 与 purge，每个规则页一个变更集，全部经过质量门。

评审服务读取知识：将 `KNOWLEDGE_ROOT` 指向 `$KB_STATE_DIR/active`。


## 仓库端门禁 `kb-gate`

必需检查 `kb-gate`（`.github/workflows/kb-gate.yml`）只从受 CODEOWNERS 保护的验证包
`.github/kb-gate/` 运行，从不导入 `src/`、`tools/`、`knowledge/tools/`。

- **PR 预检**：`pull_request_target`、带判定标记的评论或手动触发；在当前 `main` 上验证后，
  把 `kb-gate` 状态发布到 PR head。只决定能否入队。
- **merge group**：名为 `kb-gate` 的作业逐段验证将要落地的提交；失败则 PR 被移出队列。
- 未触碰 `knowledge/` 的 PR 总是通过；知识 PR 需要有效签名判定、清单一致、L1 通过、
  暂停清单新鲜且未命中（见 SPEC `knowledge_service.md` 的 kb-gate 验证器一节）。

修改验证逻辑后重新生成验证包（属于 `.github/**` 改动，需要知识维护者审批）：

```bash
python tools/build_kb_gate_bundle.py          # 重新生成
python tools/build_kb_gate_bundle.py --check  # CI 提醒（非阻塞）
python tools/build_kb_gate_bundle.py --lock   # 从 PyPI 重新按哈希固定依赖
```

暂停清单端点（bot 主机）：

```bash
infermatrix-copilot kb holds-server --port 8765   # 只提供 GET /holds.json，默认绑定 127.0.0.1
# 反向代理加 TLS，例如 Caddy：  handle /kb/holds.json { rewrite * /holds.json; reverse_proxy 127.0.0.1:8765 }
```

切换前的负责人步骤：提交 `.github/kb-gate.pub`（`kb keygen` 的公钥）；在
`.github/kb-gate/config.json` 填入暂停清单的公开 HTTPS 地址（`$KB_STATE_DIR/public/holds.json`）；
在 `.github/CODEOWNERS` 中再加入至少一名知识维护者；仓库 admin 开启合并队列（merge commit）
与 ruleset（必需检查 `kb-gate` 限定 GitHub Actions 来源、Code Owner 审阅、新推送需重新批准）。
在此之前，所有触碰 `knowledge/` 的 PR 都会被 `kb-gate` 拒绝（失败即关闭），代码 PR 不受影响。

## 发布器（GPU 盒）

发布器以仓库负责人现有的 `gh` 登录执行服务签名的 outbox 项，写回签名回执。凭据不离开 GPU 盒。

```bash
infermatrix-copilot kb keygen --out ~/.infermatrix-copilot/kb-publisher.pem   # 发布器密钥；公钥给服务的 KB_PUBLISHER_PUBKEY
export KB_SERVICE_PUBKEY=/path/to/service.pub          # 服务公钥（kb keygen 输出的一行）
export KB_PUBLISHER_KEY=~/.infermatrix-copilot/kb-publisher.pem
export KB_PUBLISHER_GIT_AUTHOR='Name <email>'         # 知识 PR 提交的作者
export KB_PUBLISHER_STATE=/data/<owner>/kb-publisher  # 必须在负责人目录下（gh 包装器按目录选择登录）
infermatrix-copilot kb publish --remote bot-host:/path/to/kb-state --once   # 只记录（dry-run）
ALLOW_POST=1 ALLOW_PUSH=1 infermatrix-copilot kb publish --remote bot-host:/path/to/kb-state   # 常驻
```

每轮还会拉取 bot 主机上每周生成的留痕归档（`$KB_STATE_DIR/archive/`），哈希校验通过后保存到
`$KB_PUBLISHER_STATE/archive/`，作为离机副本。

没有 `ALLOW_POST=1` 时只把将要执行的动作写入 `$KB_PUBLISHER_STATE/traces/publisher.jsonl`；推送分支还需要
`ALLOW_PUSH=1`。控制记录超过 10 分钟未更新（服务可能宕机）时整轮不执行任何动作。

## 留痕、回放与数据集（trace/1）

知识服务的每次模型调用（含失败）、每个质量门判定与每个事后结果都写入 `$KB_STATE_DIR/traces/`
（JSONL + 内容寻址 blob + SQLite 索引，写入前脱敏）。RB 通过 `sdk.v1.TraceStore` 使用同一 schema。

```bash
infermatrix-copilot kb traces --changeset <id>                      # 查询记录
infermatrix-copilot kb replay --record <id> --model codex:gpt-6-mini:low   # 用便宜模型重放一次调用
infermatrix-copilot kb export --out judge.jsonl                     # 导出数据集（自动剔除校准集相关调用）
```
