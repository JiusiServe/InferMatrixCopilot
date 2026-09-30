---
title: "定时任务（Cron）运行时：任务模型、存储后端与投递路由"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 定时任务（Cron）运行时：任务模型、存储后端与投递路由

负责定时任务（CronJob）的数据模型、cron 表达式的校验与下次触发时间计算，以及任务的持久化。持久化有两种后端：个人版用文件存储，主备 Gateway 用 etcd 存储，两者都实现同一个存储协议。模块还负责把钉钉里创建的定时任务推送回发起它的会话。

**从这里读起**

- `jiuwenswarm/runtime/cron/factory.py` — load_cron_store_settings 读取配置，create_gateway_cron_store 据此选用文件存储或 etcd 存储
- `jiuwenswarm/runtime/cron/store_base.py` — CronJobStoreBackend 协议：定义 list/get/create/update/delete/get_revision/watch/aclose，两种后端都要实现
- `jiuwenswarm/runtime/cron/models.py` — CronJob、CronTarget、CronRunState 数据模型，以及目标频道、运行模式、超时、MCP、模型字段的规范化与校验

**关键文件**

- `jiuwenswarm/runtime/cron/cron_job_mutations.py` — 文件和 etcd 两种存储共用的任务构建、patch 合并、work_mode 推断与迁移逻辑，以及 proactive 任务的改删保护
- `jiuwenswarm/runtime/cron/store.py` — FileCronJobStore：在文件锁下读写 JSON，用文件修订号实现 watch，另有 disable_project_jobs
- `jiuwenswarm/runtime/cron/etcd_store.py` — EtcdCronJobStore：主备 Gateway 用的 etcd 存储，更新时带 mod_revision 做 CAS，并监听前缀变化
- `jiuwenswarm/runtime/cron/etcd_client.py` — 基于 httpx 的精简 etcd v3 gRPC-gateway JSON 客户端（range/put/delete/CAS/watch），不依赖 grpc
- `jiuwenswarm/runtime/cron/cron_expr.py` — cron 表达式规范化、按时区校验、把 ISO 时间转成 7 段 cron、计算下次触发时间
- `jiuwenswarm/runtime/cron/dingtalk_routing.py` — 钉钉定时任务的会话 ID 编码与解析，以及推送元数据解析（Issue #2449）

**路由**

- `jiuwenswarm/runtime/cron/`
