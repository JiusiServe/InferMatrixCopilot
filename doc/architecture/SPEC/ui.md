# ui.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~164 · 呈现 · refactor-status: ok`

## 职责
终端渲染：流式输出、spinner、markdown、颜色；在非 TTY / 管道下降级为纯文本。

## 功能
`make_ui(out?)` 返回 rich UI 或 `PlainUI`；流的 start/delta、带样式的 step/tool 输出、
markdown 渲染、输入历史。

## 公开契约
`make_ui`、`style(...)`，以及 UI 对象的 `stream_*` / print 方法。

## 不变量
- **只做呈现** —— 不携带控制流或 run 状态。
- 确定性的纯文本回退，因此脚本化输出保持稳定。

## 边界 —— 不属于这里
不决定**做什么** —— 只决定**长什么样**。不含任务/规划/执行逻辑；不含仓库知识。

## 依赖（允许）
`rich`；stdlib。

## 扩展点
新的渲染元素 → 在 UI 上加一个方法；**同步维护 `PlainUI` 回退**。

## 测试
`test_ui.py`。

## 重构备注
职责分离得很干净。唯一的坏味道：`cli/`/`chat.py` 会先内联格式化一些字符串再交给 `ui`；
一次重构可以把更多格式化搬到这里，让调用方传**结构化数据**而不是预格式化字符串。
