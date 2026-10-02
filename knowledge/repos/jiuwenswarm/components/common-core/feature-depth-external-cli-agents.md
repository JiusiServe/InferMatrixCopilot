---
title: "外部 Claude 与 Codex CLI 智能体：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_runtime.py:L215-L239, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L24-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_runtime.py:L162-L212, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L118-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L26-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_runtime.py:L520-L588, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_runtime.py:L597-L608, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L67-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L75-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L20-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L140-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_external_cli_catalog.py:L35-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_external_cli_catalog.py:L13-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L30-L36, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_external_cli_catalog.py:L13-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_external_cli_catalog.py:L35-L51]
feature: "external-cli-agents"
entry_points: ["jiuwenswarm/common/external_cli_runtime.py", "jiuwenswarm/common/external_cli_catalog.py"]
source_globs: ["jiuwenswarm/common/external_cli_runtime.py", "jiuwenswarm/common/external_cli_catalog.py"]
---

# 外部 Claude 与 Codex CLI 智能体：实现深读

[功能概览](feature-external-cli-agents.md) · [owner 入口](_index.md)

<!-- kb:depth feature=external-cli-agents facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a2d1b35ba8281b375531ef33c12b5f6187928234ca0e8faa329f795ee4a82fd -->
**运行时目录与探测超时的取值**
external_cli_site_packages 在冻结 Windows 下解析为 sys.executable 同级的 runtime/external-cli/<cli_agent>/site-packages，在冻结 macOS 下为 ~/Library/Application Support/<DISPLAY_NAME>/runtime/external-cli/<cli_agent>/site-packages（用户目录以占位符表示）；非冻结环境抛 RuntimeError。模型目录刷新的探测超时默认 DEFAULT_PROBE_TIMEOUT_S = 15.0 秒。

来源：[jiuwenswarm/common/external_cli_runtime.py:L215–L239](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L215-L239), [jiuwenswarm/common/external_cli_catalog.py:L24–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L24-L27)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/external_cli_runtime.py","start":215,"end":239,"sha256":"0d43a5b773460a56c4eb85a162cbe1cdd9dab6e5b6e7002353da61ab46b5bbbc"},{"path":"jiuwenswarm/common/external_cli_catalog.py","start":24,"end":27,"sha256":"276e99eb8c6dd94f84fe7406fea2f43bedb725979bdcc023ee297000e8238914"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=external-cli-agents facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b309b83fa5be2cee5934315ba32c560bdee797c329e4c74140c67d21776d2c4a -->
**get_external_cli_runtime_status 按平台 artifacts 与安装元数据逐级判定 runtime_state**
校验 cli_agent 后从 manifest 取当前平台 artifacts，为空即 raise RuntimeError；site-packages 目录不存在或为空返回 runtime_state="not_installed"；安装元数据 JSON 损坏或非 dict 记 "invalid"，与期望 {agent, platform, packages} 不一致记 "update_required"，必需文件齐全才记 "current"。

来源：[jiuwenswarm/common/external_cli_runtime.py:L162–L212](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L162-L212)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":212,"path":"jiuwenswarm/common/external_cli_runtime.py","sha256":"a62382825850f2bb0dcd90e7f14042fc6cb9b08851e59047db9d3e25cf1a283a","start":162}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=external-cli-agents facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8004b89689d7a3d67b7118f498b15f866a19b101c60018cecc680ae4b41643fa -->
**refresh_external_cli_builtin_models(timeout_s) 契约：逐 CLI 探测期限，返回漂移警告**
入参 timeout_s（默认 DEFAULT_PROBE_TIMEOUT_S=15.0）是每个 CLI 的探测期限；返回漂移警告列表，目录全部匹配时为空。只探测声明了目录的 CLI，探测失败（未登录、无法启动、超时）时该 CLI 的目录保持不动。

来源：[jiuwenswarm/common/external_cli_catalog.py:L118–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L118-L130), [jiuwenswarm/common/external_cli_catalog.py:L26–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L26-L27)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":130,"path":"jiuwenswarm/common/external_cli_catalog.py","sha256":"4401bc8113d61cf4f0222e822920bf57670ab311927e9bf13a6f4f068eb50de2","start":118},{"end":27,"path":"jiuwenswarm/common/external_cli_catalog.py","sha256":"0a4bdc973f88c00dfa6eb8f25a543ae58932b24c27762315071eb76c770228ec","start":26}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=external-cli-agents facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb45c87134036bc7cdff59d40a3391cd042960f7a90899d481eb100ad04766ee -->
**探测按 cli_agent 分支延迟导入 openjiuwen harness provider；目录刷新依赖 config 声明，无任何声明时不发起探测**
_probe_models 以 cli_agent == "claude" 为界在函数内导入 openjiuwen.harness_providers.claudecode 或 openjiuwen.harness_providers.codex，分别以 cli_path or None 构造 ClaudeCodeHarness / CodexHarness（codex_bin），两支都 await harness.list_models() 并映射为 {option.model_id: list(option.efforts)}，导入延迟到探测时发生。目录刷新侧从 jiuwenswarm.common.config 导入 get_config 与 update_external_cli_builtin_models_in_config；遍历条目时跳过无 cli_agent 或 builtin_models 非非空列表者，收集后 declared_by_agent 为空则在调用 _run_probes(paths, timeout_s) 之前局部 return []。

