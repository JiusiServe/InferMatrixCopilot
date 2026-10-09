---
title: "jiuwenbox-src 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7821"]
confidence: high
---

# jiuwenbox-src 审查规则

## JW-JBX-DLL-1a — 原生 DLL 进入包数据，构建中间产物留在仓库外

- 触发：修改 jiuwenbox 原生 DLL、其构建脚本或 pyproject package-data。
- 强制：将分发 DLL 匹配到 package-data 的 native/*.dll；构建使用与目标一致的 x64 工具链，缺 cl.exe 明确失败；忽略并清理 pdb/lib/exp/obj 等中间产物。
- 禁止：只在源码目录放 DLL 而遗漏 wheel 包数据；提交链接中间产物；仅凭脚本提示 x64 就宣称工具链位数已经验证。
- 验收：检查构建工具链和输出 PE 架构；实际 wheel 中包含分发 DLL，受跟踪文件中无新增中间产物。^[PR #7821]
