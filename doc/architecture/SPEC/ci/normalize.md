# ci/normalize.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~31 · 边缘（CI） · refactor-status: ok`

## 职责
在分组之前，把一条 CI 失败签名归一化。

## 公开契约
`normalize_signature(signature) -> str`。

## 不变量
- 抹去逐 run 变化的噪声（时间戳、哈希、地址、tmp 路径、行号、耗时）；
  保留小的字面数字作为信号。
- **刻意不继承**父 monitor 的精确字符串比较缺陷 —— 跨 run 的同一个失败必须坍缩为
  同一组。

## 边界 —— 不属于这里
只做字符串归一化 —— 不分组（那是 `pr.group_failures`），不抓日志（那是
`ci/providers`）。

## 依赖（允许）
仅 stdlib 的 `re`。

## 测试
`test_ci_and_repo_map.py`。

## 重构备注
小而纯 —— 归一化规则本身就是它的全部价值。如果实践中出现误合并，请调这里的正则表
（**唯一一处**），而不是在调用点打补丁。
