---
title: "定时任务与调度"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# 定时任务与调度

## 什么时候查这里

- CronJob schema 与字段校验、cron 表达式/时区校验、mode 归一与超时。
- 共享创建/patch 规则、proactive.tick 任务保护、模型解析与 credential_ref 绑定。
- 文件存储（双层锁、原子写、惰性迁移）与 etcd 存储（CAS、watch、无文件回落）、后端选择配置。

## 不放什么

- Gateway 侧调度循环/主备 HA（gateway/cron/scheduler.py、controller.py）的运行行为。
- 钉钉会话编码之外的 IM 推送管线细节。

## 目录内容

- [定时任务（Cron）运行时：任务模型、存储后端与投递路由](jiuwenswarm-runtime-cron.md) — 任务模型与校验、目标路由、执行模式与 proactive 保护、模型解析与凭据绑定、共享创建/更新规则、文件/etcd 双后端行为、表达式校验

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：cron、定时任务、cron job、cron 表达式、etcd、主备、HA、cron store、work_mode、proactive、钉钉推送、timezone。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| cron、定时任务、cron job、cron 表达式、etcd、主备、HA、cron store、work_mode、proactive、钉钉推送、time… | 入口 | `jiuwenswarm/runtime/cron/` |

## 专题入口

- [Cron 文件与 etcd 存储后端](jiuwenswarm-cron-store.md) — 说明 CronJob 持久化、后端选择、文件锁、变更修订与 etcd CAS/watch；任务 schema、表达式和执行路由见 Cron 主页面。
