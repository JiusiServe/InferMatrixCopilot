---
title: "定时任务与调度存储：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_cron_expr.py:L12-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_cron_scheduler.py:L2564-L2593, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/models.py:L477-L641, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/cron_expr.py:L55-L76, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/cron_expr.py:L15-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/cron_expr.py:L11-L12]
feature: "cron"
entry_points: ["jiuwenswarm/runtime/cron/factory.py"]
source_globs: ["jiuwenswarm/runtime/cron/factory.py", "jiuwenswarm/runtime/cron/*.py"]
---

# 定时任务与调度存储：实现深读

[功能概览](feature-cron.md) · [owner 入口](_index.md)

<!-- kb:depth feature=cron facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb3cf61887ef06c6209b3c4d75eacea54b56f2047f20400fcedffee40f7c4a69 -->
**表达式校验与文件锁的单测入口**
`test_validate_cron_expression_accepts_shared_five_and_seven_field_syntax` 参数化断言 `validate_cron_expression` 在 `Asia/Shanghai` 下同时接受 5 段（`15 9 * * 1-5`）与 7 段（含固定年份 2099）表达式；`test_next_cron_datetime_preserves_seconds_for_seven_fields` 与 `test_next_cron_datetime_supports_far_future_fixed_year` 断言秒字段保留和跨年触发。`TestCronJobStoreFileLock.test_held_file_lock_times_out_other_store` 断言伴生锁被外部持有时 `create_job` 抛 portalocker `LockException`、锁释放后写入恢复。以上为断言内容，非本次运行结果。

来源：[tests/unit_tests/runtime/test_cron_expr.py:L12–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_cron_expr.py#L12-L41), [tests/unit_tests/gateway/test_cron_scheduler.py:L2564–L2593](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_cron_scheduler.py#L2564-L2593)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":41,"path":"tests/unit_tests/runtime/test_cron_expr.py","sha256":"85056f1cc20e2ef6c5f28439ed33c7a37fafdf0df3a6cd981299451c8552ccfd","start":12},{"end":2593,"path":"tests/unit_tests/gateway/test_cron_scheduler.py","sha256":"8c016c26ce3b567e320e3370642a371511d7f288742a5311ded62939984cce9c","start":2564}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cron facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d938c756241f98663dba9b3e7d24c0fcc5b2f1d3a6bcf2610330fc7dfc543336 -->
**持久化 job 字典到已校验 CronJob 的调用链**
输入是存储读出的单个 job 字典：CronJob.from_dict（models.py:477）规整各字段后，在 536 行把 cron_expr 连同 timezone 传入 validate_cron_expression；后者在 70 行调用 normalize_cron_expr，把 5 段表达式补成 7 段 Quartz（24-25 行），字段数非 5/7 时抛 ValueError；normalize_cron_expr 在 23 行调用 cron_field_count 统计字段数。校验全部通过后 from_dict 返回完整 CronJob，ValueError 则向上传播给调用方决定取舍。

调用路径：`jiuwenswarm/runtime/cron/models.py`（`CronJob.from_dict`） → `jiuwenswarm/runtime/cron/cron_expr.py`（`validate_cron_expression`） → `jiuwenswarm/runtime/cron/cron_expr.py`（`normalize_cron_expr`） → `jiuwenswarm/runtime/cron/cron_expr.py`（`cron_field_count`）

来源：[jiuwenswarm/runtime/cron/models.py:L477–L641](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/models.py#L477-L641), [jiuwenswarm/runtime/cron/cron_expr.py:L55–L76](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/cron_expr.py#L55-L76), [jiuwenswarm/runtime/cron/cron_expr.py:L15–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/cron_expr.py#L15-L32), [jiuwenswarm/runtime/cron/cron_expr.py:L11–L12](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/cron_expr.py#L11-L12)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":641,"path":"jiuwenswarm/runtime/cron/models.py","sha256":"e32a65ad2c92553e70f1fafea568872f3b111e3fa39cb8dffe1a58638cd4e160","start":477},{"end":76,"path":"jiuwenswarm/runtime/cron/cron_expr.py","sha256":"40a4c8261611545689b9dc53759588596b1ccbcfee2cd19e9b069677e41b1456","start":55},{"end":32,"path":"jiuwenswarm/runtime/cron/cron_expr.py","sha256":"97c8a10ccb9ae48ebc1c48e46beb063df08f4acc53ff20e5b4648fa5d41a7aa2","start":15},{"end":12,"path":"jiuwenswarm/runtime/cron/cron_expr.py","sha256":"abd4cadbcdef7eee9f65e1540510a54b20f680fda5e15eab573031fd738f57c0","start":11}],"trace":[{"end":641,"path":"jiuwenswarm/runtime/cron/models.py","start":477,"symbol":"CronJob.from_dict"},{"end":76,"path":"jiuwenswarm/runtime/cron/cron_expr.py","start":55,"symbol":"validate_cron_expression"},{"end":32,"path":"jiuwenswarm/runtime/cron/cron_expr.py","start":15,"symbol":"normalize_cron_expr"},{"end":12,"path":"jiuwenswarm/runtime/cron/cron_expr.py","start":11,"symbol":"cron_field_count"}]} -->
<!-- /kb:depth -->
