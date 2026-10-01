---
title: 桌面宿主与自动更新 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/windows自动更新设计.md
---

# 桌面宿主与自动更新 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-desktop facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

桌面宿主负责启动、窗口和更新流程，Agent 执行仍由服务承担。更新涉及文件替换与进程重启，发布版本与正在运行的版本需要分别确认。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/channels/desktop/desktop_app.py:L1–L3602](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1-L3602)；[docs/zh/windows自动更新设计.md:L1–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/windows%E8%87%AA%E5%8A%A8%E6%9B%B4%E6%96%B0%E8%AE%BE%E8%AE%A1.md#L1-L149)。

<!-- kb:knowledge owner=feature-desktop facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `attachment_open_file_types()`；`resolve_desktop_ports(host, scan_range)`；`DesktopRuntime [frontend_url, frontend_display_url, get_startup_status, start_services, minimize_window]`；`main()`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/channels/desktop/desktop_app.py:L1–L3602](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1-L3602)；[docs/zh/windows自动更新设计.md:L1–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/windows%E8%87%AA%E5%8A%A8%E6%9B%B4%E6%96%B0%E8%AE%BE%E8%AE%A1.md#L1-L149)。

<!-- kb:knowledge owner=feature-desktop facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `updater.enabled`、`updater.desktop_release_api_type`、`updater.repo_owner`、`updater.repo_name`、`updater.release_api_url`、`updater.asset_name_pattern_linux`、`updater.timeout_seconds`。这些是示例字段，不单独证明源码默认值或全部优先级。 实现中直接读取的环境变量名称包括 `SKILLHUB_OAUTH_BASE_URL`、`TEAM_SKILLS_HUB_BASE_URL`、`WINDIR`；名称与实际部署值分开核对。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/channels/desktop/desktop_app.py:L1–L3602](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1-L3602)；[docs/zh/windows自动更新设计.md:L1–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/windows%E8%87%AA%E5%8A%A8%E6%9B%B4%E6%96%B0%E8%AE%BE%E8%AE%A1.md#L1-L149)。

<!-- kb:knowledge owner=feature-desktop facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：外部更新 helper 在退出后安装和重启，降低运行进程自替换的复杂度；代价是下载成功仍需跨进程完成安装。Windows 与 macOS 按 Release 时间排序而非语义版本，稳定版也可能收到 beta；发布资产命名和当前版本 Release 的可查询性成为更新契约。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/channels/desktop/desktop_app.py:L1–L3602](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1-L3602)；[docs/zh/windows自动更新设计.md:L1–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/windows%E8%87%AA%E5%8A%A8%E6%9B%B4%E6%96%B0%E8%AE%BE%E8%AE%A1.md#L1-L149)。

<!-- kb:knowledge owner=feature-desktop facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

桌面宿主负责启动、窗口和更新流程，Agent 执行仍由服务承担。更新涉及文件替换与进程重启，发布版本与正在运行的版本需要分别确认。 联调时结合[打包与部署](../packaging-deploy/feature-deployment.md)、[单机多实例](feature-instances.md)、[Web 页面与功能入口](../web-frontend/feature-web-navigation.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/channels/desktop/desktop_app.py:L1–L3602](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1-L3602)；[docs/zh/windows自动更新设计.md:L1–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/windows%E8%87%AA%E5%8A%A8%E6%9B%B4%E6%96%B0%E8%AE%BE%E8%AE%A1.md#L1-L149)。

<!-- kb:knowledge owner=feature-desktop facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

分别检查启动自动查更与手动查更、当前版本不在分页列表时的 tag 补查、同平台多个附件的选择。验证下载失败保留现有安装，并在 helper 安装重启后核对实际运行版本与用户工作区。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/channels/desktop/desktop_app.py:L1–L3602](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1-L3602)；[docs/zh/windows自动更新设计.md:L1–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/windows%E8%87%AA%E5%8A%A8%E6%9B%B4%E6%96%B0%E8%AE%BE%E8%AE%A1.md#L1-L149)。
