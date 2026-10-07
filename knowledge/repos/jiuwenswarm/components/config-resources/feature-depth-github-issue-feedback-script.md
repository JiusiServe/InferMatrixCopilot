---
title: "GitHub Issue 反馈创建脚本：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L18-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L54-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L11-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L29-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L9-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L48-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L34-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L31-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L15-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L18-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L39-L51]
feature: "github-issue-feedback-script"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py"]
---

# GitHub Issue 反馈创建脚本：实现深读

[功能概览](feature-github-issue-feedback-script.md) · [owner 入口](_index.md)

<!-- kb:depth feature=github-issue-feedback-script facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=478cc7050c4b136b9be664d3c1cabe0a423b8b2c54a286d19a2896ae704921c0 -->
**main 完成 path：token 解析守卫通过后构造 GitHub 客户端并调用 issues.create，打印 parsed_data 并返回 0**
main(argv) 先 argparse 解析 title 与必需的 --body；token 取 os.getenv("GITHUB_ACCESS_TOKEN") 否则回退 args.api_key（L34）。若 token 为空，经 output_content（L15 定义为 partial(print)）向 stderr 输出 "GITHUB_ACCESS_TOKEN is not set" 并局部返回 1，不发起 API 调用（L35–L37）。否则组装 owner/repo/title/body，且仅当 --label 提供时加入 labels 列表（L39–L46），以 GitHub(auth=token) 调用 gh.rest(version=API_VERSION).issues.create(**payload)（L48–L49），随后 output_content(resp.parsed_data) 打印解析结果并返回 0（L50–L51）。返回 1/0 是函数局部返回值；L49 若抛出异常，所示 main 体内无 except，将向上传播。

来源：[jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L15–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L15-L15), [jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L18–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L18-L37), [jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L39–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L39-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":15,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"8bcdf2039422c90b8259d6a2d434938a381a51c739cb1f7231e864d5bfbcfe7a","start":15},{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"ff12473afaad4467e86cd845a1f4a39143ab405acd803632bb72fbd3f41f7ee3","start":18},{"end":51,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"6078f5a476e2269e1cd5d47b0e941045f720e0da6f664b915eda8e86a145df08","start":39}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=github-issue-feedback-script facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=97933c1f52a89f4b3df0dc9a7fd5b9155154b4741e6864e704424434fdbcca0c -->
**CLI 契约：位置参数 title，--body 必填，--label 可重复，返回进程内 int**
调用方须提供位置参数 title 和必填 --body；--label 每次 append 可重复；--owner 默认 "Trenza1ore"、--repo 默认 "GitCode-API"、--api-key 默认空。main 返回 int（0 成功、1 缺 token），作为模块运行时经 raise SystemExit(main()) 转为退出码。

来源：[jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L18–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L18-L32), [jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L54–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L54-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":32,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"b9dba8e1b4820ba78d343b82cf7e29ba5cdbcb9b171b07829d079738f7e60ab6","start":18},{"end":55,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"34336821e270180f917411b77fe541ae43e60a9670634b7c9655bc9a07ce6531","start":54}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=github-issue-feedback-script facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3fd347419d81c0261c2dc57e946c438959b7f88016e3e652ab1872642025376b -->
**token 优先取环境变量 GITHUB_ACCESS_TOKEN，其次 --api-key**
token = os.getenv("GITHUB_ACCESS_TOKEN") or args.api_key；owner/repo 默认常量 DEFAULT_OWNER="Trenza1ore"、DEFAULT_REPO="GitCode-API"，可被同名 CLI 参数覆盖。

来源：[jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L11–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L11-L13), [jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L29–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L29-L37)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"ac921eb6aaacb5ec2a405dbd4b2b810499e95c37c1ee5f73a2c5da092055a32f","start":11},{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"fc3469eed043625de35b31a08efd522a3d60ea29d74cabdb84ad4532cf546114","start":29}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=github-issue-feedback-script facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18f48aecac015553cc61e390cc09000e9c6fb4b9a14590dd9e825ad3605d678e -->
**依赖 githubkit.GitHub 执行创建，pin 到 rest version "2026-03-10"**
脚本导入 githubkit 的 GitHub 客户端并固定 API_VERSION="2026-03-10" 调用 issues.create；创建结果依赖 githubkit 的解析（resp.parsed_data）。此依赖未安装时脚本无法运行。

来源：[jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L9–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L9-L13), [jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L48–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L48-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"4133a0fdf5e5076843dae7ec193f16f151ee2fa04f7f9676ec93a65ccf10bac0","start":9},{"end":51,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"95a6e03c15003fc1ce62960db0a4560825b41186943962ef048c8bf6989b0dd8","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=github-issue-feedback-script facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8040af70c0d5f46dd96c6b6e6d236ece248289e46f6fc5c202093c989972fdd1 -->
**token 为空时向 output_content 传 stderr 并返回 1；API 异常未捕获**
当 GITHUB_ACCESS_TOKEN 未设置且 --api-key 为空（falsy）时，L34–L37 以参数 file=sys.stderr 调用 output_content("GITHUB_ACCESS_TOKEN is not set") 并 return 1，不发起 API 调用。L48–L49 无 try/except，githubkit 抛出的异常会从 main 原样传播。

来源：[jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L34–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L34-L37), [jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L48–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L48-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"adeff0004a9d667ced6bf2f64d0aab8ed6ea0aaf0b5ea1224374b8ed490df139","start":34},{"end":51,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"95a6e03c15003fc1ce62960db0a4560825b41186943962ef048c8bf6989b0dd8","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=github-issue-feedback-script facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c5042c3feefac289ceea93f5c0cb088a65a2da09617183979ec9c5e31d2af0ab -->
**环境变量优先于 --api-key：便于无人值守，但非空的旧值会覆盖 CLI 传入 token**
设计推断（非作者历史意图）：

L34 用 os.getenv("GITHUB_ACCESS_TOKEN") or args.api_key：环境变量非空时总是胜出，--api-key 仅在环境变量为空/falsy 时生效（推断：这便于脚本化无人值守运行，但代价是环境中残留的非空 token 会覆盖调用方在命令行显式传入的 --api-key）。

来源：[jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py:L31–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py#L31-L37)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/gitcode-api/scripts/open_github_issue.py","sha256":"6686eb3456dda8e8385d463f613b6b6e942006182c642aec43488ed1eb12ebd5","start":31}],"trace":[]} -->
<!-- /kb:depth -->
