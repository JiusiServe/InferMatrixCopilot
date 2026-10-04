---
title: "Harness Package 与热激活：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L221-L263, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L169-L178, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L38-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L157-L166, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L86-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L321-L331, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L99-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L38-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L104-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/materializer.py:L27-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/rsi/test_plugin_catalog.py:L103-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L338-L344, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L324-L331]
feature: "rsi-packages"
entry_points: ["jiuwenswarm/agents/harness/common/rsi/harness_activation.py"]
source_globs: ["jiuwenswarm/agents/harness/common/rsi/harness_activation.py", "jiuwenswarm/agents/harness/common/rsi/*"]
---

# Harness Package 与热激活：实现深读

[功能概览](feature-rsi-packages.md) · [owner 入口](_index.md)

<!-- kb:depth feature=rsi-packages facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1592d6bb1d1f9bcfdbaf9b556951b936f344e0db60710fb6e58e9fc20038c93c -->
**发布 refs 解析链路**
parse_published_harness_refs 以引擎产出的最终 refs 文件与 task_run_root 为输入：先把 refs 与 run 根目录解析为绝对路径并用 _ensure_inside 约束边界，随后调用 _load_refs。_load_refs 读取 YAML（OSError/UnicodeError/YAMLError 均归一为 _invalid 错误）并要求结果是 mapping，最终供上层校验 harness_refs 唯一 role 并返回 PublishedHarnessRef。

调用路径：`jiuwenswarm/agents/harness/common/rsi/harness_activation.py`（`parse_published_harness_refs`） → `jiuwenswarm/agents/harness/common/rsi/harness_activation.py`（`_load_refs`）

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L221–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L221-L263), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L169–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L169-L178)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":221,"end":263,"sha256":"f4e28160649b0b80d1037dc885a43ac4a9b996be15ed0aa52793ab8cdc8d214c"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":169,"end":178,"sha256":"a1ade19510f2a2536b7eb468b30f0008842bbb76dd94770f65ee1fa134659b62"}],"trace":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","symbol":"parse_published_harness_refs","start":221,"end":263},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","symbol":"_load_refs","start":169,"end":178}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f3398adc2140dc0476ea1dfed89cfdb6c3da5fa3f3a5e454b25ee1378c699ff -->
**manifest 名称与原生基线配置**
包 manifest 按 _MANIFEST_NAMES = ("manifest.json", "harness_config.yaml", "expert_harness.yaml", "harness.yaml") 查找；无插件时的基线是模块同目录的 harness_config.yaml（_NATIVE_HARNESS_BASELINE_CONFIG）。resolve_native_harness_baseline 在该文件不存在或其目录未通过 _validate_engine_manifest（抛 RsiHarnessInvalid）时返回 None，否则返回其 resolve 后的绝对路径。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L38–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L38-L40), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L157–L166](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L157-L166)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":38,"end":40,"sha256":"eac74cb141235ecab5ee055a42d43675b3f3e64da6af97418cc7de61902c997e"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":157,"end":166,"sha256":"7a5351d27ed1738fb99890e55296b4c11a90354bb335718cc53a0119fa42c2ce"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3d105cb72f9932d60400397b6bc74e69d4095a9d2815776b98dabd7c6e10168c -->
**具体失败触发与传播**
refs 文件缺失/不可读/非 mapping 时 _load_refs 抛 _invalid（RsiHarnessInvalid 类错误）；包内符号链接解析到包外时 _ensure_package_tree_inside 以 "Harness 包含越界软链接" 拒绝；RsiHarnessActivationStore._validate_runtime_path 对不在 activation root 内的 runtime_path 抛 ValueError，require_exists 且目录不存在时返回 None 而非报错。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L169–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L169-L178), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L86–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L86-L96), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L321–L331](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L321-L331)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":169,"end":178,"sha256":"a1ade19510f2a2536b7eb468b30f0008842bbb76dd94770f65ee1fa134659b62"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":86,"end":96,"sha256":"b56c221cf2b03da4bf42ad96b74329bf8bfa244d2d653bdc2c764c672cbe4e69"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":321,"end":331,"sha256":"9b12f2dad693138a4dd3b0a68a46546c18c5bec5242aede99ad732bab3f1fdba"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1997809fe0cbf574766e8569add8fee91907aa3701ad2cbe219df83994c634e0 -->
**RsiHarnessActivationStore.get_active：active 为 dict 且 runtime_path 通过 require_exists=True 校验才返回 dict(active)，否则 None**
get_active() 无参数：读取文档 active 字段，非 dict 返回 None；runtime_path 经 _validate_runtime_path(require_exists=True) 返回 None（如目录不存在）时也返回 None，校验通过则返回 dict(active)。runtime_path 解析后不在 self.root 内时抛 ValueError「RSI Harness runtime_path 不在 activation root 内」。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L338–L344](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L338-L344), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L324–L331](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L324-L331)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":344,"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","sha256":"5cac07f88e8d43207fcd36f4ddc5fa9670309339a68eabf10365184f4dafcbfd","start":338},{"end":331,"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","sha256":"222dc08e0ce39405ae902864d45532e5a9fb8d6e7bf9c46990478d9027c68f47","start":324}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=788a47472876aab5751fefeb0b9ab6ed307f0f02d59d656c2fa2864cd5f824c6 -->
**清单发现依赖 openjiuwen SDK，ImportError 时回退本地 _MANIFEST_NAMES 匹配**
`_find_manifest` 优先 `from openjiuwen.harness.resources import find_plugin_manifest` 并 `resolve(strict=True)`；`ImportError` 时置 `None` 回退，按 `_MANIFEST_NAMES` 顺序 `is_file()` 匹配（注释声明 manifest.json 优先于 legacy YAML），全部缺失抛 `_invalid("Harness 包缺少配置文件")`。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L99–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L99-L115)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":115,"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","sha256":"be46918f06f4f7e3a1b3a113a7fb9172e0a23dd465d63bb426ffeaaf8b35f4b8","start":99}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e119b0dd75561ec7ca958936009f312d855f55d5e7a4dfe9a0ab8fb7380b47e6 -->
**SDK 优先加本地回退换取旧 SDK 兼容，代价是清单名元组重复定义（推断）**
设计推断（非作者历史意图）：

