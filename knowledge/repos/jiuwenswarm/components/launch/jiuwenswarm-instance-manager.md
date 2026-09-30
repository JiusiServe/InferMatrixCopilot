---
title: "instance_manager：多实例配置、端口与进程管理"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# instance_manager：多实例配置、端口与进程管理

负责 JiuwenSwarm 多实例的配置与生命周期：维护 instances.yaml、校验实例名、分配端口并检测冲突、为每个实例生成 bootstrap .env。它还用锁文件和 PID 文件控制实例并发启动，并负责查询实例状态和停止实例进程。

**从这里开始读**

- `jiuwenswarm/instance_manager/status.py` — list_all_instances、get_instance_status 查询实例状态，stop_instance_process 停止实例进程
- `jiuwenswarm/instance_manager/bootstrap.py` — create_bootstrap_env 为实例生成 bootstrap .env；load_instance_bootstrap_by_name 在 argparse 解析后加载它；带有 main()
- `jiuwenswarm/instance_manager/yaml.py` — load_instances_yaml 和 update_instances_yaml 负责读写并校验 instances.yaml

**关键文件**

- `jiuwenswarm/instance_manager/config.py` — InstanceConfig、InstanceStatus 数据类，BASE_PORTS、RESERVED_NAMES 等常量，实例名校验，端口计算、探测与冲突检查
- `jiuwenswarm/instance_manager/lock.py` — InstanceLock（跨平台启动锁，含过期锁清理）、GatewayLock、PID 文件读写和进程存活检测
- `jiuwenswarm/instance_manager/status.py` — 按 PID、进程组和监听端口判断进程是否属于本实例，再安全停止；这里的判断逻辑较细，审查时重点看
- `jiuwenswarm/instance_manager/yaml.py` — 实例目录和工作区路径，instances.yaml 结构与端口字段校验，get_instance_index
- `jiuwenswarm/instance_manager/bootstrap.py` — bootstrap .env 的生成与加载，包括不依赖其他模块的早期创建函数 _create_basic_bootstrap_env

**相关文档**

- `docs/zh/Quickstart.md` — 想了解用户怎样启动 JiuwenSwarm，从而判断改动对启动流程的影响时读
- `README_CN.md` — 需要项目整体介绍和启动方式概览时读
- `docs/zh/FAQ.md` — 改动涉及启动失败、端口占用等用户常见问题时，查看已有说法
- `TESTING.md` — 给本模块补测试时参考；其中有过期路径，要以 tests/ 下实际存在的用例为准

**改动路由**

- `jiuwenswarm/instance_manager/`
