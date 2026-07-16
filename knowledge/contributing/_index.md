# 知识树贡献规范

## 什么时候查这里

- 新增、移动、拆分、删除或重命名知识页面。
- 不确定内容归属、页面类型、错题格式或拆分时机。

## 不放什么

- 某个仓库或模型的业务规则；这些放 `repos/`。
- SSH、review、CI 等日常任务方法；这些放 `framework/`。
- 当前机器事实；这些只放 ignored `local/`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 快速落盘和 P0 | [根贡献入口](../CONTRIBUTING.md) | 日常必读的短入口 |
| 判断层级、owner 和查询路由 | [layout](layout.md) | framework、repo、component、model、local |
| 写索引、规则、架构和普通页 | [page rules](page-rules.md) | 人类可直接照做的页面规范 |
| 复盘、规则提炼和错题 | [incidents](incidents.md) | 错题可选，规则优先 |
| 文件、目录、dev、component 或 model 长大 | [scaling](scaling.md) | 拆分阈值和方式 |
| 同步索引、链接、隐私和检查脚本 | [validation](validation.md) | 修改和提交前验收 |
