---
title: "技能安装、挂载与发现：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L811-L877, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/archive_store.py:L1-L35, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L6331-L6343, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/archive_store.py:L87-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L995-L1014, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L903-L915, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L786-L809, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1816-L1824, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_skill_content_images.py:L43-L88, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_skill_content_images.py:L92-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_type.py:L48-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skill_manager.py:L8673-L8675, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/skill_toolkits.py:L173-L188]
feature: "skills"
entry_points: ["jiuwenswarm/server/runtime/skill/skill_manager.py"]
source_globs: ["jiuwenswarm/server/runtime/skill/skill_manager.py", "jiuwenswarm/server/runtime/skill/*"]
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

<!-- kb:depth feature=skills facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d42c43e36b7769164bece2c969bacfa0711822562c884d6130103862877d22d7 -->
**图片改写行为的单测断言**
tests/unit_tests/agentserver/test_skill_content_images.py::test_skills_get_rewrites_relative_image_keeps_external：manager fixture monkeypatch 技能目录后写入含本地 PNG、外链 https://example.com/a.png 与缺失文件的 SKILL.md，调用 handle_skills_get（name=visual-doc、_session_id=sess-1），断言返回 content 含 /file-api/download?token= 与 session_id=sess-1、外链与缺失路径保持原文，且磁盘 SKILL.md 仍含 assets/flow.png、不含 /file-api/download。

来源：[tests/unit_tests/agentserver/test_skill_content_images.py:L43–L88](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_skill_content_images.py#L43-L88), [tests/unit_tests/agentserver/test_skill_content_images.py:L92–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_skill_content_images.py#L92-L125)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":88,"path":"tests/unit_tests/agentserver/test_skill_content_images.py","sha256":"5af9d2abd24719995e333874e9242076368e763d6bd4757d4f65f9694069e515","start":43},{"end":125,"path":"tests/unit_tests/agentserver/test_skill_content_images.py","sha256":"d21207d8263afdea19294bd2bf7955d7ca3809bf33c977af0c995facf0c0b6cc","start":92}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skills facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b047216812b2e42296bf5b201df3e11c66d00238dbd75071a4a92dc52a58d5f8 -->
**detect_skill_type 类型判定流程：目录无效或全部未命中时返回 SKILL_TYPE_SKILL**
skill_dir 为 None 或非目录时直接返回 SKILL_TYPE_SKILL；否则依序判定 is_skillpack→SKILL_TYPE_SKILLPACK、_frontmatter_kind_is_swarm→SKILL_TYPE_SWARM、_has_multimedia_asset→SKILL_TYPE_MULTIMODAL，均未命中返回 SKILL_TYPE_SKILL。

来源：[jiuwenswarm/server/runtime/skill/skill_type.py:L48–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_type.py#L48-L61)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/server/runtime/skill/skill_type.py","sha256":"5d40062cb0a78bf46dd9202812785bcdb68a52f14613cca3bb96d2dc69b7f890","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skills facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=960f35535a4a9208ad7fc6af848e872477263e5551aa69503950d1bfa6b9fdb6 -->
**get_local_skills(self) -> list[dict] 返回 local_skills 记录的列表副本，键缺省时为空列表**
SkillManager.get_local_skills(self) -> list[dict]，实现为 list(self._state.get("local_skills", []))，键缺省时返回空列表。工具侧 _find_installed_by_target 消费该列表：跳过非字典项，仅当传入 source 与记录 source 均为 "skillnet" 且记录 origin 等于去空白后的 identifier 时按 name 构造已安装项；identifier 为空直接返回 None。list() 仅给出列表级副本，所示代码不证明嵌套字典被深拷贝。

来源：[jiuwenswarm/server/runtime/skill/skill_manager.py:L8673–L8675](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_manager.py#L8673-L8675), [jiuwenswarm/agents/harness/common/tools/skill_toolkits.py:L173–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/skill_toolkits.py#L173-L188)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8675,"path":"jiuwenswarm/server/runtime/skill/skill_manager.py","sha256":"104029b2a7932d482b1077a64b57a38f7e8642cb447606f8b7dc94e303edb276","start":8673},{"end":188,"path":"jiuwenswarm/agents/harness/common/tools/skill_toolkits.py","sha256":"644f729008790d5e4f53f4e6ae992b257377c135fecb0765e0ec69340f3462dc","start":173}],"trace":[]} -->
<!-- /kb:depth -->
