---
title: "定时任务与调度存储：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_cron_expr.py:L12-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_cron_scheduler.py:L2564-L2593]
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
