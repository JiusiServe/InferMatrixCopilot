---
title: "一键成片流水线与质量门禁（finalize_deck.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L117-L137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L100-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L192-L197, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L139-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L56-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L132-L137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L44-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/workflows/create-deck.md:L121-L133, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md:L26-L28]
feature: "ppt-deck-finalize"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/make_blank_template.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/fill_cover.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/prune.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py"]
---

# 一键成片流水线与质量门禁（finalize_deck.py）：实现深读

[功能概览](feature-ppt-deck-finalize.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ppt-deck-finalize facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=25750d50e30f6d9570b53e4f8589beb6f7fe0495b63efbf03d9d434f79087dbb -->
**_run 在校验输入后用 run() 依次解包 template 与 content 到工作目录**
_run 解析参数后检查 content 与 template 文件存在且 content/out 不在 SKILL_ROOT 内；workdir 取 --keep-workdir 指定目录，否则新建临时目录，然后通过 run() 先后调用 unpack.py 解包 template 到 tdir、content 到 sdir。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L117–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L117-L137)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":137,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"11a39c13b8fa89948ef5198884af8448d38f4a1fb7d6aef6c131b6a8d430ebca","start":117}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-deck-finalize facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8507a3bcf7416cf7b44e296863c0f782b18855ba4351f06455c1d3493727950a -->
**CLI takes positional content and out; main maps FinalizeError to SystemExit**
finalize_deck.py accepts positional args `content` (generated content .pptx) and `out` (final .pptx to write); main() calls _run() and, on FinalizeError, raises SystemExit(str(exc)) chained from it, per its docstring keeping helpers usable as a library.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L100–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L100-L109), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L192–L197](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L192-L197)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"38577686d109ee6afd379cb6dba0f5db75daf655a57055dc22443f32ac497de7","start":100},{"end":197,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"55a3c5e21ffbdec40b9cb89c3a79db4334dd38e21d424b638f14aa20ebb355d2","start":192}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-deck-finalize facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d09b3069dfffe0b9f05b886cfb085385a40a98e6ffa7d8b6b16c2da0978c5601 -->
**Defaults: template.pptx, order "t1,s*,t5", slideLayout7.xml, source-layout-mode template**
--template defaults to SKILL_ROOT/references/template.pptx, --order defaults to "t1,s*,t5" (tN/sN/s* tokens), --template-layout defaults to slideLayout7.xml (Office's Blank), and --source-layout-mode accepts only "template" or "source", defaulting to "template".

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L100–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L100-L109)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"38577686d109ee6afd379cb6dba0f5db75daf655a57055dc22443f32ac497de7","start":100}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-deck-finalize facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5702f008068981346a8df181c20d9d457633a252d16f45d8c022220db89a8802 -->
**finalize_deck 通过 sys.executable 子进程调用同目录 scripts/opc/unpack.py，非零退出即抛 FinalizeError**
run() 用 subprocess.run([sys.executable, *argv]) 执行子脚本；SCRIPTS 定位为 finalize_deck.py 所在目录（SKILL_ROOT 为其父目录），_run() 先后调用 SCRIPTS/opc/unpack.py 解包模板与内容。任一子进程 returncode != 0 时抛 FinalizeError，提示用 --keep-workdir 检查中间目录。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L56–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L56-L66), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L132–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L132-L137)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":66,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"56221c02c958899fb7110736a343cf815953d798ddeb9684b67691b0eaec14d1","start":56},{"end":137,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"7fe15d9afdfcca105a186e895bf566c6b55fdc47bbbe308f68b9cd2157ee00ad","start":132}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-deck-finalize facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f60b223bc15a2c2649a3112442d7aa24f438dd60f0b1d315a832c47f06a83a32 -->
**Zero content slides raise FinalizeError; main converts it to SystemExit with the message**
When count_slides(sdir) returns 0, _run raises FinalizeError("finalize_deck: no slides found in {content}"); main() catches FinalizeError and re-raises SystemExit(str(exc)), terminating the process with the fatal message.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L139–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L139-L146), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L192–L197](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L192-L197)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":146,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"9f765a240ab321bd04d3a646d97cdfe4d685aa556cac2696ec14c4379f0a28e7","start":139},{"end":197,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"55a3c5e21ffbdec40b9cb89c3a79db4334dd38e21d424b638f14aa20ebb355d2","start":192}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-deck-finalize facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2633e3be9c59adecf819c6c084e2e70057749ced146bb6f31ae2b4f9a079119 -->
**helpers 抛 FinalizeError 而非 SystemExit 以保持库可用；代价是进程入口需自责转换**
设计推断（非作者历史意图）：

FinalizeError 的 docstring 说明在入口外抛 SystemExit 被禁止且使函数无法作库使用；main() 捕获 FinalizeError 并转为 SystemExit(str(exc))。推断的代价：经由 main() 运行时错误以退出消息呈现，库式调用方需自行捕获 FinalizeError。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L44–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L44-L49), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L192–L197](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L192-L197)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"df59311b6c7f24be8dd4aa59e1581cddf05a441e5a61a3dc71d8830d25be79b7","start":44},{"end":197,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py","sha256":"55a3c5e21ffbdec40b9cb89c3a79db4334dd38e21d424b638f14aa20ebb355d2","start":192}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-deck-finalize facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d10bcce2784f82a110420228b2d0c0e05a2e6296af18f6e0ddef2acc56448b6b -->
**文档化手工流程：finalize_deck.py --cover-title 与收尾门禁（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档记载的手工验证（NOT EXECUTED）：运行 `python3 ../scripts/finalize_deck.py output/content.pptx output/final.pptx --cover-title "..." --cover-meta "部门|作者|日期"`，脚本封装 unpack→merge→fill_cover→clean→pack 并在结束时自检，打印页数/母版/版式摘要；若未传 `--cover-title`，收尾的 cover-title 硬门禁判失败（模板 ctrTitle 出厂为空且合并流程不写入）。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/workflows/create-deck.md:L121–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/workflows/create-deck.md#L121-L133), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md:L26–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md#L26-L28)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":133,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/workflows/create-deck.md","sha256":"7e9436b79df75c68bbc6150e60ef04d133b14b50876a4dfa44d10503356c2100","start":121},{"end":28,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md","sha256":"03a9aca0c86039540cf4953130dc24af0e5de4ec93546145b41f1e0bae1ba988","start":26}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
