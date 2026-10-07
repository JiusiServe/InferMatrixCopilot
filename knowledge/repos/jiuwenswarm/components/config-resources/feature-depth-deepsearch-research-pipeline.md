---
title: "openJiuwen-DeepSearch 深度研究执行管线：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L200-L230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L80-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L41-L46, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L147-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L6-L34, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L152-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L225-L230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L233-L235, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/SKILL.md:L12-L16]
feature: "deepsearch-research-pipeline"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/validate_environment.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/convert_docx.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/convert_html.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/verify_skill_structure.py"]
---

# openJiuwen-DeepSearch 深度研究执行管线：实现深读

[功能概览](feature-deepsearch-research-pipeline.md) · [owner 入口](_index.md)

<!-- kb:depth feature=deepsearch-research-pipeline facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be2418432ff44117fb9616719aae57119f77d5fced28f2a6c247ca42ad3df7c2 -->
**execute_deep_search 同步封装异步工作流并返回报告或 None**
execute_deep_search(query) 先调用 load_agent_config() 加载配置，再用 asyncio.run(run_jiuwen_workflow(query, agent_config)) 执行工作流；结果非空则返回报告字符串，为空时记录 warning 并返回 None。run_jiuwen_workflow 内部通过 AgentFactory 创建 agent，异步消费 agent.run 的 chunk 流，用 parse_endnode_content 提取最终报告。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L200–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L200-L230), [jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L80–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L80-L98)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":230,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"e997812ffab064c9367d0939ca491efc6f496e2d5b80af72c3c157c5d9d4a1ff","start":200},{"end":98,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"1b6943e38660453b755d2a35834cc6d221345c82888178020befe4e3fd7564e9","start":80}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deepsearch-research-pipeline facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa669813fbeda4fde2c6e8f4975bfd8c22ba887c8724f9cdc0f0d3f72fff004c -->
**execute_deep_search(query) 返回报告字符串，捕获 ValueError 与 Exception 时返回 None**
execute_deep_search 接收研究题目 query，加载配置后用 asyncio.run 执行 run_jiuwen_workflow；结果非空则返回该字符串，为空记 warning 返回 None，ValueError 与 Exception 分支记日志后同样返回 None（不覆盖 BaseException）。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L200–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L200-L230)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":230,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"e997812ffab064c9367d0939ca491efc6f496e2d5b80af72c3c157c5d9d4a1ff","start":200}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deepsearch-research-pipeline facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=521d68b0baf6c1390513e310d454a64e03699bb5333e1ac84b660b984b35464d -->
**SKILL_ROOT 环境变量默认脚本上级目录，.env 仅为推荐配置位置**
SKILL_ROOT 取环境变量，未设置时默认 Path(__file__).parent.parent，并 load_dotenv(SKILL_ROOT/.env)。load_agent_config 用 os.getenv 检查进程环境中必需变量（含 WEB_SEARCH_API_KEY/WEB_SEARCH_URL），缺失时抛出列出变量名的 ValueError，提示语仅建议写入 .env 文件。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L41–L46](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L41-L46), [jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L147–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L147-L161)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":46,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"1e407cbed3073ef7c6d88922453275bf982b9677f7cd3c028302f5592514dc2d","start":41},{"end":161,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"6474e949455b994b1275bbab524f3093c4ce9ad014e64e6aef4d1fb243b906ee","start":147}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deepsearch-research-pipeline facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5934d819f47f72821f4a96dc6b368ef011e9ea6a0574c1c22328137e966b2bd7 -->
**管线依赖 openjiuwen-deepsearch==0.1.1 并直接导入其 Config/AgentFactory/LogManager**
模块 docstring 声明依赖 openjiuwen-deepsearch==0.1.1 与 python-dotenv；源码实际 from openjiuwen_deepsearch 导入 Config、ExecutionMethod、AgentFactory、ResultExporter、parse_endnode_content、LogManager，并从本地 convert_docx/convert_html 导入转换函数，构成对 SDK 与本地脚本的硬耦合。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L6–L34](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L6-L34)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":34,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"3c3eb68e0f48743466c5837a681deb74ea2f6253bbf0db0b0c02046fe8a8995a","start":6}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deepsearch-research-pipeline facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=957e3ad116035cc8f530bbf414a3ef3b78c8299d35183fd504faa1a55d57b340 -->
**缺环境变量抛 ValueError，execute_deep_search 捕获后返回 None**
触发条件：任一必填环境变量为空，load_agent_config 在 guard `if missing_vars:` 中 raise ValueError；execute_deep_search 的 `except ValueError`/`except Exception` 分支记录日志并 return None，异常不向外传播，仅以 None 结果呈现。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L152–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L152-L161), [jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L225–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L225-L230)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":161,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"3a3254b773cf7cc63a4ae0df149133bc0739b92ac1d583ffa8123e7a7be1dc9c","start":152},{"end":230,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"12be8bea252df1cf82fbdd1c45ea03371db11999390daa3742c9cb1821e5e0ae","start":225}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deepsearch-research-pipeline facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9d8d2da2445bbb72d2889d2ab087e7b14182f059738076f78b3cc85640c540d0 -->
**execute_deep_search 吞掉 ValueError/Exception 便于调用方，但错误细节只在日志中**
设计推断（非作者历史意图）：

益处：Agent 调用方拿到的失败结果统一为 None，不会因配置缺失（ValueError）或其他 Exception 中断。代价：异常的具体原因仅写入 logger.error/exception，调用方无法从返回值区分失败原因（推断）。另 run_background 以注释说明其检查用于防止后台自我重启的无限循环。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L225–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L225-L230), [jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L233–L235](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L233-L235)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":230,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"12be8bea252df1cf82fbdd1c45ea03371db11999390daa3742c9cb1821e5e0ae","start":225},{"end":235,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py","sha256":"cdff58e0bd4d3d8f160e758a4dc13775decf18f305228f44dca53e69fd1b559a","start":233}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deepsearch-research-pipeline facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3cfa2c97fb2ac8fd41707c3eca587a3cd18c4b7beb5f3b0f17fab01ee9e2723 -->
**SKILL.md 记录的手动验收流程（仅环境预检与启动观察，未执行）**
文档中的人工验收步骤（本轮未执行）：

文档化手动流程（NOT EXECUTED）：先确认技能目录存在 .venv 与已填写的 .env（占位值不算），再运行 uv run "scripts\main.py" --mode query --query "<标题>"，随后读取技能文件夹根目录 PID.info 中的后台子进程 PID，等待约15分钟，并通过该 PID 进程与技能文件夹中的 Markdown/Doc/Html 文件列表判断报告是否生成完成。仅覆盖预检与启动/观察步骤，未含报告内容的断言。

来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/SKILL.md:L12–L16](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/SKILL.md#L12-L16)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":16,"path":"jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/SKILL.md","sha256":"a4ea118ed6722268063dffb1182c899197f63ea787c359290817211346a271ae","start":12}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
