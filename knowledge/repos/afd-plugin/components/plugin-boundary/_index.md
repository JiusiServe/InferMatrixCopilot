---
title: "AFD plugin boundary 入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components, plugin-boundary, config]
sources:
  - "afd-plugin@a432692:docs/design/module/plugin_boundary.md"
---

# AFD plugin boundary 入口

## 什么时候查这里

- 修改插件注册、AFD 配置 schema、alias、验证、CPU-safe import 或自动 worker 选择。
- 调查为什么 AFD 未激活、选错 worker，或非 AFD 路径被插件污染。

## 不放什么

- monkey patch 具体差异放 [compatibility](../compatibility/_index.md)。
- connector 私有 schema 和通信资源放 [connectors](../connectors/_index.md)。

## Owner 凭证

- 基线：`afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。
- 主源码：`afd_plugin/__init__.py`、`config.py`、`config_utils.py`、`envs.py`、`validation.py`、`py.typed`、`afd_plugin/v1/__init__.py`、两层 worker `__init__.py`、`pyproject.toml`。
- 输入：`VllmConfig.additional_config["afd"]`、平台、role 和 worker selection state。
- 输出：类型化 `AFDConfig`、已验证的 runtime wiring、lazy model/worker 注册。
- 验证：`tests/unit/config/**`、`tests/unit/package/test_package.py`、`tests/unit/test_envs.py`、`tests/unit/v1/worker/test_runtime_classpaths.py`。
- 影响：所有 AFD 角色、connector、模型和平台路径。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解注册、配置和 worker 选择 | [architecture](architecture.md) | 当前 normative boundary |
| 审查新配置或启动入口 | [rules](rules.md) | `AFD-2b`–`AFD-2d` 硬门禁 |
| 理解整体依赖方向 | [仓库架构](../../architecture.md) | 七 owner 系统图 |
