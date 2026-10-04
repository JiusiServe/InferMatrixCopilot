# engine/steps/improve.py —— 规范

<!-- verified-against: 2026-10-04 -->

## 职责

将工作流改进服务接入 StepRegistry。算法、评估及持久化契约见 [改进引擎规范](../../improve.md)；操作入口见 [中文使用指南](../../../../guide/self-evolution.md)。

## 公开契约

`improve.stage_items` 准备冻结输入；`improve.mode` 区分周度周期、进化协调器和元基准 case。`improve.preflight/sync/lint/experiments/forensics/ledger/report` 保留 P0–P4 周期。`improve.coordinate` 调用 CLI 和调度器共用的可续跑协调器。

`improve.forensics` 只读指定工作流和仓库的 trace；归因输出引用记录 ID。旧配置元基准路径调用 `meta.run_case` 生成 `meta_eval`；源码版本化实验则由可信父进程评分，候选 worker 只接收 case 输入，不接收人工标签。

## 不变量

- 读取 trace store 优先使用当前绑定实例，未绑定时使用 Settings 的根目录；缺根时阻塞或返回明确跳过原因。
- `improve.publish` 和 `improve.evolve_publish` 为 push 风险，影子执行器在运行前拒绝。
- 进化发布只接受 pr-ready 制品；任务 post、ALLOW_POST、ALLOW_PUSH 均须开放，发布准备仍由可信父进程验证。
- `IMPROVE_ENABLED` 是总停止开关；元基准模式不顺带运行周度周期或发布。
- 知识摄取候选仅在隔离输入中验证，不写生产知识库。

## 测试

`test_improve_p0b.py`、`test_improve_p1.py`、`test_improve_p2.py`、`test_improve_p3.py`、`test_improve_p4.py`、`test_evolution.py`。
