---
title: "XLSX 公式静态校验（formula_check.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L27-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L60-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L17-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L38-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L9-L11, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L30-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L24-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L61-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L67-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L82-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L169-L172, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L3-L11]
feature: "xlsx-formula-check"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py"]
---

# XLSX 公式静态校验（formula_check.py）：实现深读

[功能概览](feature-xlsx-formula-check.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xlsx-formula-check facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d543d2032865ef4198163fe6296fdb3ee189f1c8664c28990639ca8bcf584729 -->
**_scan 两遍读取工作簿并汇总 issue 列表**
_scan(path) 先以 data_only=True 只读加载工作簿，遍历所有工作表单元格，缓存值为字符串且包含任一 ERROR_TOKENS 时记录 {sheet, cell, type:"cached_error", detail}；再以 data_only=False 只读加载一遍，对以 "=" 开头的公式文本做同样的 token 匹配并记录 type:"formula_error"，最后返回 issue 列表。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L27–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L27-L57)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":57,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"df8576884789c47ccd704f89b099164796898cd4f9480cab617f95036647b1a1","start":27}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-formula-check facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9454a99661114a7d211b555572dc2b7e318b718035fc8ea2a4ba05235a9f8b4d -->
**main 的 CLI 契约：位置参数 file，--json/--report 布尔旗标，返回 0/1**
main() 用 argparse 接受一个位置参数 file 和 --json、--report 两个 store_true 旗标，返回 0（无 issue）或 1（有 issue）；--json 时输出 {"ok":bool,"issues":[...]} 的缩进 JSON，否则打印 "OK: ..." 或逐条 "[type] sheet!cell -> detail" 文本。调用方需自行传入可被 openpyxl 加载的 xlsx 路径。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L60–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L60-L79)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":79,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"90ac628c6dd6f2adfca50e361fb45b2e2736a7d129705721b61152e8e5d8adcc","start":60}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-formula-check facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=176e37d58ff48f6e883c8927018fb234da13a9a91517f05b36cbbd058d37c51a -->
**错误 token 列表硬编码，CLI 两个开关默认关闭，默认文本输出（在已展示的 argparse 解析器内）**
ERROR_TOKENS（#REF!、#DIV/0!、#VALUE!、#N/A、#NAME?、#NULL!、#NUM!）硬编码于 L24，所示解析器中没有覆盖它们的选项。--json 与 --report 为 store_true，默认 false；未传 --json 时输出人读文本（L69–L78）。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L24–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L24-L24), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L61–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L61-L71)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":24,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"fae3662d084aee307b2f2075dd819ffd6713a09a7ddbe68429dc7fc6c66e8def","start":24},{"end":71,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"c90b3a80bac3b6033917dc905d3135bdfcd16ceadc1e267a1c01c7380b59d24e","start":61}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-formula-check facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=14c96af5f8f0b9766251299b24bc0eb3764e59e4ef398eabe11e4ef45cbcd08f -->
**仅依赖 openpyxl，导入失败即打印并 sys.exit(2)**
脚本在模块顶层 try 导入 openpyxl 的 load_workbook 与 get_column_letter，任何异常都会向 stderr 打印 "openpyxl is required: ..." 并 sys.exit(2)；get_column_letter 用于把列号转成字母拼出单元格地址。不依赖其他第三方库。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L17–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L17-L22), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L38–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L38-L40)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"19df94d1a8c679d6a93b4e598997894ceafb51beb6cf91a2015c4d592827d710","start":17},{"end":40,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"cf7f53f41e8bfd928a7e17835495f2e80b0d3af52a341aa05823748bf401e5f5","start":38}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-formula-check facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=04bfbd58d44706e4cf373366e25745938a9878723a288f6326f63cf836ac00a0 -->
**openpyxl 导入失败时打印 stderr 并 sys.exit(2)；发现问题时 main 返回 1 并经 sys.exit(main()) 传播为进程退出码**
L17–L22 捕获导入 Exception，向 stderr 打印 "openpyxl is required: ..." 并 sys.exit(2)。L67–L79 中 issues 非空时 main 返回 1，L82–L83 的 __main__ 块以 sys.exit(main()) 将该返回值作为进程退出码。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L17–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L17-L22), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L67–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L67-L79), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L82–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L82-L83)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"19df94d1a8c679d6a93b4e598997894ceafb51beb6cf91a2015c4d592827d710","start":17},{"end":79,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"b6e191092d5e9ef403689f6970aa97d1ac09d088fe3b4396e99968208d792aad","start":67},{"end":83,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"c86a687dc0735836998a4f2d1ad0536d34c088d503731b70989149cd3c97105a","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-formula-check facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dac02b26bafd3a0bc53feb1e530542c10196b40fa819ebde1f12e1260f7b469b -->
**只读静态扫描便宜但可能基于过期缓存值**
设计推断（非作者历史意图）：

（推断）收益：read_only=True 两遍加载 + 纯字符串 token 匹配，避免执行公式的开销与副作用；代价：docstring 明言不执行公式，cached_error 检查的是文件中缓存的值，若缓存过期则结果过期——需先运行 libreoffice_recalc.py 才能得到新鲜值。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L9–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L9-L11), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L30–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L30-L30)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":11,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"69d63d909068067aeab6d7f99782553cf948a787771f4ca0a6b62e4b9f4c5c0c","start":9},{"end":30,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"573700730c9d5ea53b0342650ae292c9b357e67183f21df36e6b119f792950f7","start":30}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-formula-check facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5339e125bdd8be014f8a1fa34632d9746bd4d7314a8a01efc76cfad8be5a238b -->
**已记录的手动静态校验命令与退出码判定（未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md 记录的手动流程：`formula_check.py file.xlsx --report`，以退出码 0 判定为未发现问题；docstring 约定 0=无错误、1=发现问题、2=用法错误，且 main 中以 `return 0 if ok else 1`（L79）对应。脚本只做静态扫描、不执行公式，需要新鲜缓存值时须先运行 libreoffice_recalc.py。以上步骤在本条目中明确未执行（NOT EXECUTED）。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L169–L172](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md#L169-L172), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L3–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L3-L11), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py:L67–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L67-L79)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":172,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md","sha256":"1fea3aa06c6efe6e3aca34787a6d1abfa274466b020b6aed665260e8c65647f2","start":169},{"end":11,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"d349be78383064ec0560db511e3abac2503dff1e22ff68bc511b56d583dd6f3f","start":3},{"end":79,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py","sha256":"b6e191092d5e9ef403689f6970aa97d1ac09d088fe3b4396e99968208d792aad","start":67}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
