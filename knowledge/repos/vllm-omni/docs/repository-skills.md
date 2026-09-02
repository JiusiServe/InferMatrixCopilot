---
title: "Repository skill contributor rules"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, docs]
sources: ["PR #6029", "PR #6046", .claude/skills/readme.md, .claude/skills/add-diffusion-model/SKILL.md, .claude/skills/add-tts-model/SKILL.md, .claude/skills/diffusion-perf-opt/SKILL.md, .claude/skills/precheck-pr/SKILL.md, .claude/skills/precheck-pr/references/checklists.md, .claude/skills/precheck-pr/references/examples-policy.md, .claude/skills/quantization/SKILL.md, .claude/skills/review-pr/SKILL.md, .claude/skills/vllm-omni-npu-upgrade/SKILL.md, .claude/skills/vllm-omni-test/SKILL.md, docs/contributing/README.md]
confidence: high
---

# Repository skill contributor rules

只有 `DOCSKILL-数字字母` 是可审计规则 ID。这里拥有 contributor-facing catalog、组合流程和
信任边界；具体 review 行为仍由 [review owner](../review/_index.md) 管理，各 domain 的源码合同
仍回对应 model/component owner。

## DOCSKILL-1a — catalog 必须从目标 revision 的真实 skill 目录生成

- 触发：增删/重命名 `.claude/skills/*`、修改 frontmatter `name`，或更新 contributor task-to-skill
  table 与 `.claude/skills/readme.md`。
- 强制：以目标 revision 的目录与每份 `SKILL.md` frontmatter 为准，分别校验链接路径和 invocation
  name。`main @ a15b5b4b` 恰有 8 个目录且都有 `SKILL.md`：`add-diffusion-model`、
  `add-tts-model`、`diffusion-perf-opt`、`precheck-pr`、`quantization`、`review-pr`、
  `vllm-omni-npu-upgrade`、`vllm-omni-test`。NPU 的目录/链接名是
  `vllm-omni-npu-upgrade`，frontmatter 与展示的调用名是
  `vllm-omni-npu-model-runner-upgrade`，两者不能互换。旧 catalog 的 `add-omni-model` 与
  `generate-release-note` 没有目标目录，不能继续列为可用 skill。
- 禁止：只检查显示名称而不解析链接；从文档名称推断存在安装包、hook、agent registry 或 runtime
  registration。contributor guide 的 GitHub 链接指向可变 `main`；发布审计必须读取 pinned target
  SHA，不能把未来 `main` 内容倒灌到当前合同。
- 验收：对 catalog/task table 的每行做 link-exists + frontmatter-name 对照，并反向检查所有顶层
  skill 目录都被登记。目标提交只改两份 Markdown，没有修改 skill body、reference、script、test
  或 agent runtime；报告的 strict MkDocs/pre-commit 证明文档可构建，不证明 automatic discovery、
  invocation 或行为正确，且没有 catalog link/frontmatter 的自动回归。

## DOCSKILL-1b — skill 是可审查指令，不是授权、执行证明或安全边界

- 触发：贡献者要求 coding agent 使用 repository skill，组合 domain/test/precheck workflow，或引用
  skill 输出作为合并证据。
- 强制：issue、accepted RFC 或明确 maintainer decision 定义任务权限与预期行为；先选最窄 domain
  skill，生产行为或 tests/CI 改动再加 `vllm-omni-test`，提交前用 `precheck-pr`。要求 agent 给出
  精确可运行命令、结果和所有因硬件、权重、credential、dependency 缺失而未运行的检查；人工再
  检查 diff scope、无关改动、测试、文档以及性能/精度证据。maintainer review 仍不可省略。
- 信任边界：automatic discovery 取决于具体 agent；手工指向 `SKILL.md` 只提供仓库维护者写入的
  指令文本，不保证 agent 已安装/识别、会遵守、能调用所需工具或实际执行命令。读取 skill 不会
  自动扩展用户授权，也不形成 filesystem/network/credential sandbox；执行前仍须审查目标 revision
  的 skill、references 与 scripts，按 agent/platform 的权限机制处理副作用和秘密。
- 禁止：把“ask it to use”描述成强制 enforcement；把未运行检查写成 pass；用 `precheck-pr` 代替
  CI、maintainer review 或 accepted design；因为多个 skill 可组合就让它们越过 issue scope，或
  假设不同 coding agent 对 `.claude/skills` 有相同 discovery/invocation 语义。
- 验收：交付记录 task authority、选用的 skill 与理由、实际命令/结果、未运行项、diff review 和
  reviewer owner；若要声称跨 agent 可发现/执行，必须增加至少一个受支持 agent 的 pinned-version
  behavioral eval。PR #6029 没有此类 agent eval，因此只建立 contributor guidance。^[PR #6029]

## DOCSKILL-1c — Python example policy 只审新增路径并共享一份分类合同

- 触发：`precheck-pr` 或 `review-pr` 遇到在 `examples/` 下新增、复制或重命名的 Python
  destination path。
- 强制：从目标 revision 的 merge base 以 `ACR` path census 选出候选，再读取文件行为而不只看
  文件名；model、checkpoint、vendor 或 family 专属的 prompt、request/output adaptation 与 launch
  config 必须回 production model module 或 `model_extras`，用户命令和验证证据进 task docs/recipe。
  两个 skill 必须引用同一份 canonical policy；shared image runner 的生产边界继续服从
  [EXEC-6a](../components/model-executor/rules.md#exec-6a-shared-image-example-先建-canonical-envelopemodel-extra-只做特化变换)。
- 禁止：报告仅修改或删除的既有 model-specific example 债务；因文件名看似 generic 就接受内部只
  实现一个模型合同的脚本；复制 policy 到 reviewer workflow 后分别演化；把 skill blocker 描述为
  已有 CI gate。
- 验收：分别覆盖 add、copy、rename、modify、delete，且 generic-looking model-specific 脚本必须
  block；真正 model-neutral、由配置选择模型的 task/protocol entrypoint 可通过。检查两个 skill 的
  reference 都解析到 canonical policy，并把结果作为独立 examples-policy 维度报告。^[PR #6046]
