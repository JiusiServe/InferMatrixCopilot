---
title: "config-resources"
created: 2026-10-01
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# config-resources

理解本 owner 的源码职责、接口和集成边界时查这里。源码接口记录是静态契约；功能语义、配置和取舍沿功能页查证。通用审查方法不放在这里。
- [advanced-daily-report-analyzers](advanced-daily-report-analyzers/_index.md)
- [advanced-daily-report-collectors](advanced-daily-report-collectors/_index.md)
- [advanced-daily-report-generators](advanced-daily-report-generators/_index.md)
- [advanced-daily-report](advanced-daily-report/_index.md)
- [agent-creator-scripts](agent-creator-scripts/_index.md)
- [agent-group-creator-scripts](agent-group-creator-scripts/_index.md)
- [ascend-moe-optimizer-auto-trace-scripts](ascend-moe-optimizer-auto-trace-scripts/_index.md)
- [ascend-moe-optimizer-trace-analyzer-analyzers](ascend-moe-optimizer-trace-analyzer-analyzers/_index.md)
- [ascend-moe-optimizer-trace-analyzer](ascend-moe-optimizer-trace-analyzer/_index.md)
- [baoyu-image-gen-scripts](baoyu-image-gen-scripts/_index.md)
- [cross-channel-history-retrieval-scripts](cross-channel-history-retrieval-scripts/_index.md)
- [delayed-restart-app](delayed-restart-app/_index.md)
- [docx-pro-scripts](docx-pro-scripts/_index.md)
- [dynamic-memory-cli-scripts](dynamic-memory-cli-scripts/_index.md)
- [financial-document-parser](financial-document-parser/_index.md)
- [gitcode-api-scripts](gitcode-api-scripts/_index.md)
- [harmonyos-dev-suite-scripts](harmonyos-dev-suite-scripts/_index.md)
- [huawei-cloud-maas-setup-scripts](huawei-cloud-maas-setup-scripts/_index.md)
- [local-doc-ocr-scripts](local-doc-ocr-scripts/_index.md)
- [openjiuwen-deepsearch-scripts](openjiuwen-deepsearch-scripts/_index.md)
- [plugin-creator-scripts](plugin-creator-scripts/_index.md)
- [ppt-creation-components](ppt-creation-components/_index.md)
- [ppt-creation-scripts](ppt-creation-scripts/_index.md)
- [project-maintainer-scripts](project-maintainer-scripts/_index.md)
- [rsi-program-dataset-creator-scripts](rsi-program-dataset-creator-scripts/_index.md)
- [skill-creator-normal-assets](skill-creator-normal-assets/_index.md)
- [skill-creator-normal-eval-viewer](skill-creator-normal-eval-viewer/_index.md)
- [skill-creator-normal-scripts](skill-creator-normal-scripts/_index.md)
- [skill-gen-4-enterprise-doc-scripts](skill-gen-4-enterprise-doc-scripts/_index.md)
- [skill-omni-creation-scripts](skill-omni-creation-scripts/_index.md)
- [swarmskill-creator-scripts](swarmskill-creator-scripts/_index.md)
- [xlsx-scripts](xlsx-scripts/_index.md)
- [内置日报技能：采集、报告接口与模型配置](knowledge-config-resources.md) — 说明接口、配置与集成边界，关联源码和维护者文档。
- [Agent 模板分层校验器（validate_template.py / validate_hot_load_worker.py）](feature-agent-template-layered-validation.md)
- [extract_arxiv_visuals v2.2 — arXiv 论文 Figure/Table 检测与高清导出](feature-arxiv-visual-extraction.md)
- [Chrome Trace JSON 生成器（trace_collector）](feature-ascend-chrome-trace-generator.md)
- [ascend-moe-optimizer-trace-analyzer CLI 主流程](feature-ascend-trace-analysis-pipeline.md)
- [instrument_operator.py：TRACE_POINT 自动埋点改写脚本](feature-ascend-trace-auto-instrumentation.md)
- [插桩编译安全静态检查器（check_compile_safety.py）](feature-ascend-trace-compile-safety-checker.md)
- [插桩计划生成器（generate_instrumentation_plan.py）](feature-ascend-trace-instrumentation-planner.md)
- [TRACE_POINT 预处理器与 point_map 映射导出（ascend-moe-optimizer-auto-trace skill）](feature-ascend-trace-preprocessor.md)
- [自包含审计可视化 HTML 报告生成器（render_audit_report.py）](feature-audit-report-html-renderer.md)
- [Cross-Channel Session History Search Skill (search_history.py)](feature-cross-channel-history-search-skill.md)
- [docx-pro Word 文档操作 CLI](feature-docx-pro-cli.md)
- [财务文档解析 Skill（financial_parser.py）](feature-financial-document-parser.md)
- [GitHub Issue 反馈创建脚本（open_github_issue.py）](feature-github-issue-feedback-script.md)
- [华为云 MaaS 委托授权自动化（auto_authorize.py）](feature-huawei-maas-cdp-authorize.md)
- [check_account — 华为云账号实名认证状态检测脚本](feature-huawei-realname-account-check.md)
- [华为云 MaaS 预置服务批量开通脚本 auto_open_model.py](feature-maas-auto-open-models.md)
- [add_slide.py — 解包 PPTX 幻灯片添加工具](feature-opc-add-slide.md)
- [OOXML 打包与 schema 校验（opc/pack.py）](feature-opc-pack-validate.md)
- [plugin-creator 插件包脚手架初始化（init_plugin.py）](feature-plugin-package-initializer.md)
- [plugin-creator 插件包分层校验器（validate_plugin.py L0/L1/L2）](feature-plugin-package-layered-validator.md)
- [一键成片流水线与质量门禁（finalize_deck.py）](feature-ppt-deck-finalize.md)
- [PPT 执行锁（execution-lock.json）语义校验器](feature-ppt-execution-lock-validator.md)
- [PPT 图表面板布局引擎（figure-panel.js）](feature-ppt-figure-panel-layout.md)
- [Deck Thumbnail Contact-Sheet Renderer (thumbnail.py)](feature-ppt-opc-thumbnail.md)
- [PPTX 结构与可读性审计脚本（audit_pptx.py 及配套 QA 脚本）](feature-pptx-structural-audit.md)
- [skill-gen CLI（sop-text / url-fetch 子命令）](feature-skill-generator-cli.md)
- [skill-omni-creation 网页抓取到统一 Stage01 Blocks（scrape_page）](feature-skill-page-scrape-blocks.md)
- [SOP 结构化抽取（parse_sop_raw_text / parse_sop_file）](feature-sop-structure-extraction.md)
- [analyze_video.py：视频粗扫抽帧与审核批次门控](feature-video-coarse-scan-frame-extraction.md)
- [XLSX Computed Column Adder (xlsx_add_column.py)](feature-xlsx-add-computed-column.md)
- [XLSX 公式静态校验（formula_check.py）](feature-xlsx-formula-check.md)
- [XLSX Row Insert with Range Extension（jiuwenswarm skills/xlsx 脚本）](feature-xlsx-insert-row.md)
- [XLSX 只读结构读取器与编辑损伤差分（xlsx_reader.py）](feature-xlsx-reader-structural-diff.md)
- [XLSX Skill 格式保留解包/重打包（xlsx_unpack.py / xlsx_pack.py）](feature-xlsx-workbook-unpack-repack.md)
- [进阶版日报/周报/月报生成器 Skill（advanced-daily-report）](feature-daily-report-skill.md)
- [华为云 MaaS API Key 自动创建与捕获（auto_create_apikey）](feature-huawei-maas-apikey-creation.md)
- [local-doc-ocr：本地离线 OCR 管线（RapidOCR：PDF/图片 → Markdown）](feature-local-doc-ocr-offline.md)
- [prepare_evidence.py — Evidence Plan Preparation and Review Lifecycle](feature-ppt-evidence-preparation.md)
- [PPT 系统架构图原生形状渲染引擎（system-diagram.js）](feature-ppt-system-diagram-renderer.md)
- [RSI 数据集任务文件夹完整性预检 check_folder.py](feature-rsi-dataset-folder-check.md)
- [XLSX 技能环境自检（doctor.py）](feature-xlsx-doctor-selfcheck.md)
- [符号审计完整性 HMAC 签名与信任验证（audit_integrity.py）](feature-audit-integrity-hmac-signing.md)
- [openJiuwen-DeepSearch 深度研究执行管线](feature-deepsearch-research-pipeline.md)

