---
title: "financial-document-parser 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# financial-document-parser 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6f044c524b9d44e0986259e15f602d26568d663816a0d4080f56e22888e82ee7 -->
**`jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py`**

- 源码对模块职责的说明：Financial Document Parser - 财务文档解析工具 支持解析 PDF 发票、收据、银行对账单等财务文档。
- `LineItem` 定义类型边界。
- `FinancialDocument` 定义类型边界。
- `FinancialParser` 定义类型边界；方法入口：`__init__`, `parse`, `to_dict`, `to_json`, `to_csv`, `to_markdown`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import csv`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L1-L558)。
<!-- /kb:file -->
