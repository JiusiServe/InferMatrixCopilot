# 同步与校验

## 修改 Markdown 时必须同步什么

新增、移动、重命名、拆分或删除 Markdown 时，在同一修改中：

1. 更新当前目录 `_index.md`。
2. 创建或删除子目录时，更新上一层 `_index.md`。
3. 新增、删除或重命名 `general/` 一级主题时，同步 `general/_index.md` 和
   `knowledge/CLAUDE.md` 的知识地图（这棵树里已经没有 `README.md`）。
4. 修复所有相对链接和 anchor。
5. 移动错题时保持“编号”不变，只更新归属、路径和索引。
6. 删除被新页面替代的重复正文，不留兼容副本。
7. 确认本次改动没有带入机器信息、凭据、用户绝对路径或临时产物。
8. 改到 `repos/vllm-omni/` 时，再对照下面的[发版审计](#vllm-omni-页面还有一道发版审计)：
   owner 入口页、SHA pin 和 `sources:` 由机器审计对账，不在两个校验器的范围里。

## 运行检查

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

两个脚本都区分**错误**和**提醒**：只有错误让退出码非 0，提醒（接近拆分线、孤页、
超过 365 天未更新、`confidence: low`）需要人判断，不是必须清零的门。当前这棵树本身
就带着 2 条接近拆分线的提醒。

如果修改准备提交，还要查当前完整 diff 和未跟踪文件，不只看 `HEAD`。以真实 target base 为准，不硬编码 remote 或默认分支。

## 检查脚本负责什么

`tools/check_knowledge_tree.py` 负责容易明确判断的事：

- 正式知识目录有 `_index.md`；
- 当前有效页面在最近索引中恰好有一个真实 Markdown 链接；
- 子目录的 `_index.md` 在上一层索引中恰好有一个真实 Markdown 链接
  （`models/_index.md` 声明 `<!-- children: filesystem -->` 时豁免）；
- 相对链接指向存在的文件，且不是绝对路径；
- 文件和目录大小没超过 [拆分阈值](scaling.md)；
- 错题文件名、字段、状态、编号和索引完整；
- `components/`、`models/` 直属仓库，没有被工作主题或另一个 owner 包住；
- 源码 owner 下没有 `guides/` 中转层；
- 没有两个 owner 各存一份**逐字节相同**的整页正文（≥200 字符时比较）；
- `doc/knowledge/CONTRIBUTING.md` 仍在 100 个非空行 / 8 KiB 以内；
- `local/` 没有被 Git 跟踪；
- 正式页面没有真实 IPv4（`127.` 除外）、`C:\Users\…`、远端用户 home、私钥块，
  也没有 `StrictHostKeyChecking=no`、全局 `safe.directory *`、`--gpus all`、`pkill`、
  `rm -rf`、`find … -exec rm`。

`tools/check_wiki_lint.py` 额外负责：

- 沉淀层 frontmatter、类型和标签符合 `SCHEMA.md`（`repos/jianghan-roleplay-data-pipeline/`
  整棵子树豁免）；
- adapter `manifest.yaml` 的 `knowledge:` 只使用允许字段（`source`、`repo_subdir`、
  `briefing_docs`、`briefing_docs_extra`、`performance_briefing_docs`、
  `review_checklist`），briefing 和 checklist 不能指向 `incidents/history/results`
  原始证据层，`review_checklist` 指向的页面必须真实存在；
- 提醒级：没有任何入链的孤页、超过 365 天没更新的页面、`confidence: low` 或
  `contested` 的页面。

## vLLM-Omni 页面还有一道发版审计

`repos/vllm-omni/` 这一片除了两个校验器，还被 `tools/audit_vllm_omni_release.py`
按 `adapters/vllm_omni/release_baseline.yaml` 对账。它不是 lint：改错了本地两个脚本
照样 0 错误，失败发生在 CI 的 `vLLM-Omni release drift audit` 里。

- **owner 入口页（`owner_documents`）**：baseline 为每个上游结构 owner 声明一个知识
  入口，例如 `scheduler → knowledge/repos/vllm-omni/components/scheduler/rules.md`。
  重命名、移动或删除这些页面时必须在同一改动里同步 baseline。
- **SHA pin（`pin_documents`）**：8 个文件的正文里带 `main @ <短 SHA>` 或
  `v0.26.0rc1 @ <短 SHA>` 形式的标记，必须与 baseline 的 `audited_sha` 一致 ——
  `doc/architecture/KNOWLEDGE.md`、`models/catalog.md`，以及 configuration、diffusion、
  distributed、model-executor、scheduler、serving 六个 component 的 `_index.md`。
  人工不要手改这些 pin，它们随发版由 `imupdate` 更新。
- **`sources:` 溯源**：frontmatter 里以 `vllm_omni/`、`tests/`、`benchmarks/`、
  `docs/`、`.buildkite/` 开头的 `sources:` 条目会与上游文件列表对账；上游删除或重命名
  该路径后报 `stale_knowledge_source`（重命名时报告会给出新路径）。`incidents/`、
  `history/`、`results/`、`_archive` 不参与这项检查。

触发方式：每周一对 upstream `main` 跑 `report-only`；**任何**改到
`knowledge/repos/vllm-omni/**`、baseline、adapter manifest、`imupdate` skill 或审计脚本
的 PR，都会用 `previous_audited_sha → audited_sha` 跑 `enforce`。命令、模式和更新一个
release 的步骤见[发版漂移审计](../../contributing/release-maintenance.md)。

## 检查脚本不会替人决定什么

- 两篇文章是不是重复；
- 错题最终属于哪个 owner；
- 大文件应该按哪些主题拆；
- 仓库专属页是否复制了太多通用内容；
- 规则是否真的会改变下次行为。

工具不会生成目录、自动移动页面、静默决定 owner，或只因行数到线就机械切文件。

## 当前写入规则

- 新的跨仓库经验只写 `general/`。
- 新的仓库、代码模块和模型知识只写 `repos/`。
- 稳定教训先写最近 owner 的规则，复杂事故证据才可选写错题。
- 当前机器事实只写 ignored `local/`。
- 不建兼容副本或第二套写入路径；历史位置通过 Git history 查询。

## 完成标准

- 不熟悉框架的人只看根入口和 `_index.md` 就能找到需要的一篇规范。
- 日常落盘不再需要读整本贡献手册。
- `doc/knowledge/CONTRIBUTING.md` 不超过 100 个非空行或 8 KiB（校验器跨树检查这一条）。
- 工作主题和代码模块并列，不形成 `dev/frontend/backend` 这类套娃。
- 复盘已经更新最近 owner 的可执行规则，确实需要的错题只有一份正文。
- 超过阈值的文件和目录已按主题整理，或有明确的不拆原因和复核日期。
- 每个当前有效页面可从最近索引找到，所有链接有效。
- 第三方只需建目录、写 Markdown、更新上层索引并运行检查，不需要额外配置系统。
- `local/` 没有被 Git 跟踪，`knowledge/CLAUDE.md` 和 `doc/knowledge/CONTRIBUTING.md`
  仍然是短入口。
