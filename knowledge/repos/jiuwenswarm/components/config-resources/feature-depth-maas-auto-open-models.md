---
title: "华为云 MaaS 预置服务批量开通自动化（CDP）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L770-L812, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L772-L810, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L523-L548, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py:L9-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L808-L812, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md:L373-L396]
feature: "maas-auto-open-models"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py"]
---

# 华为云 MaaS 预置服务批量开通自动化（CDP）：实现深读

[功能概览](feature-maas-auto-open-models.md) · [owner 入口](_index.md)

<!-- kb:depth feature=maas-auto-open-models facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=75fb756ce05c8bf6332ed4e409a9d8217326efef254c8d829e376c73ad30c9c0 -->
**main 解析参数后调用 auto_open_models 并按 result.ok 返回 0/1**
main 先解析 argv，cdp_url 为空时回退 resolve_cdp_url()；--model 优先，否则从 --models-file 读取展示名，然后调用 auto_open_models(cdp_url, models, type_filter, timeout_s)，output_json 输出结果并返回 0 if result.get("ok") else 1（此返回值是 main 的局部返回，非直接证明进程退出码）。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L770–L812](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py#L770-L812)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":812,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py","sha256":"35cfc5f9d535e4e9309a359f889f6f5f9967052aa4f152723bba7e13f503218e","start":770}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=maas-auto-open-models facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a04b41f123312716240a7b07b2349e1cbc192b0f6544401b3d3c25976426500c -->
**main(argv) 的 CLI 契约：可重复 --model、--models-file、--type-filter、--timeout、--json**
调用方通过 argv 传入 --cdp-url（默认空字符串）、可多次指定的 --model（优先于 --models-file）、--models-file（默认 _DEFAULT_MODELS_FILE）、--type-filter（默认 "文本生成"）、--timeout（int，默认 90 秒）与 --json 开关；返回 int，成功路径取决于 result.get("ok")。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L770–L812](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py#L770-L812)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":812,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py","sha256":"35cfc5f9d535e4e9309a359f889f6f5f9967052aa4f152723bba7e13f503218e","start":770}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=maas-auto-open-models facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59cb9640d74932ee36923e3d01f73c514060d34998ac65e40d3f87fe9af33d5f -->
**模型来源优先级：--model（可重复）优先，其次 --models-file；cdp-url 空则回退 resolve_cdp_url()**
args.model 非空时逐个 strip 作为模型列表；否则从 args.models_file 加载展示名。cdp_url 取 args.cdp_url 去空白，为空时调用 resolve_cdp_url()。--type-filter 默认 "文本生成"（按预置服务列表“类型”列过滤），--timeout 默认 90。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L772–L810](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py#L772-L810)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":810,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py","sha256":"a3213365cd78c7c2802fa8430c98e53258f1f21a2bbc666182c62fa137fdbf76","start":772}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=maas-auto-open-models facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c417277632f43ed67f7baf8d013b292d90a391373972c69c92bbcd48469874c1 -->
**连接/导航/表格加载失败时返回 make_failure 统一 JSON（ok=false, stage, error），由 main 以本地返回码 1 输出**
connect_page 抛异常返回 make_failure("connect_failed")；goto 抛异常或 _wait_table_ready 为假分别返回 stage=navigate_failed 与 stage=table_timeout（提示可能未登录）。make_failure 构造 {"ok": False, "stage": …, "error": …, **extra}；main 输出 JSON 并按 result.get("ok") 本地 return 0/1，不证明进程退出码语义之外的行为。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L523–L548](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py#L523-L548), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py:L9–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py#L9-L17), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py:L808–L812](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py#L808-L812)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":548,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py","sha256":"e344cff9d46e494a6b2e5365860a5c44ef2beb1a4e6c62821f904639c316e974","start":523},{"end":17,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py","sha256":"05311fcb94baefb213deae5de4cf0446fddbd90d66d2c21d6ece0b016cd93c8f","start":9},{"end":812,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py","sha256":"c911ceb009478fb9edceabc5dfdcfd09d67ce6b3382cd5c379704a08175b6f56","start":808}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=maas-auto-open-models facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5af87e9bcebd3c02ef3ca204b29a2e128d368d0a259d463598adc589248a2ba1 -->
**SKILL.md 步骤 5 给出的 documented_manual 验证流程（未执行）**
文档中的人工验收步骤（本轮未执行）：

既有文档化手工流程：依次运行 navigate.py 跳转 deployment 页与 `auto_open_model.py --json --cdp-url <CDP_URL> --models-file <skill_dir>/models.json --timeout 90`，期望 stdout 返回 ok=true、stage=open_models 且 opened/already_opened/failed 分列。此为文档记载的操作与预期结果，本轮未执行，不构成运行时证据。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md:L373–L396](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md#L373-L396)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":396,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md","sha256":"32b1cad8264eb08ca84ad29c2775645fb5a129f2d9d267a2eb19dfb799ae5092","start":373}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