收益：无公开 loader 的旧 SDK 仍可按文件名发现清单（回退分支注释标明兼容旧 SDK）；代价：清单文件名列表在 harness_activation 的 `_MANIFEST_NAMES` 与 materializer 的同名元组各定义一份，两处需人工保持同步。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L38–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L38-L38), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L104–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L104-L115), [jiuwenswarm/agents/harness/common/rsi/materializer.py:L27–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/materializer.py#L27-L28)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","sha256":"6a10d82a54d61c732f0aae33424048209ba2ee6c884ef078863701525dcce14a","start":38},{"end":115,"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","sha256":"5cb0f779874f5d6880e6489a08b7ffb5386bc8eaaa9784ad7055fb8d02d0bafc","start":104},{"end":28,"path":"jiuwenswarm/agents/harness/common/rsi/materializer.py","sha256":"5ee36a2bb446f87d8bdebfb59b56698d78ac18a3edaf69cde53464e605663cd4","start":27}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=85f1b69c71bc0a784fd8f24035380eba5dc2b004a93ea90e288ce6c9058341c4 -->
**test_registration_undo_preserves_preexisting_import：断言 undo() 后插件许可被撤销而插件目录保留**
该 pytest 用例注册 `rsi-harness-aabbcc`、upsert installed=False 后再次注册取 undo，断言撤销前 is_plugin_allowed(package_id) 为 True、undo() 后为 False，且 resolve_plugin_dir(package_id).is_dir() 仍为 True。

来源：[tests/unit_tests/rsi/test_plugin_catalog.py:L103–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/rsi/test_plugin_catalog.py#L103-L112)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":112,"path":"tests/unit_tests/rsi/test_plugin_catalog.py","sha256":"dfc1700f128a36571d1388997ad684044c79ea7ef149de509414149b4fae3ad8","start":103}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
