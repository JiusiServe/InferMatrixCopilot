---
title: "Code 模式编码记忆：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1697-L1739, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L426-L465, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L414-L423, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L250-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L156-L198, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L104-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L133-L136, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/coding_memory_paths.py:L70-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/coding_memory_paths.py:L43-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L130-L136]
feature: "coding-memory"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/interface_code.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/interface_code.py", "jiuwenswarm/agents/harness/code/*"]
---

# Code 模式编码记忆：实现深读

[功能概览](feature-coding-memory.md) · [owner 入口](_index.md)

<!-- kb:depth feature=coding-memory facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f90a799ebec9feba491c1df4c1b2acc3834252a3acd7d2fdb6fa9b388e31d03 -->
**CodingMemoryRail 装配调用链**
JiuwenSwarmCodeAdapter._build_coding_memory_rail 以活动配置快照为输入，先经 is_memory_enabled 校验开关与 embed/project_dir/workspace 指纹决定缓存复用，再调用 create_coding_memory_rail；后者通过 _resolve_coding_memory_dir 解析项目级记忆目录并构造 CodingMemoryRail 实例作为输出缓存到 self._coding_memory_rail。

调用路径：`jiuwenswarm/server/runtime/agent_adapter/interface_code.py`（`JiuwenSwarmCodeAdapter._build_coding_memory_rail`） → `jiuwenswarm/server/runtime/agent_adapter/interface_code.py`（`create_coding_memory_rail`） → `jiuwenswarm/server/runtime/agent_adapter/interface_code.py`（`_resolve_coding_memory_dir`）

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1697–L1739](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1697-L1739), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L426–L465](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L426-L465), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L414–L423](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L414-L423), [jiuwenswarm/agents/harness/common/memory/config.py:L250–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L250-L281)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":1697,"end":1739,"sha256":"4cc2c248955828668816e9983adfe99310099a7ab085f030873cccb4a5d499d9"},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":426,"end":465,"sha256":"06e60fd38a034fac80542176cb8d5285ef67de7a049d586706c465fcb7c3924c"},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":414,"end":423,"sha256":"6280a49ac499a49a64afadbbd7bfc7c6e1e8eee0114cc376a62e257daf8a6f35"},{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":250,"end":281,"sha256":"d0cf034249e3b6c660c35aeb9beb5fe3ce2aed6efd9adab36b125f4a3a760e74"}],"trace":[{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","symbol":"JiuwenSwarmCodeAdapter._build_coding_memory_rail","start":1697,"end":1739},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","symbol":"create_coding_memory_rail","start":426,"end":465},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","symbol":"_resolve_coding_memory_dir","start":414,"end":423}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=coding-memory facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c487fb57e977b4e4932469e388e43f2b576e15facef25b1475bb3c64af49e091 -->
**开关与 Embedding 默认值**
is_memory_enabled 读取 modes.code.memory.enabled，code 及 code.* 子模式缺省为 True（agent 模式缺省 False）；create_coding_memory_rail 中 embed_model 缺省 "text-embedding-v3"，embed_base_url 依次取 embed 的 embed_base_url 或 embed_api_base，三者（含 embed_api_key）任一缺失即视为配置不完整并将 api_key 置 None 降级。

来源：[jiuwenswarm/agents/harness/common/memory/config.py:L250–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L250-L281), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L426–L465](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L426-L465)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":250,"end":281,"sha256":"d0cf034249e3b6c660c35aeb9beb5fe3ce2aed6efd9adab36b125f4a3a760e74"},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":426,"end":465,"sha256":"06e60fd38a034fac80542176cb8d5285ef67de7a049d586706c465fcb7c3924c"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=coding-memory facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f235fefc6b5b4184248e32a15c749b6b933d995d73f4304044c5ef99dd45dc39 -->
**后台初始化换取首请求延迟**
设计推断（非作者历史意图）：

（推断）把冷启动索引用后台 task 完成，收益是 before_invoke 不等待初始化、首个用户请求不被阻塞；代价是管理器就绪前的请求拿不到 _auto_recall 预取，且需用 asyncio.current_task 判断防止取消后的旧 task 覆盖新一轮 rail 状态。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L156–L198](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L156-L198)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":156,"end":198,"sha256":"11d2859093a154536a5646fb780d3ae3f12744aabe5932233ec5a67427443778"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=coding-memory facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83a47d9af15f352f67a59939abaf1cc23de8de7a6eaca60350f5393805bf7302 -->
**resolve_project_coding_memory_dir 目录解析与 get_node_path 双节点名返回契约**
resolve_project_coding_memory_dir(*, agent_workspace_dir, project_dir) 将 abspath(agent_workspace_dir)、"coding_memory" 与 resolve_coding_memory_project_name(project_dir) 拼接后返回；project_dir 为 None 或 strip 后为空时该名称取 DEFAULT_CODING_MEMORY_PROJECT。_CodingMemoryToolWorkspace.get_node_path 仅当 node_name 为 "memory" 或 "coding_memory" 时返回构造时传入的目录，否则返回 None。

来源：[jiuwenswarm/common/coding_memory_paths.py:L70–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/coding_memory_paths.py#L70-L80), [jiuwenswarm/common/coding_memory_paths.py:L43–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/coding_memory_paths.py#L43-L56), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L130–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L130-L136)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":80,"path":"jiuwenswarm/common/coding_memory_paths.py","sha256":"1dc5fbd8e59721d6fbe5b6b7f79536d4d39771def0d5280f85487bab91480779","start":70},{"end":56,"path":"jiuwenswarm/common/coding_memory_paths.py","sha256":"1b0a7457d73dc47e5f629c9a21ba19d75732181a155f664308f70252c649e378","start":43},{"end":136,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"6e0d1fcaeaa891e23941090024cdb3cc380b3e43ebbe1f0d4039b422f6aeb1a4","start":130}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=coding-memory facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dab8389d83e43b18d227f25aab68e8a5277ba1dff1fd427ce2a3fd50e447e996 -->
**interface_code.py 依赖共享 coding_memory_paths 并声明 _CodingMemoryToolWorkspace**
Code 适配器模块从 jiuwenswarm.common.coding_memory_paths 导入 resolve_project_coding_memory_dir，并在模块级声明 _CodingMemoryToolWorkspace；编码记忆路径解析由共享 common 模块定义，不是适配器私有实现。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L104–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L104-L119)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":119,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"a06fbb8afa139c11e673419d70f5dc609e13ce41c3a50032c0fbcad0c7e3b7dc","start":104}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=coding-memory facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d39bd3b8660f6684239a45c5585525894a827c04ca31418cf7caba78d12c2c6b -->
**get_node_path 对未知 node_name 返回 None，不抛异常**
触发条件：node_name 不在 {"memory", "coding_memory"} 集合内；守卫分支在本地直接 return None，调用方在此分支拿不到路径也不会收到异常。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L133–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L133-L136)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":136,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"e16f6b821effcb759f7cfbc65ff41f561de55b690074a458b58c574d1ca4e0f2","start":133}],"trace":[]} -->
<!-- /kb:depth -->