来源：[jiuwenswarm/common/external_cli_catalog.py:L75–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L75-L86), [jiuwenswarm/common/external_cli_catalog.py:L20–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L20-L20), [jiuwenswarm/common/external_cli_catalog.py:L140–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L140-L151)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":86,"path":"jiuwenswarm/common/external_cli_catalog.py","sha256":"20b45ada6a4d17c605bff30d38e04d7615d6cb8b70e7130ded38849342cbca4b","start":75},{"end":20,"path":"jiuwenswarm/common/external_cli_catalog.py","sha256":"8a94adaa79d8d54968533b1b3d4e4d379f04eaefa8c4fbda5d08bce00fa48f23","start":20},{"end":151,"path":"jiuwenswarm/common/external_cli_catalog.py","sha256":"8cc4d3f99407e0d02ae9fdb5f2f3c3da1d3b75772450138ca33354779fd14ecb","start":140}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=external-cli-agents facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=42d9dae66f46f2af617d61944f345b7721cad82184a6407aa13a433d4bf45786 -->
**提权安装器（仅 frozen Windows）启动失败按 GetLastError 分流传播**
非 frozen Windows 入口即 raise；ShellExecuteExW 失败按 GetLastError 分流：1223（ERROR_CANCELLED）→RuntimeError("administrator permission was cancelled")，其余→OSError("failed to start elevated external CLI installer")；安装器退出码非 0 再 RuntimeError 附码，finally 中 CloseHandle。

来源：[jiuwenswarm/common/external_cli_runtime.py:L520–L588](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L520-L588), [jiuwenswarm/common/external_cli_runtime.py:L597–L608](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L597-L608)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":588,"path":"jiuwenswarm/common/external_cli_runtime.py","sha256":"3214879f7ebc456214d3b6ec22f81f0952f6113c0eb9fc10c429c3f7a25250a5","start":520},{"end":608,"path":"jiuwenswarm/common/external_cli_runtime.py","sha256":"f0fa2dc92d6f1e601384bfe775612c8c15ba3936cf29107d09ae9569a6dc4797","start":597}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=external-cli-agents facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=529b160847a084a647a433407dc50067e034e7aa90ac405ca8676487ecfcb4c1 -->
**CLI 新增模型只警告不自动入目录：成本决策留给运维，但需手工补配置**
设计推断（非作者历史意图）：

收益（推断）：注释明言加模型是成本决策，CLI 新报出且未声明的模型只汇成警告而不改写目录，运维保持控制；代价（推断）：警告文本写明必须手工 "add them to builtin_models" 这些模型才可用。

来源：[jiuwenswarm/common/external_cli_catalog.py:L67–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L67-L71)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":71,"path":"jiuwenswarm/common/external_cli_catalog.py","sha256":"0d60fba21c0b682afcf47b0acc957916902de243bed12e55c7075afcd4ffc4bc","start":67}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=external-cli-agents facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d91063efc8eff19b50b5a3ce6e371e0272596609c57bcfba66d33013607fc552 -->
**直接单测仅覆盖 reconcile_builtin_models 纯 helper（未涉及原生 CLI 集成）**
test_reconcile_drops_unknown_models_and_fixes_efforts 直接调用 reconcile_builtin_models("claude", declared, reported)，断言 corrected 仅保留 sonnet 与 haiku、sonnet 的 efforts 修正为上报的 low/medium/high 并保留 daily 描述与仍有效的 high default_effort、haiku 不含 efforts 字段，且 warnings 提及 removed 'fable-5' 与 also offers opus。断言仅及该 helper 的返回值，所示片段未执行原生 CLI、认证、刷新或持久化；本轮亦未运行该测试。

来源：[tests/unit_tests/common/test_external_cli_catalog.py:L13–L16](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/common/test_external_cli_catalog.py#L13-L16), [tests/unit_tests/common/test_external_cli_catalog.py:L35–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/common/test_external_cli_catalog.py#L35-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":16,"path":"tests/unit_tests/common/test_external_cli_catalog.py","sha256":"2cc93f6373bde3d8abb7367c0d188058503caaa951c041888143cff9dd895228","start":13},{"end":51,"path":"tests/unit_tests/common/test_external_cli_catalog.py","sha256":"ca890b3fbacd8371367a866b97cfeaf4050c679184b75ecb380664c5b183eaef","start":35}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
