---
title: "定时任务与调度存储：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_cron_expr.py:L12-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_cron_scheduler.py:L2564-L2593, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/models.py:L477-L641, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/cron_expr.py:L55-L76, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/cron_expr.py:L15-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/cron_expr.py:L11-L12, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/etcd_store.py:L208-L246, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/etcd_store.py:L212-L226, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/etcd_store.py:L227-L246, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/factory.py:L75-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/factory.py:L17-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/factory.py:L63-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_cron_factory.py:L14-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/factory.py:L54-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/cron/etcd_store.py:L65-L74, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_cron_factory.py:L33-L40]
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

<!-- kb:depth feature=cron facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4e40507d6224774c61bd649ec5279f51e66822210ff0770651a7a97c3858667c -->
**update_job 契约：空 id 抛 ValueError("id is required")，job 不存在抛 KeyError("job not found")**
update_job 对空 id 抛 ValueError("id is required")，读取不到现有任务抛 KeyError("job not found")；成功路径在锁内按 mod_revision 条件写回并返回更新后的 CronJob。

来源：[jiuwenswarm/runtime/cron/etcd_store.py:L208–L246](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/etcd_store.py#L208-L246)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":246,"path":"jiuwenswarm/runtime/cron/etcd_store.py","sha256":"849aa58ebe9024b559b3d955099c41bb2d103e4496f1d684f3433e4c594bfd33","start":208}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cron facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=91887ac6b601abf2b4e21076c997ef0236f92cb673b7615dd2febe5c91dfb0be -->
**store_backend 缺省 "file"、仅显式 "etcd" 生效；etcd_endpoints/etcd_prefix 的缺省与解析**
gateway.cron.store_backend 未设置或空白时默认 "file"（取值经 strip().lower() 归一），任何非 "etcd" 值都返回 FileCronJobStore；仅 "etcd" 构造 EtcdCronJobStore，且 etcd_endpoints 为空时只记 error 日志、不回落文件。etcd_endpoints 接受列表/元组或逗号分隔字符串，逐项 strip 并丢弃空项；etcd_prefix 缺省为 "/jiuwenswarm/cron/jobs/"。

来源：[jiuwenswarm/runtime/cron/factory.py:L17–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/factory.py#L17-L51), [jiuwenswarm/runtime/cron/factory.py:L63–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/factory.py#L63-L84), [tests/unit_tests/gateway/test_cron_factory.py:L14–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_cron_factory.py#L14-L17)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":51,"path":"jiuwenswarm/runtime/cron/factory.py","sha256":"c6272eb136a8c7030db42224d6e1f399fc9f35d4d78a673c816016bd2776a12e","start":17},{"end":84,"path":"jiuwenswarm/runtime/cron/factory.py","sha256":"8eddaac024714ede55ffcf6484c7cc255153cfd4ec852ff2aaf95487f13ede88","start":63},{"end":17,"path":"tests/unit_tests/gateway/test_cron_factory.py","sha256":"ecfbe9a3ce33eaf2d260eb28c768e1955a6553409d45c062fb32c019871a0e3b","start":14}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cron facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3cfd52254241a69407c0d9c9458e67d8e13a0941c6b6a929ad621b5c2d7a9cec -->
**update_job 依赖 etcd 客户端的 mod_revision 条件写**
更新依赖 _client.put_if_mod_revision(..., mod_revision=mod_rev) 条件写入：先经 _get_job_with_rev 取回任务与修订号；任何 EtcdError 统一被包成 _unavailable(...) 再上抛。

来源：[jiuwenswarm/runtime/cron/etcd_store.py:L212–L226](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/etcd_store.py#L212-L226)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":226,"path":"jiuwenswarm/runtime/cron/etcd_store.py","sha256":"f2b480e2695fc3196812fe84c9bd0f7cba2278540cf7b3791fff323251aa5ed9","start":212}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cron facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=faa8d7e4d029b357a37aa349230a412a2cd0ff555e2ca7741324943c4349f106 -->
**CAS 冲突单次重试后上抛；选 etcd 缺 etcd_endpoints 不回退文件**
put_if_mod_revision 抛 EtcdCasError 触发重读任务并重放 patch 的单次重试；重读时任务已删抛 KeyError，重试 put 的 EtcdError 包成 unavailable("cas-put")。选 etcd 但无 endpoints 仅记 error 日志仍构造 EtcdCronJobStore。

来源：[jiuwenswarm/runtime/cron/etcd_store.py:L227–L246](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/etcd_store.py#L227-L246), [jiuwenswarm/runtime/cron/factory.py:L75–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/factory.py#L75-L83)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":246,"path":"jiuwenswarm/runtime/cron/etcd_store.py","sha256":"9b1199e2e79dc9f935fba3c3c33de50e6905f2784397ef2c5e022ca404d1bba9","start":227},{"end":83,"path":"jiuwenswarm/runtime/cron/factory.py","sha256":"a1d28630adb041bf8443f79564bdbd58588ee3eefd0126cb1ba8fba62c8e8438","start":75}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cron facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a298c142294870867d05e4803ffb72bff55971589a413b0b4fa60820ef1fde14 -->
**默认 file 免外部状态服务（推断收益）；etcd 缺 endpoints 不回落文件（推断代价）**
设计推断（非作者历史意图）：

收益（推断）：默认 file 后端使部署无需 etcd 服务，docstring 明确 etcd 仅经 gateway.cron.store_backend=etcd 显式启用、不从非空 endpoints 推断。代价（推断）：误选 etcd 且 etcd_endpoints 为空时不回落文件，工厂记 error 后仍返回 EtcdCronJobStore（测试断言 list_jobs()==[]），_unavailable 相应报 "etcd endpoints are empty"。

来源：[jiuwenswarm/runtime/cron/factory.py:L54–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/factory.py#L54-L84), [jiuwenswarm/runtime/cron/etcd_store.py:L65–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/cron/etcd_store.py#L65-L74), [tests/unit_tests/gateway/test_cron_factory.py:L33–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_cron_factory.py#L33-L40)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":84,"path":"jiuwenswarm/runtime/cron/factory.py","sha256":"ca69ed37c6a706515ad2c4627b8b306f6af8d6b251ec445ce63eeae001c5137e","start":54},{"end":74,"path":"jiuwenswarm/runtime/cron/etcd_store.py","sha256":"664d78b12853ae303f8e8f80ce0cb328d725d39a4514bb8ca57d609f0bfc7fbc","start":65},{"end":40,"path":"tests/unit_tests/gateway/test_cron_factory.py","sha256":"30eded892e7436ae8f9eae4cd902a575a4803fd3eadf05db25d72975d2b17a42","start":33}],"trace":[]} -->
<!-- /kb:depth -->
