---
title: "common-tools 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7797", "PR #7809"]
confidence: high
---

# common-tools 审查规则

## JW-TOOLS-ROUTE-1a — 命令工具执行与测试必须绑定同一 SysOperation 路由

- 触发：修改 xiaoyi_0.2.4.beta3 中 command_tools、mcp_toolkits 或多会话子代理的命令执行绑定。
- 强制：通过绑定的 SysOperation 创建命令工具，并让子代理解析同一 operation；未绑定或 provider 不支持时返回明确错误。沙箱测试 mock/await `client.exec_async`，host 用例断言沙箱未调用，反之亦然。
- 禁止：未绑定时退回宿主直接执行；只 mock 未被真实调用的同步 exec；把工具路由已绑定当作 FileGuard 已安装。
- 验收：未绑定用例不执行命令；host/sandbox 路由分别验证返回值与真实调用参数，沙箱 AsyncMock 被 await 一次。^[PR #7797]^[PR #7809]