- [Agent 模板分层校验器（L0 规范 / L1 静态 AST / L2 子进程编排）：实现深读](feature-depth-agent-template-layered-validation.md)

- [arXiv 论文 Figure/Table 检测与高清导出（extract_arxiv_visuals）：实现深读](feature-depth-arxiv-visual-extraction.md)

- [Chrome Trace JSON 生成器（trace_collector）：实现深读](feature-depth-ascend-chrome-trace-generator.md)

- [ascend-moe-optimizer-trace-analyzer CLI 主流程：实现深读](feature-depth-ascend-trace-analysis-pipeline.md)

- [TRACE_POINT 自动埋点改写（instrument_operator）：实现深读](feature-depth-ascend-trace-auto-instrumentation.md)

- [插桩编译安全静态检查器：实现深读](feature-depth-ascend-trace-compile-safety-checker.md)

- [插桩计划生成器（调用图深度受限展开）：实现深读](feature-depth-ascend-trace-instrumentation-planner.md)

- [TRACE_POINT 预处理器与 point_map 映射导出：实现深读](feature-depth-ascend-trace-preprocessor.md)

- [符号审计完整性 HMAC 签名与信任验证（audit_integrity.py）：实现深读](feature-depth-audit-integrity-hmac-signing.md)

- [自包含审计可视化 HTML 报告生成器：实现深读](feature-depth-audit-report-html-renderer.md)

