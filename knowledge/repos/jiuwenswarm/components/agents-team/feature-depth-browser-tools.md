---
title: "浏览器服务与网页工具：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/browser_runtime.py:L26-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/browser_config.py:L12-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L62-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/browser_config.py:L19-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L416-L433, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/浏览器.md:L99-L119", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/playwright_mcp_runtime.py:L333-L381, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/browser_runtime.py:L26-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/browser_runtime.py:L17-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/browser_runtime.py:L39-L43, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/electron_sideview.py:L214-L239, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/browser_runtime.py:L47-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_electron_browser_fallback.py:L19-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_electron_browser_fallback.py:L67-L79]
feature: "browser-tools"
entry_points: ["jiuwenswarm/agents/swarm/browser_runtime.py", "jiuwenswarm/agents/harness/common/browser_config.py"]
source_globs: ["jiuwenswarm/agents/swarm/browser_runtime.py", "jiuwenswarm/agents/harness/common/browser_config.py", "jiuwenswarm/agents/harness/common/*"]
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

<!-- kb:depth feature=browser-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a305a55496c9f7edcc0a6c2b0b746640944991d0a55b0d2c21ef59d49b86a626 -->
**apply_swarm_browser_settings(settings, config, session_id, *, member_id='')：守卫分支返回 sideview 调用结果，越过守卫返回替换 instance/mcp_cfg 的新 settings**
member_id 为仅关键字参数、默认空串。守卫 not chrome_path or not electron_browser_selected() 成立时返回 apply_session_sideview_target(settings, session_id, member_id=member_id, label=member_id)；越过守卫则第77行返回 replace(settings, instance=instance, mcp_cfg=mcp_cfg)。

来源：[jiuwenswarm/agents/swarm/browser_runtime.py:L26–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/browser_runtime.py#L26-L77)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":77,"path":"jiuwenswarm/agents/swarm/browser_runtime.py","sha256":"3aa0b38e68d70f8388acb02199b7c5d8a4c5a03266f78c71191c9d640ed89f73","start":26}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8acb78555b3036a95ebb8fc48a4b0053519d61cc3fd5b7414f3244bbc7f98be0 -->
**守卫分支委托导入的 electron_sideview 助手；resolve_chrome_path 的空串结果也会触发该守卫**
守卫 not chrome_path or not electron_browser_selected() 时转入 apply_session_sideview_target：该助手在 resolver 为空或 session_id 去空白后为空时原样返回 settings，否则写 PLAYWRIGHT_MCP_* env 并置 server_id=playwright_electron_<sha256([session_id, member_id])>；config/browser 非字典时 resolve_chrome_path 返回空串即可触发守卫。

来源：[jiuwenswarm/agents/swarm/browser_runtime.py:L17–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/browser_runtime.py#L17-L22), [jiuwenswarm/agents/swarm/browser_runtime.py:L39–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/browser_runtime.py#L39-L43), [jiuwenswarm/agents/harness/common/electron_sideview.py:L214–L239](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/electron_sideview.py#L214-L239), [jiuwenswarm/agents/harness/common/browser_config.py:L12–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/browser_config.py#L12-L32)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/agents/swarm/browser_runtime.py","sha256":"60114e49baf09e17bf524abd58f702c64e8433cb06df7c836838f919e58f1167","start":17},{"end":43,"path":"jiuwenswarm/agents/swarm/browser_runtime.py","sha256":"096d9d9d8921b1e78bda464c96f2a130eb86879ea1885dbcddc8b39042208c53","start":39},{"end":239,"path":"jiuwenswarm/agents/harness/common/electron_sideview.py","sha256":"5c9465430f4b5d639e4efc188c464f51174c94ded469ce41397ef0c8147c59fb","start":214},{"end":32,"path":"jiuwenswarm/agents/harness/common/browser_config.py","sha256":"e6f5dbdc9edb43d911f002bac2b66c380cbe9d06e5394c7def24e10a6a6da1f3","start":12}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2212536c9e551732c9d0e1575c7799ad132fe5516e282067b2669743f9815bb4 -->
**仅托管分支按 stripped 身份哈希分配 profile：隔离收益与不可共享代价（均为推断）**
设计推断（非作者历史意图）：

托管分支的 user_data_dir=workspace/.browser-profiles/<key>，key='swarm_'+sha256([session_id.strip(), member_id.strip()])。收益（推断）：不同身份的浏览器状态互相隔离；代价（推断）：不同身份无法共享同一 profile。

来源：[jiuwenswarm/agents/swarm/browser_runtime.py:L47–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/browser_runtime.py#L47-L57)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":57,"path":"jiuwenswarm/agents/swarm/browser_runtime.py","sha256":"bb0c0fe0f5aafd8f8083ecc6a48221a382a5b4097d7e56326dd342970ff7771e","start":47}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=144ff45859ae87b332068e3c48dfd55a00e8c7d1d56ba9bbec3468cc7ae6e9ea -->
**browser_config.resolve_chrome_path 平台选择与默认回退的 helper 单测**
test_platform_path_resolution_matches_browser_settings 将 browser_config.sys.platform 逐参 mock 为 win32/cygwin/darwin/linux，断言 resolve_chrome_path 对平台键 " /chrome " 去空白后返回 /chrome、平台路径空白时回退 default="/other"；相邻参数化用例 test_missing_or_invalid_configuration_does_not_select_external 断言 None、{}、browser 为 None、chrome_path=3 均返回 ""。断言仅覆盖该配置 helper，本轮未执行，不验证浏览器启动、远程连接或网页操作。

来源：[tests/agents/swarm/test_electron_browser_fallback.py:L19–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_electron_browser_fallback.py#L19-L19), [tests/agents/swarm/test_electron_browser_fallback.py:L67–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_electron_browser_fallback.py#L67-L79)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"tests/agents/swarm/test_electron_browser_fallback.py","sha256":"291f916d1d25be80d0cb7700adbb2b68e4a00e71ffc70aafaf85bf328514b067","start":19},{"end":79,"path":"tests/agents/swarm/test_electron_browser_fallback.py","sha256":"69f6b112bb0b5c72e611a3ef07502251aad5d2dc0f036e98f138fe55211cd6eb","start":67}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
