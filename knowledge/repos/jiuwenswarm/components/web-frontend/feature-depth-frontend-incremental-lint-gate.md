---
title: "增量 ESLint 门禁（相对基线只报新增诊断）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L1-L5, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L16-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L28-L31, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L33-L46, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L7-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L26-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L54-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L9-L10, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L22-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L28-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L49-L72, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L11-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L75-L81, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L36-L45]
feature: "frontend-incremental-lint-gate"
entry_points: ["jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs"]
source_globs: ["jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs"]
---

# 增量 ESLint 门禁（相对基线只报新增诊断）：实现深读

[功能概览](feature-frontend-incremental-lint-gate.md) · [owner 入口](_index.md)

<!-- kb:depth feature=frontend-incremental-lint-gate facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c36f1164f2330798e89a9d3bd3c8501a128aa8ed13b3453cd3723854373d1472 -->
**变更 TS/TSX 文件逐个做基线/当前 lintText 对比，按 multiset 扣除既有诊断**
对每个变更的 .ts/.tsx 文件（须位于 cwd 下且未被 ESLint ignore），用 git show 取基线内容，分别 lintText 基线与当前文本；当前诊断按 [ruleId, severity, message] 键与基线计数逐条抵扣，剩余的新诊断重算 error/warning 计数后收集到 introduced。

来源：[jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L26–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L26-L26), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L28–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L28-L48), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L49–L72](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L49-L72)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":26,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"2c0140e1815a62c81d8bc84494d979710d9e8d8e32c278a874893fe3be72c950","start":26},{"end":48,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"64eac5591f4e9c493a1eee2c040c075d03b967e10f60d17d0dea83aa90bf2c58","start":28},{"end":72,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"739dfc17aef9dbb679f1790e145507b7cc87b23ed3240c12a760868ae548e9f1","start":49}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=frontend-incremental-lint-gate facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f7d31ea9ab65fd723c8ceb93ec9b6aee2ce2629dace339c2ec7ea2dc5a7c7d2c -->
**ESLint 以 frontend 目录为 cwd 且 reportUnusedDisableDirectives: 'error'；其余规则按该 cwd 下的默认配置解析**
cwd 固定为脚本目录的上一级（frontend 根），git 与路径解析均用它；new ESLint({ cwd, reportUnusedDisableDirectives: 'error' }) 显式开启未使用 disable 指令报 error，ESLint 配置文件本身未在脚本中显式指定，由 ESLint 在该 cwd 下的默认解析决定。

来源：[jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L9–L10](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L9-L10), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L22–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L22-L22)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":10,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"85135a79988ada268c503ca91367f3fb4cda9d414adcfc7f54ce98997fbfef3b","start":9},{"end":22,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"e0b8375282302814ad92da0b71878fde4425c01cb476dbb5db9b1aae88a48fcf","start":22}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=frontend-incremental-lint-gate facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=496824576280fa84684327b2b70e95c5c7b6129d62dd1eb56ef965bc1b87f269 -->
**依赖 git 子进程与项目内 eslint 包，路径换算受仓库布局约束**
通过 execFileSync 调 git（rev-parse/diff/ls-files/show），ESLint 类直接 import 自 'eslint' 包并以 frontend 为 cwd，因此使用 frontend 自己的 lint 配置；git diff 输出仓库相对路径而 ls-files 输出 cwd 相对路径，脚本用 prefix 剥离来统一两者。

来源：[jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L1–L5](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L1-L5), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L16–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L16-L22), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L28–L31](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L28-L31)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":5,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"4735ec523f55e4216ab8eee5704c85f863429ac90d38bd49aa3cca934ab6f3ff","start":1},{"end":22,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"60ac676f67047c884e7b3a96be4cd1bdad99b246a4815cee700482a71c4a715a","start":16},{"end":31,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"eee383b2e46fbcbce8f8542506313ecdb1bcb11ec466f499f817d199f6edf78d","start":28}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=frontend-incremental-lint-gate facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e1c34af6e401dab8ae34529be5ce393c20f2cfad9c600830363ea95dd5636da4 -->
**git show 仅对'基线中不存在该路径'容错，其余 Git 错误原样抛出**
读取基线内容包在 try/catch 中：stderr 含 'does not exist in' 或 'exists on disk, but not in' 时视为新文件（previous 保持 ''），其他 Git 失败 rethrow 而不弱化检查；非 frontend 内或被 ESLint ignore 的文件直接 continue 跳过。

来源：[jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L33–L46](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L33-L46)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":46,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"fb26d99a49a75345d7457a090049863d872e0ad0a621d5f9b2da2974d2868232","start":33}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=frontend-incremental-lint-gate facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb5bc9fe306ddff32a614a9331626d895aa6d919c713aa81900977c5d1fd20b1 -->
**增量门禁放行存量诊断，但错误与警告一律拦截**
设计推断（非作者历史意图）：

收益：基线已有的诊断不阻塞本次检查（existing 计数仍可见，npm run lint 保留全量视图）；成本：warnings 也会失败，且诊断按 [ruleId, severity, message] 三元组抵消——同一规则同一文案的基线诊断可抵消本次同键新增，位置变化不区分（推断：键中不含行号）。

来源：[jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L7–L8](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L7-L8), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L26–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L26-L26), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L54–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L54-L61)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"a128cea397747bd87d6c7800b2c31511872cc365c7bcadb05d8fb138335fa9c2","start":7},{"end":26,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"2c0140e1815a62c81d8bc84494d979710d9e8d8e32c278a874893fe3be72c950","start":26},{"end":61,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"4204478974375d10e1547b0eef477295a4229b85a8ddb7fe16a5e0a79f5561c7","start":54}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=frontend-incremental-lint-gate facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3866a341b1bd7dd0652a2708768afa044e7d336d13f4b45855a6e76ebac55490 -->
**lint-changed 脚本的参数契约与非零退出（有新增诊断时）**
可选参数仅 `--base <commit>`，缺省 `HEAD`，由 `git rev-parse --verify <ref>^{commit}` 解析；参数形式不符时抛出 Usage 错误终止。循环结束后若 introduced 非空，打印 stylish 格式结果并将 `process.exitCode` 置 1（L75-77），随后顺序输出 checked/新增/既有计数摘要（L79-81）；该摘要仅在执行到达此处时打印——参数错误（L13）或被重新抛出的 Git 失败（L44）会提前终止。

来源：[jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L11–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L11-L15), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L75–L81](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L75-L81), [jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs:L36–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L36-L45)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":15,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"1a857b2c897bf75f02f6337ed973e15b675f94e48155ff80ca18cf006aeed239","start":11},{"end":81,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"52300059f76f349cc10d7ed5ef2666de1a17e35918cba3834c3f862fd47afe1d","start":75},{"end":45,"path":"jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs","sha256":"b269828f18b850a5cf14a450e31e92a99da9c0b89d1aa61c764d82248f1c25f2","start":36}],"trace":[]} -->
<!-- /kb:depth -->
