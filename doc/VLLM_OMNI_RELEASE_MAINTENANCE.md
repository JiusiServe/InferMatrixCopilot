# vLLM-Omni 发版漂移审计

InferMatrixCopilot 的模型清单、代码 owner 路由和源码引用会随着
vLLM-Omni 发版而过期。这个审计只读取两个 Git 提交和本仓库声明，不会 checkout
目标版本，也不会自动修改知识规则。

## 用户入口

安装 InferMatrixCopilot 后，在 Codex、Claude Code 或 Cursor 中运行：

```text
/imupdate D:\path\to\vllm-omni
```

Skill 自动用 baseline 中的 `audited_sha` 作为旧版本、目标仓库当前 `HEAD`
作为新版本，先做只读审计，再由 Agent 更新有证据支持的结构事实并完成强制校验。
可选的第二个参数可以指定目标 tag 或 SHA。

## 底层命令

先在 vLLM-Omni checkout 中 fetch 需要比较的 tag 或 SHA，然后运行：

```powershell
python tools/audit_vllm_omni_release.py `
  --from 5d44868e `
  --to v0.26.0rc1 `
  --repo D:\path\to\vllm-omni `
  --json-output $env:TEMP\vllm-omni-release-audit.json
```

审计覆盖：

- AR、Diffusion 和 pipeline registry；
- deploy YAML；
- 新增、修改、删除和重命名路径；
- changed path 到 Direct 知识 owner 的机器路由；
- adapter runtime module 未覆盖的 changed path；
- active knowledge 中受删除或重命名影响的 `sources:`；
- component、model catalog 与 canonical baseline 的 source pin。

同样的提交和 baseline 会产生等价 JSON；报告不包含时间戳和本机 checkout 路径。
默认 `--mode enforce`：存在未解释漂移时退出 1，输入或 Git 失败时退出 2。
`--mode report-only` 仍报告 `DRIFT`，但退出 0，供定时巡检使用。

底层实现不 checkout 版本：它用 `git rev-parse` 固定两个提交，用
`git diff --name-status -M` 找新增、修改、删除和重命名，再用
`git show <sha>:<path>` 直接读取 Git 对象。Python AST 负责提取模型和
pipeline registry，deploy YAML 直接按提交列举；结果做排序和哈希后与 baseline、
owner 路由、manifest、知识 `sources:` 和 pin 对账，最后输出稳定 JSON。
这个命令只报告证据，不编辑任何文件。

## 更新一个 release

1. 用当前 `release_baseline.yaml` 的 audited SHA 作为 `--from`，新 tag 作为
   `--to`，先跑 `report-only`。
2. 人工确认 registry、deploy、路径 owner 和知识来源变化。
3. 把旧的 `audited_sha` 移到 `previous_audited_sha`，再只更新报告证明已经漂移的
   baseline、catalog、source map 或 manifest；不要自动生成语义规则。
4. 用同一组 `--from/--to` 跑 `enforce`，再运行知识 validator 和相关 pytest。
5. JSON 是临时证据，不提交到 `knowledge/`；完成后删除。

## PR 学习与 release 审计是两件事

合并 PR 的复盘只提炼可复用、可执行的 owner 规则，且必须等最终修复、review thread
和 CI 结果稳定后再做。Release 审计只对账结构事实，不把 PR 内容、事故过程或审计报告
写进知识树，也不因为上游发版自动升级 InferMatrixCopilot 版本或依赖。

CI 每周对 upstream `main` 运行 `report-only`。修改 baseline 的 PR 会自动用
`previous_audited_sha → audited_sha` 运行 `enforce`；Actions 手动运行可用
`report-only` 检查任意区间，`enforce` 只接受当前 baseline 声明的升级区间。
