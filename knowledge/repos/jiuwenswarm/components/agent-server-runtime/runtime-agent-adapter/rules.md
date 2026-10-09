---
title: "Agent adapter 运行时规则"
created: 2026-10-06
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7689", "PR #7796", "PR #7587"]
confidence: high
---

# Agent adapter 运行时规则

## JW-RUNTIME-ROUTING-1a — Code 的模型路由 rail 由规范化 sub-mode 决定

- 触发：修改 `CodeAdapter._build_agent_rails`、Code session 重建或模型档位路由的挂载。
- 强制：以规范化后的 `sub_mode` 区分 profile；`normal`/`plan` 分支追加 `_model_routing_rail`，builder 为 `_build_model_routing`，参数使用同一 `config_base`；team 分支将该属性设为 `None`。重建时顶层 `mode="agent"` 的兼容默认不能替代 sub-mode 判定。
- 禁止：只凭顶层 mode 决定挂载；给已由 relay 解析具体模型 ID 的 team profile 再挂同一档位 rail；把挂载 diff 或注释当作四档实际转换已验证的证据。
- 验收：分别检查默认/规范化后的 `normal`、`plan` 与 team 分支，断言 builder、config 和属性清除一致；需要宣称档位转换有效时另核对 rail 的转换实现及实际路由测试。^[PR #7689]

## JW-DEEP-STOP-1a — 停止轮次提醒只在 cancel 成功时计数，并在新轮消费一次

- 触发：修改 xiaoyi_0.2.4.beta3 DeepAdapter 的 interrupt、普通 chat.send 或输出租约收回。
- 强制：cancelled 且 intent=cancel 时递增停止轮计数，supplement 不计；普通新轮先有界收回 attach_output 租约，再消费并清零一次性提醒，只提示处理最新请求。
- 禁止：未取到输出流时静默只回 accepted；把 supplement 算作放弃；消费提醒前丢失收回过程中新增的取消计数；宣称注入提醒能保证模型必然服从。
- 验收：覆盖 cancel/supplement 分支、单次消费和 cancel 早于旧轮注册的租约竞态；超时按真实失败处理，不吞掉新请求。^[PR #7796]

## JW-CODE-MEMORY-1a — 冷启动初始化去重且不阻塞请求，卸载时取消后台任务

- 触发：修改 dev-stable interface_code.CodingMemoryRail 的 before_invoke、后台 manager 初始化或 uninit。
- 强制：用一个保存的 task 启动冷初始化，不在 before_invoke 等待索引完成；并发调用共享该 task。cron/heartbeat 只读判定来自真实输入，只有 manager 可用且非只读时才预取；uninit 取消未完成初始化并清除 task 引用。
- 禁止：重复启动冷索引或阻塞用户首条请求；引入没有定义来源的只读属性；把 task 已创建当作 manager 初始化成功；将取消当作正常初始化完成。
- 验收：阻塞 initializer 时 before_invoke 仍及时返回且只创建一次任务；只读请求不预取，uninit 取消后台 task，取消不置完成标记；失败降级行为同时核对锁定的基类实现。^[PR #7587]
