---
title: "生命周期 Hooks 与扩展：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L90-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L89-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L4-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L58-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L111-L118, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L58-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L120-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L10-L11, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L31-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L36-L45, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L48-L54]
feature: "hooks"
entry_points: ["jiuwenswarm/extensions/manager.py"]
source_globs: ["jiuwenswarm/extensions/manager.py", "jiuwenswarm/extensions/*.py"]
---

# 生命周期 Hooks 与扩展：实现深读

[功能概览](feature-hooks.md) · [owner 入口](_index.md)

<!-- kb:depth feature=hooks facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f0254f060009147374512b98dbe60b3a8f9e65bdf5a6a262b071b1baebf31cb -->
**transport 扩展按 manifest 标志整体跳过**
设计推断（非作者历史意图）：

Runtime 直连（include_transport_extensions=False）时依据 manifest 的 requires_transport is True 直接跳过整个扩展包并记 info 日志，而不是逐能力选择性挂载。推断：收益是加载路径简单、避免无传输层的宿主挂载不可用扩展；代价是同包内不依赖 transport 的能力也一并丢失，且该过滤完全信任 manifest 声明。

来源：[jiuwenswarm/extensions/manager.py:L90–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L90-L100)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/extensions/manager.py","start":90,"end":100,"sha256":"29ecdb708aaa4663754417b9db05a2c16ec0303367f87ac01dace1d547c23b5f"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=hooks facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=10164c78dc93cc1226b1399f4ef62ed50d89fc30ef156d3ea8140b61769af54e -->
**单根路径加载失败的隔离**
load_all_extensions 对每个扩展根路径各自 try/except：当 load_manifest 或 load_extension 抛出任意 Exception 时，108-109 行捕获并 logger.error 记录路径与异常，for 循环继续处理下一个 root，异常不向外重抛。该分支只证明单个失败根路径被跳过且循环继续推进，不构成对其余扩展必然加载成功的保证。

来源：[jiuwenswarm/extensions/manager.py:L89–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L89-L109)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/extensions/manager.py","sha256":"0a2cb91d16a87efa1e1f199f995898cdeac50188604baa608f89bf36394feb54","start":89}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=hooks facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de90095d5297aa5fb2507aee5bcbf89af801c69ece5dc8cb63ce42d304cf0ae0 -->
**shutdown_all_extensions：hasattr 探测 shutdown 并 await，except Exception 记 warning 继续，循环后清空**
遍历 _loaded_extensions，仅对 hasattr(ext, "shutdown") 为真的条目 await ext.shutdown()；单项抛出的 Exception 被捕获记录 warning 后继续下一项；for 循环结束后执行 _loaded_extensions.clear()。

来源：[jiuwenswarm/extensions/manager.py:L111–L118](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L111-L118)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":118,"path":"jiuwenswarm/extensions/manager.py","sha256":"4fddadf4ad1bfedf5542e70a80e6d5b20b2bc74ce7de703546f28833484f696a","start":111}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=hooks facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=993c7e15b35a55fe3aa4b4c9c81e825db910acd9a5250cd82e7325f7bfd9d19b -->
**ExtensionManager.__init__ 需注入 ExtensionRegistry；list_extensions 仅列带 metadata 条目**
构造签名 __init__(self, registry: ExtensionRegistry)：调用方须传入 registry，内部自建 ExtensionLoader(registry) 与空 _loaded_extensions，并调用 _setup_search_paths()；list_extensions() 只返回带 metadata 条目的 id/name/version 字典。

来源：[jiuwenswarm/extensions/manager.py:L58–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L58-L65), [jiuwenswarm/extensions/manager.py:L120–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L120-L125)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":65,"path":"jiuwenswarm/extensions/manager.py","sha256":"d00e38cb64a00446faabd3a4ca58f7165da2d6d6a9fffc2d9d7762c055449965","start":58},{"end":125,"path":"jiuwenswarm/extensions/manager.py","sha256":"9b3988c390cccf115163de254f252561a969499dc2ac83bbb46182e5df9da330","start":120}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=hooks facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0597373cb7a674722d690f710f95d5a41e34384f3518e09398b20484c55a84e -->
**extensions.extension_dirs 仅认 ';' 分割字符串，追加默认 jiuwenswarm/extensions 后按小写段去重**
_extension_dir_paths_from_config 仅当 extensions.extension_dirs 为字符串时按 ';' 拆分并去空白段，随后追加 _DEFAULT_EXTENSION_DIR（"jiuwenswarm/extensions"）；_dedupe_extension_dirs 按小写路径段去重且保留首次出现，配置路径因此排在默认路径之前。

来源：[jiuwenswarm/extensions/manager.py:L10–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L10-L11), [jiuwenswarm/extensions/manager.py:L31–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L31-L33), [jiuwenswarm/extensions/manager.py:L36–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L36-L45), [jiuwenswarm/extensions/manager.py:L48–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L48-L54)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":11,"path":"jiuwenswarm/extensions/manager.py","sha256":"bde4c7c172d58fa2a05f4296f0cf10581ccaf0f7605f642aa591fe2cbdb74e6b","start":10},{"end":33,"path":"jiuwenswarm/extensions/manager.py","sha256":"2784c6e823a88fdb9c6290f53f000b6a6920549af0cbaf4ec42f4478e436bf91","start":31},{"end":45,"path":"jiuwenswarm/extensions/manager.py","sha256":"d46a34d08644b00e3d43029f379332ca4adf2249bf7fadb7090575ce4684a798","start":36},{"end":54,"path":"jiuwenswarm/extensions/manager.py","sha256":"2ab0e4af9cf0be2647ef4042e4d34c0e3175812573f84ecb2430a2be1b0a5594","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=hooks facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=788d2e2797cad2f7e893a3fbcb0c68107ca89a15ab4caba0b0b705137e9cb2d4 -->
**调用方注入 ExtensionRegistry，自建 ExtensionLoader 并依赖 common.config/common.utils**
ExtensionManager 接收调用方注入的 ExtensionRegistry，__init__ 内自建 ExtensionLoader(registry) 并持有空 _loaded_extensions；模块导入 jiuwenswarm.common.config.get_config 以及 jiuwenswarm.common.utils 的 get_root_dir 与 logger。

来源：[jiuwenswarm/extensions/manager.py:L4–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L4-L7), [jiuwenswarm/extensions/manager.py:L58–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L58-L64)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":7,"path":"jiuwenswarm/extensions/manager.py","sha256":"2b06f824c513651b2688577e749ee95542cdab6a11f5a5f06001713a8839107d","start":4},{"end":64,"path":"jiuwenswarm/extensions/manager.py","sha256":"db2511ae33c43ebc9af97faa9885ce9cb54f4eb72f15bdfae4b385270a6db1aa","start":58}],"trace":[]} -->
<!-- /kb:depth -->
