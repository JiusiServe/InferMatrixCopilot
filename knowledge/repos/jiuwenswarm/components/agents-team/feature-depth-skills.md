---
title: "技能安装、挂载与发现：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L811-L877, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/archive_store.py:L1-L35, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L6331-L6343, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/archive_store.py:L87-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L995-L1014, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L903-L915, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L786-L809, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1816-L1824]
---

# 技能安装、挂载与发现：实现深读

[功能概览](feature-skills.md) · [owner 入口](_index.md)

<!-- kb:depth feature=skills facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d38917f7d966362a0e975cae9b4fad450f3752cd42cef45a44eb78b7bfc7ddfd -->
**skills.list 的开关默认值与技能目录位置**
handle_skills_list 的 refresh_marketplaces 默认 False（True 时先对已配置 marketplace 执行 clone/pull 再扫描），with_installed 默认 False（True 时同响应附带 plugins，避免网关串行两次 RPC）。本地技能目录由 get_agent_skills_dir() 给出：~/.jiuwenswarm/agent/workspace/skills（get_agent_workspace_dir()/skills）。

来源：[jiuwenswarm/server/runtime/skill/skill_manager.py:L786–L809](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L786-L809), [jiuwenswarm/common/utils.py:L1816–L1824](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L1816-L1824)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","start":786,"end":809,"sha256":"b32f6f369ac7b684bdeb9c010f7fb43a60f15ad887d3a227a34e5a03d5c6aec7"},{"path":"jiuwenswarm/common/utils.py","start":1816,"end":1824,"sha256":"2fafb1938cc8c02d020440f61748f8a758d4e0c81096c6da661e519294d513dc"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skills facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d8924afe4a16b8501d39e73bb116440df0e75f1579eefd966264540219b1a9f -->
**版本真值依赖 archive_store 而非插件登记**
handle_skills_installed 不再信任 installed_plugins[].version，而是对每个 skill 用 _resolve_local_skill_dir 定位目录后调 archive_store 的 get_current_version，从 Skill 根目录 .archive/versions/index.json 读取版本；读取失败（SkillArchiveError）时版本回退为 None 而非中断整个列表。这一耦合把版本真值收敛到技能目录内，使登记数据与磁盘可分叉。

来源：[jiuwenswarm/server/runtime/skill/skill_manager.py:L811–L877](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L811-L877), [jiuwenswarm/server/runtime/skill/archive_store.py:L1–L35](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/archive_store.py#L1-L35), [jiuwenswarm/server/runtime/skill/skill_manager.py:L6331–L6343](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L6331-L6343)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","start":811,"end":877,"sha256":"feca6d45ff1438125dc80e8c73e55811a7f1f8d27905558fc53c5ed6d318037c"},{"path":"jiuwenswarm/server/runtime/skill/archive_store.py","start":1,"end":35,"sha256":"01dfc1c7310197a2c535a4ac2d51b1d08f2a1fd43986a25290ae1984c7f1d7a1"},{"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","start":6331,"end":6343,"sha256":"02bec404b0ee2743d475006d958394d17b64c3d62bfb9eb8eb2c4c3b6c12450a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skills facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a8939ef87da0a86f888633057f619222b12cf5fe49f4e7bb92b7573a23d4b94f -->
**索引损坏与图片改写失败的传播**
.archive/versions/index.json 损坏或无法解析时 read_versions_index 抛 SkillArchiveError(ERROR_INDEX_CORRUPT，即 "SKILL_VERSION_CONTENT_INVALID")，handle_skills_get 将其原 code/message 转为 SkillRpcError 向上层透传。正文中本地图片改写（rewrite_skill_markdown_images）抛任何异常时仅 logger.debug 记录并返回原文，不影响 skills.get 成功返回。

来源：[jiuwenswarm/server/runtime/skill/archive_store.py:L87–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/archive_store.py#L87-L100), [jiuwenswarm/server/runtime/skill/skill_manager.py:L995–L1014](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L995-L1014), [jiuwenswarm/server/runtime/skill/skill_manager.py:L903–L915](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L903-L915)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/skill/archive_store.py","start":87,"end":100,"sha256":"c232465f62d7773048d837622746db84c695012d53952d1b536c75c2e7800530"},{"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","start":995,"end":1014,"sha256":"7f8a5275ea6b5fe2173093cd5f5ce430b0863a7eec4168e9d84c6745098cbebf"},{"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","start":903,"end":915,"sha256":"743428a46bb420f032261df64fbdee61c8644712a74d73085b7ab7c52c9f1142"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skills facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=410b6f92848189cee0e433bbf3db9e89a30545826ed73b957e4d341d1df5f709 -->
**with_installed 合并响应**
设计推断（非作者历史意图）：

推断：skills.list 的 with_installed 把 installed 列表并入同一次响应，收益是网关不必串行处理两次 RPC、避免列表刷新超时或排队过久；代价是单次响应变大，且 installed 计算里的逐目录版本读取开销被计入 list 请求。设计动机来自函数 docstring，代码本身只证明该合并行为存在。

来源：[jiuwenswarm/server/runtime/skill/skill_manager.py:L786–L809](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L786-L809)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","start":786,"end":809,"sha256":"b32f6f369ac7b684bdeb9c010f7fb43a60f15ad887d3a227a34e5a03d5c6aec7"}],"trace":[]} -->
<!-- /kb:depth -->
