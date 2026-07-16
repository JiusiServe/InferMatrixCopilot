# Serving 共享架构

## 负责什么

Serving 层把用户输入转换成内部请求，选择 online/offline 执行入口，并把参数交给实际 engine 或 pipeline。它也是 CLI、HTTP 和兼容 API 之间保持行为一致的责任边界。

## 调查顺序

1. 从用户实际入口确认请求字段和默认值。
2. 沿解析后的请求对象确认字段没有丢失或改义。
3. 用 server log 或真实请求证明命中了预期 engine/pipeline。
4. 只有字段已经正确到达模型层后，才把问题下钻到 component 或 model。

## 不在这里决定的事情

Serving 层不应该偷偷修正模型算法、制造静默 fallback，或用入口默认值掩盖下游配置错误。

源码目录会随版本演进，具体 owner path 在改代码前必须以目标仓库当前版本为准。
