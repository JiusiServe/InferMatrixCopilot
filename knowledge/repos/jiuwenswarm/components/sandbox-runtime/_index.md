---
title: "sandbox-runtime"
created: 2026-10-01
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# sandbox-runtime

理解该代码 owner 的职责、接口、配置与相关功能时查这里；通用审查方法不属于本目录。
- [JiuwenBox 隔离执行 功能知识](feature-sandbox.md)
- [JiuwenBox 推理隐私代理功能知识](feature-sandbox-privacy-proxy.md)
- [JiuwenBox 隔离执行：实现深读](feature-depth-sandbox.md)
- [JiuwenBox 推理隐私代理：实现深读](feature-depth-sandbox-privacy-proxy.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：sandbox runtime。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| sandbox runtime | 入口 | `jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py`、`jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py`、`jiuwenbox/src/jiuwenbox/server/app.py` |

- [sandbox-runtime（JiuwenBox 服务与推理隐私代理）](knowledge.md)
