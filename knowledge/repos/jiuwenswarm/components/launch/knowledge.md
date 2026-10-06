---
title: "launch 组件基础：桌面外壳 desktop_app 的启动编排"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L1230-L1284, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L1287-L1427, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/desktop-electron-packaging.md:L216-L232, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L340-L381, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L443-L492, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/desktop-electron-packaging.md:L29-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L1087-L1137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L1693-L1904, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L710-L774, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L1230-L1278, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/desktop/desktop_app.py:L1287-L1389]
---

# launch 组件基础：桌面外壳 desktop_app 的启动编排

<!-- kb:knowledge owner=launch facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**桌面主进程作为三服务的编排者**

desktop_app.py 的 DesktopRuntime.start_services 是桌面启动的控制流核心：先做 Gateway 单例预检（防止同一 workspace 双开导致 cron 重复调度），再依次拉起 web 静态服务、AgentServer 与 Gateway 三个托管子进程，并用三个并行等待线程分别探测 agent/gateway 的 TCP 就绪与 web 的 HTTP 就绪，任一失败即终止全部子进程树。web 静态页就绪即触发先行导航（on_web_ready），界面骨架先于后端就绪展示，API/WS 由前端重连逻辑补齐。启动成功后还有一个 daemon 看护线程保持 agent/gateway 成对存活：任一退出立即终止另一方，防止端口、cron 与单例锁泄漏。Electron 壳文档将这一流程标注为与 Python 桌面对齐的参照物。

Sources / 来源：[jiuwenswarm/channels/desktop/desktop_app.py:L1230–L1284](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1230-L1284), [jiuwenswarm/channels/desktop/desktop_app.py:L1287–L1427](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1287-L1427), [docs/zh/desktop-electron-packaging.md:L216–L232](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/desktop-electron-packaging.md#L216-L232)

<!-- kb:knowledge owner=launch facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**端口组与子进程环境契约**

resolve_desktop_ports 复用 instance_manager 的 find_available_ports（base + index×1000，scan 默认 10 组），docstring 明确结果只存在于本次进程内存与子进程 env，不落盘；BASE_PORTS 文档给出 agentServer=18092、gatewayApi=19000、frontend=5173。_build_child_env 为所有子进程注入 JIUWENSWARM_DESKTOP=1、JIUWENSWARM_RUNTIME_WORKSPACE_READY=1 及整套会话端口（WEB_PORT/GATEWAY_PORT/AGENT_SERVER_PORT=AGENT_PORT/FRONTEND_PORT），并删除陈旧 AGENT_SERVER_URL 防止 .env 里的旧 URL 绕过重映射端口；JIUWENSWARM_START_CMD 缺省时记录本次 argv 供更新器构造重启命令。桌面 token 仅注入 web 子进程，其他子进程主动剔除。

Sources / 来源：[jiuwenswarm/channels/desktop/desktop_app.py:L340–L381](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L340-L381), [jiuwenswarm/channels/desktop/desktop_app.py:L443–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L443-L492), [docs/zh/desktop-electron-packaging.md:L29–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/desktop-electron-packaging.md#L29-L41)

<!-- kb:knowledge owner=launch facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**桌面会话锁定与 Windows 托盘/关闭策略**

桌面锁：DesktopRuntime 每次启动生成 secrets.token_urlsafe(32)，首个导航 URL 以 ?dt=<token> 携带，由 web 静态服务换取 HttpOnly Cookie，浏览器直接打开对话页面则返回 403；日志展示用不含 token 的 frontend_display_url。Windows 关闭行为：_on_closing 读取 workspace 下 desktop-window.json 的 close_action（ask/hide/quit），ask 时弹出 WinForms 原生对话框询问隐藏到托盘还是退出并可记住选择；hide 走 NotifyIcon 托盘（显示并最大化/退出菜单），macOS 则通过拦截 windowShouldClose: 与 reopen 事件实现关窗不退应用。

Sources / 来源：[jiuwenswarm/channels/desktop/desktop_app.py:L1087–L1137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1087-L1137), [jiuwenswarm/channels/desktop/desktop_app.py:L1693–L1904](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1693-L1904)

<!-- kb:knowledge owner=launch facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**pywebview 桥接方法与服务启动生命周期**

_WindowApi 是暴露给 WebView 内 JS 的桥接对象：一部分方法（如 minimize_window/close_window、blob 保存四步事务 begin/append/finish/abort）薄委托给 DesktopRuntime 同名实现；另一些方法在桥接层直接实现行为——open_external_url 自行校验目标 URL 必须匹配 SkillHub OAuth 基址（环境变量或默认 swarmskills.openjiuwen.com）且路径限于 gitcode/github 两个 start 端点后才调用系统浏览器，download_file 会把以 / 开头的相对 URL 改写为前端 host:port 的完整地址。DesktopRuntime.start_services 是主生命周期入口：先 _preflight_gateway_singleton 拒绝同工作区二次启动（等待至多 15s），再依次拉起 web、agent、gateway 子进程，并用三个线程并行等待就绪（超时 STARTUP_TIMEOUT_SECONDS=120s）；任一等待失败立即终止全部进程树，全部结束后若 startup_errors 非空则抛出第一个错误——但在此之前先检查 _startup_cancelled，窗口关闭导致的取消优先于等待错误抛出。web 的 HTTP 就绪会触发一次 on_web_ready 回调（先行导航），不必等 agent/gateway 就绪。

Sources / 来源：[jiuwenswarm/channels/desktop/desktop_app.py:L710–L774](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L710-L774), [jiuwenswarm/channels/desktop/desktop_app.py:L1230–L1278](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1230-L1278), [jiuwenswarm/channels/desktop/desktop_app.py:L1287–L1389](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/desktop/desktop_app.py#L1287-L1389)

