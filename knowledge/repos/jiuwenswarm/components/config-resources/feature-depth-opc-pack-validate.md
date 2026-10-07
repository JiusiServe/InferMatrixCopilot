---
title: "OOXML 打包与 schema 校验（opc/pack.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L87-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L147-L152, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L94-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py:L187-L199, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py:L178-L184, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L101-L117, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L94-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L131-L143, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/validate.py:L158-L195, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L62-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/editing.md:L49-L95]
feature: "opc-pack-validate"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/unpack.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/validate.py"]
---

# OOXML 打包与 schema 校验（opc/pack.py）：实现深读

[功能概览](feature-opc-pack-validate.md) · [owner 入口](_index.md)

<!-- kb:depth feature=opc-pack-validate facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f5e06e7c155b951a1b6d8a1815c402b154c8a08f639752c57ce67221873b455 -->
**pack() 校验通过后在临时目录压缩 XML 并写出 ZIP**
pack() 先（默认）执行 repair_all 与 validate；若校验有错误，记录前 20 条并抛出 PackError 拒绝写出。否则把 unpacked 复制到临时目录，对每个 *.xml 与 *.rels 执行 condense，按排序且把 FIRST_ENTRY 指定的条目排最前，以 ZIP_DEFLATED 写入 output。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L94–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L94-L126)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":126,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"517540bbd7b9d4a635d4b0a1a83ebfadcbe24261040c8bda703470a5d53b3e05","start":94}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-pack-validate facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72faa12c082904c65f5031d7487fc1da573167b98fd324b1862f50111b2db62e -->
**pack(unpacked, output, do_repair=True, do_validate=True, original=None) 前置校验与失败契约**
pack() 要求 unpacked 是目录且 output 后缀（小写比较）属于 SUPPORTED={".pptx",".docx",".xlsx"}，否则抛 PackError；validation 失败时抛 PackError 拒绝写 output。main() 把 PackError 转成 SystemExit，保持函数可作库使用。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L87–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L87-L110), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L62–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L62-L62), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L147–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L147-L152)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":110,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"eea1623c7bbff2159d7350b2318b19591ff75ad2764c554935027f12fa0196ce","start":87},{"end":62,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"35d7bc1b23cfb7ac0c8166f1086e96f2986d9af5a68a1edcca55a24d379fdad4","start":62},{"end":152,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"ac725f660d06c421ad78c1ab5716663bd93d8a4b46006e05fe4c51b562c88f78","start":147}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-pack-validate facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a88d140d5a26dd75130d74e16204caaf53b6015222dba6b3e97057cf8e2c5970 -->
**do_repair/do_validate 默认开启，--no-repair/--no-validate 关闭，--original 作为校验基线**
_run() 的 argparse 定义 `--no-repair`、`--no-validate`（store_true）与 `--original`，并以 `do_repair=not args.no_repair, do_validate=not args.no_validate` 调用 pack()。original 传入 validate 的 baseline；基线错误按 _fingerprint（去掉行号的 part+message）过滤，仅报告基线中不存在的缺陷，基线不可读时报告全部错误。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L131–L143](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L131-L143), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/validate.py:L158–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/validate.py#L158-L195)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":143,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"6da3ead0649f7f2afe6c5ffe69937aaeccaac071b9bb707361d95d07531e7abe","start":131},{"end":195,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/validate.py","sha256":"8d57abecc47b5cba353c4519ac3ae0a1c5692b39d88d8a3d1a55191a6071e8b7","start":158}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-pack-validate facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ab2b41df831de0613ec567067dfcf74500e1f0c5bc7e9dd3c733c43a0ee75db -->
**pack 依赖 repair.repair_all 与 validate，且 repair 会就地改写源目录**
pack 直接调用 repair_all(unpacked) 与 validate(unpacked, baseline=original)。repair_all 对每个 *.xml 逐条应用 5 条规则并当文本变化时就地 write_text，因此 do_repair=True 时传入的 unpacked 目录本身被修改，发生在 condense 的临时 staged 复制之前。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L94–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L94-L102), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py:L187–L199](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py#L187-L199), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py:L178–L184](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py#L178-L184)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":102,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"92f18422e2dfcf1627c678013d6e37621da78e780f5852877bb6cf3cfa2f57c7","start":94},{"end":199,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py","sha256":"9c44efdfbc7653a0724007eef68de5dcde63cc09ec793b9f68cafe56998e4cc6","start":187},{"end":184,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/repair.py","sha256":"46ec334ff0db7ab989782ea2ab727b151cc667e4ab407e58efec1cdf19d4aea9","start":178}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-pack-validate facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=487f27dda731a8b00b9045bccb15fca5a341e67d141a11444badb6abea484d8e -->
**非目录/非法后缀/校验失败均抛 PackError，main() 转为 SystemExit**
unpacked 非目录或 output 后缀不在 SUPPORTED 时抛 PackError；validate 返回错误时记录前 20 条并抛 `pack: refusing to write {output}`，中止写入。main() 捕获 PackError 并 raise SystemExit(str(exc))。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L87–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L87-L110), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L147–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L147-L152)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":110,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"eea1623c7bbff2159d7350b2318b19591ff75ad2764c554935027f12fa0196ce","start":87},{"end":152,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"ac725f660d06c421ad78c1ab5716663bd93d8a4b46006e05fe4c51b562c88f78","start":147}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-pack-validate facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=083197415959fab8551ab2307c4af44619615ce307a8e6dce51c7cf91c6bafd3 -->
**验证失败拒写 output（安全）换取整目录复制到临时目录（成本）**
设计推断（非作者历史意图）：

收益（推断）：validate 报错时 raise PackError refusing to write，output 不会被新写入的坏包覆盖。成本（推断）：每次打包都要 copytree 到 TemporaryDirectory 并对全部 *.xml/*.rels 重新解析写出。注意源目录并非全程只读——repair_all 已在此之前就地改写。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py:L101–L117](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py#L101-L117)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":117,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/pack.py","sha256":"c94fde73abac86953ce06da3132c30c3db92dd6a0f3a26a0d4ae5f2ed9021ed3","start":101}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-pack-validate facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a5c09fd99efa09225017603f7d6d989e71947a80cf8b49f964ca1dbf35749d23 -->
**editing.md 中记录的 pack.py 手动流程（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档给出具体操作 `python scripts/opc/pack.py unpacked/ output.pptx --original input.pptx`，并声明其效果为校验、修复、压缩 XML、重新编码弯引号。这是 documented_manual 证据，本条未执行该流程；未见任何针对 pack.py 的自动化测试断言。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/editing.md:L49–L95](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/editing.md#L49-L95)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":95,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/editing.md","sha256":"f6835cf0498f61f3669389df44ad73e682b72727e0418b9668df7282aec3be64","start":49}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