- [Cross-Channel Session History Search Skill：实现深读](feature-depth-cross-channel-history-search-skill.md)

- [进阶版日报/周报/月报生成器 Skill：实现深读](feature-depth-daily-report-skill.md)

- [openJiuwen-DeepSearch 深度研究执行管线：实现深读](feature-depth-deepsearch-research-pipeline.md)

- [docx-pro Word 文档操作 CLI：实现深读](feature-depth-docx-pro-cli.md)

- [财务文档解析 Skill（发票/收据/对账单解析与报告生成）：实现深读](feature-depth-financial-document-parser.md)

- [GitHub Issue 反馈创建脚本：实现深读](feature-depth-github-issue-feedback-script.md)

- [华为云 MaaS API Key 自动创建与捕获（auto_create_apikey）：实现深读](feature-depth-huawei-maas-apikey-creation.md)

- [华为云 MaaS 委托授权自动化（auto_authorize）：实现深读](feature-depth-huawei-maas-cdp-authorize.md)

- [华为云账号实名认证状态检测（check_account）：实现深读](feature-depth-huawei-realname-account-check.md)

- [本地离线 OCR 管线（RapidOCR：PDF/图片 → Markdown）：实现深读](feature-depth-local-doc-ocr-offline.md)

- [华为云 MaaS 预置服务批量开通自动化（CDP）：实现深读](feature-depth-maas-auto-open-models.md)

- [解包 PPTX 幻灯片添加工具（opc/add_slide.py）：实现深读](feature-depth-opc-add-slide.md)

- [OOXML 打包与 schema 校验（opc/pack.py）：实现深读](feature-depth-opc-pack-validate.md)

- [plugin-creator 插件包脚手架初始化：实现深读](feature-depth-plugin-package-initializer.md)

- [plugin-creator 插件包分层校验器（L0/L1/L2）：实现深读](feature-depth-plugin-package-layered-validator.md)

- [一键成片流水线与质量门禁（finalize_deck.py）：实现深读](feature-depth-ppt-deck-finalize.md)

- [Evidence Plan Preparation and Review Lifecycle：实现深读](feature-depth-ppt-evidence-preparation.md)

- [PPT 执行锁（execution-lock.json）语义校验器：实现深读](feature-depth-ppt-execution-lock-validator.md)

- [PPT 图表面板布局引擎（figure-panel.js）：实现深读](feature-depth-ppt-figure-panel-layout.md)

- [Deck Thumbnail Contact-Sheet Renderer：实现深读](feature-depth-ppt-opc-thumbnail.md)

- [PPT 系统架构图原生形状渲染引擎：实现深读](feature-depth-ppt-system-diagram-renderer.md)

- [PPTX 结构与可读性审计脚本：实现深读](feature-depth-pptx-structural-audit.md)

- [RSI 数据集任务文件夹完整性预检：实现深读](feature-depth-rsi-dataset-folder-check.md)

- [skill-gen CLI（sop-text / url-fetch 子命令）：实现深读](feature-depth-skill-generator-cli.md)

- [Web Page Scraping to Unified Stage01 Blocks：实现深读](feature-depth-skill-page-scrape-blocks.md)

- [SOP 结构化抽取（parse_sop_raw_text / parse_sop_file）：实现深读](feature-depth-sop-structure-extraction.md)

- [视频粗扫抽帧与审核批次门控（analyze_video.py）：实现深读](feature-depth-video-coarse-scan-frame-extraction.md)

- [XLSX Computed Column Adder：实现深读](feature-depth-xlsx-add-computed-column.md)

- [XLSX 技能环境自检（doctor.py）：实现深读](feature-depth-xlsx-doctor-selfcheck.md)

- [XLSX 公式静态校验（formula_check.py）：实现深读](feature-depth-xlsx-formula-check.md)

- [XLSX Row Insert with Range Extension：实现深读](feature-depth-xlsx-insert-row.md)

- [XLSX Read-Only Structure Reader and Edit-Damage Differ：实现深读](feature-depth-xlsx-reader-structural-diff.md)

- [XLSX Skill Format-Preserving Unpack/Repack：实现深读](feature-depth-xlsx-workbook-unpack-repack.md)
