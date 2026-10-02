---
title: "浏览器服务与网页工具：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/browser_runtime.py:L26-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/browser_config.py:L12-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L62-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/browser_config.py:L19-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L416-L433, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/浏览器.md:L99-L119", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/playwright_mcp_runtime.py:L333-L381]
---

# 浏览器服务与网页工具：实现深读

[功能概览](feature-browser-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=browser-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b79bfd8df4186124f7480697795f51b790b202d400a0336ef444f5bd9f1d7941 -->
**Swarm 托管 Chrome 设置解析调用链**
apply_swarm_browser_settings 接收 RuntimeSettings、config 与 session_id，先调用 resolve_chrome_path 从 config.browser 提取 Chrome 路径；resolve_chrome_path 内部调用 resolve_env_vars 展开配置中的 ${VAR:-default} 占位符后读取 chrome_path。若路径为空或未选中 Electron 浏览器，则走 apply_session_sideview_target 分支；否则继续构造 managed 实例并返回替换了 instance 与 mcp_cfg 的新 RuntimeSettings。

调用路径：`jiuwenswarm/agents/swarm/browser_runtime.py`（`apply_swarm_browser_settings`） → `jiuwenswarm/agents/harness/common/browser_config.py`（`resolve_chrome_path`） → `jiuwenswarm/common/config.py`（`resolve_env_vars`）

来源：[jiuwenswarm/agents/swarm/browser_runtime.py:L26–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/browser_runtime.py#L26-L57), [jiuwenswarm/agents/harness/common/browser_config.py:L12–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/browser_config.py#L12-L32), [jiuwenswarm/common/config.py:L62–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L62-L99)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/browser_runtime.py","start":26,"end":57,"sha256":"ae7ec0f8e91240ce6e8426f42b36147da8dcd5a59cdfd94340d44c291cf442f2"},{"path":"jiuwenswarm/agents/harness/common/browser_config.py","start":12,"end":32,"sha256":"e6f5dbdc9edb43d911f002bac2b66c380cbe9d06e5394c7def24e10a6a6da1f3"},{"path":"jiuwenswarm/common/config.py","start":62,"end":99,"sha256":"9b0ac4984a7e1bed5c688f21385f2783d3019f9c7285ecc50fa4b8fede4eb67b"}],"trace":[{"path":"jiuwenswarm/agents/swarm/browser_runtime.py","symbol":"apply_swarm_browser_settings","start":39,"end":43},{"path":"jiuwenswarm/agents/harness/common/browser_config.py","symbol":"resolve_chrome_path","start":19,"end":21},{"path":"jiuwenswarm/common/config.py","symbol":"resolve_env_vars","start":71,"end":99}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=13d982ab81db6815828459eea3fc500075f7e4f76f7c992f75b13ce5463b6e66 -->
**chrome_path 形态与工作区目录优先级**
browser.chrome_path 可为字符串或按平台映射的 dict：先取 sys.platform 对应键（win32/cygwin→windows、darwin→macos、linux/linux2→linux），未命中再取 "default" 键，均无则返回 ""（文档默认值为空、留空走自动检测）。托管实例的 user_data_dir 派生自 get_user_workspace_dir()：优先缓存的已设值，其次 JIUWENSWARM_DATA_DIR 环境变量，最后 <用户主目录>/.jiuwenswarm。

来源：[jiuwenswarm/agents/harness/common/browser_config.py:L19–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/browser_config.py#L19-L32), [jiuwenswarm/common/utils.py:L416–L433](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L416-L433), [docs/zh/浏览器.md:L99–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%B5%8F%E8%A7%88%E5%99%A8.md#L99-L119)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/browser_config.py","start":19,"end":32,"sha256":"3a37b279491d3ba795b10b744a554f9e29c460f2bbf7ce614c47665d8bae93cf"},{"path":"jiuwenswarm/common/utils.py","start":416,"end":433,"sha256":"3f14f83a313739a80f61a61ecaf853a29e1b2f7c15c0daf69a032a387e6b0f73"},{"path":"docs/zh/浏览器.md","start":99,"end":119,"sha256":"c81232373cc263bd2974c9fd0a934902951b50fc391311418245b63b677db137"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=580c907a6b14cc0f361d60d254b015cb816e477acd4332fb1592bee7cf8a22e5 -->
**内置运行时不可用的降级行为**
materialize_bundled_runtime 抛出任意异常时，resolve_playwright_mcp_launch 捕获并 logger.warning 提示降级，返回 source="pinned-npx-fallback" 的 PlaywrightMcpLaunch（固定 npx 命令与参数），该路径可能访问 npm 注册表；不向调用方传播异常。此外检测到旧版 .env 模板默认值时仅告警忽略，继续走内置运行时。

来源：[jiuwenswarm/common/playwright_mcp_runtime.py:L333–L381](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/playwright_mcp_runtime.py#L333-L381)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/playwright_mcp_runtime.py","start":333,"end":381,"sha256":"32defc7bf80438f9ba094df3e0ddc4a468d918700bba0878cc45b0a22994691f"}],"trace":[]} -->
<!-- /kb:depth -->
