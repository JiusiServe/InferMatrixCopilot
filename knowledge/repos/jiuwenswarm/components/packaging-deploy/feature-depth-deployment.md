---
title: "打包与部署：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L144-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:Dockerfile.claw:L78-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L55-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L301-L307, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build_config.py:L264-L299, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build_config.py:L164-L166, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build_config.py:L149-L150, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L143-L176, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_build_config.py:L80-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_build_config.py:L308-L331, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/desktop-electron-packaging.md:L97-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L214-L219, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L260-L261, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/desktop-electron-packaging.md:L49-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L55-L75, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L77-L81]
feature: "deployment"
entry_points: ["scripts/build-electron-exe.sh", "Dockerfile.claw", "docker/Dockerfile.claw", "docker/Dockerfile.claw.base", "docker/Dockerfile.yr.rt.mgr"]
source_globs: ["scripts/build-electron-exe.sh", "scripts/*", "Dockerfile.claw", "docker/Dockerfile.claw", "docker/Dockerfile.claw.base", "docker/Dockerfile.yr.rt.mgr"]
---

# 打包与部署：实现深读

[功能概览](feature-deployment.md) · [owner 入口](_index.md)

<!-- kb:depth feature=deployment facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f9dc181cd85aa67ff253fee7ceb1787a34422d2f7c5ee0502a59dabfd8090fe -->
**ELECTRON_DIR 覆盖与 DMG 命名规则**
Electron.app 来源默认按候选顺序探测（desktop 目录 node_modules、项目根、$HOME），设置 ELECTRON_DIR 环境变量可整体覆盖该探测。DMG 文件名由构建模式决定：FrontendOnly 为 <名>-frontend-test-<版本>.dmg、Test 为 <名>-test-<版本>.dmg、正式为 <名>-setup-<版本>.dmg。

来源：[scripts/build-electron-exe.sh:L55–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L55-L68), [scripts/build-electron-exe.sh:L301–L307](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L301-L307)

<!-- kb:depth-proof {"evidence":[{"path":"scripts/build-electron-exe.sh","start":55,"end":68,"sha256":"bc8de90679acd490af8a06c95276ecf6cd841a82af088e7eb3ef0493715364da"},{"path":"scripts/build-electron-exe.sh","start":301,"end":307,"sha256":"58e86c041555cdc0bd7cbbe7268fae8555d1d9c2282bb6c6859d0bd6d742bfd6"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deployment facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=031170e40c571d3d5f693cb39a417fa92ce166919407b55f338a5fea25991581 -->
**build_config 单一来源与 Docker 前端产物的双份落盘**
dist 目录名、exe 名、版本号和 bundle 标识全部来自 scripts/build_config.py --sync --emit-shell，--sync 先同步 _build_config.py，否则 PyInstaller spec 的漂移守卫会硬失败；产物名不写死以免命中改名前的陈旧目录。容器侧 Dockerfile.claw 因后端安装早于前端构建，最终镜像把 dist 同时复制进 site-packages 的 web 路径与源码树，前者是 app_web 唯一的服务目录。

来源：[scripts/build-electron-exe.sh:L144–L159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L144-L159), [Dockerfile.claw:L78–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/Dockerfile.claw#L78-L85)

<!-- kb:depth-proof {"evidence":[{"path":"scripts/build-electron-exe.sh","start":144,"end":159,"sha256":"a8965329140844b3c4458fde0b578328c78cf1ff092198999ad5416d14b028e8"},{"path":"Dockerfile.claw","start":78,"end":85,"sha256":"c2a25bb51a598248682a2a5d5de9ef264f7f0292091d1700b1764459e3d7c30a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deployment facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8cfd495d341c24eb8cba049c2de5efe877062233a77751d9f2ca8f9f9225e60 -->
**main 在 --sync --emit-shell 下经 render_shell 到 _constant_values 输出 BUILD_* 赋值**
输入是 scripts/build-electron-exe.sh:149 的 --sync --emit-shell 调用：main 先在 268-270 行经 write_expected 同步受管文件并把 updated … 状态写 stderr，280 行 load_build_config 取值；因请求了输出，跳过 285-288 行的提前 return，294 行 _emit(render_shell(config), sys.stdout)；render_shell 165 行调 _constant_values（键转大写），经 shlex.quote 生成 BUILD_*=值 写入 stdout，由脚本 150-154 行 sed 提取 BUILD_DIST_DIR_NAME / BUILD_EXECUTABLE_NAME / BUILD_VERSION 等。

调用路径：`scripts/build_config.py`（`main`） → `scripts/build_config.py`（`render_shell`） → `scripts/build_config.py`（`_constant_values`）

来源：[scripts/build_config.py:L264–L299](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build_config.py#L264-L299), [scripts/build_config.py:L164–L166](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build_config.py#L164-L166), [scripts/build_config.py:L149–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build_config.py#L149-L150), [scripts/build-electron-exe.sh:L143–L176](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L143-L176)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":299,"path":"scripts/build_config.py","sha256":"7876066bc1ef84c9799ac3b96fc3056956f038b4887ceb308793aa60cfc20215","start":264},{"end":166,"path":"scripts/build_config.py","sha256":"aef5a1ae5acc6f0cf4b9a0fd9d7d56e1b7f91a968e3d7c00409e6e532e3dbb4b","start":164},{"end":150,"path":"scripts/build_config.py","sha256":"7adc65eb97b273ccf3559c6fe2d7e08e26464b9ed8bd6986c5bcb1a1ab536dd9","start":149},{"end":176,"path":"scripts/build-electron-exe.sh","sha256":"1b50141a676ac36cc1061877ca7796b50e83391c42927ee0107305f3f65ff4f9","start":143}],"trace":[{"end":299,"path":"scripts/build_config.py","start":264,"symbol":"main"},{"end":166,"path":"scripts/build_config.py","start":164,"symbol":"render_shell"},{"end":150,"path":"scripts/build_config.py","start":149,"symbol":"_constant_values"}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deployment facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd55584b57d9c29c5e650c33b0336d49257dca2575b05032a688c7c7d5c7e8cd -->
**test_build_config.py 以临时 fixture 和真实子进程 CLI 钉住漂移检测与输出流分离**
test_check_detects_version_drift_before_write（80-98 行）在同步后的临时 fixture 中把根 pyproject 版本改为 9.8.7.beta6，断言 find_drift 报出 packages/jiuwenswarm-tui/pyproject.toml 与 jiuwenswarm/common/_build_config.py，且 write_expected 之后漂移清零；test_cli_sync_status_uses_stderr_without_log_prefix（308-331 行）以子进程运行真实 CLI，断言 --sync --version 时 stdout 恰为版本行、stderr 恰为三条 updated 行。

来源：[tests/unit_tests/test_build_config.py:L80–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_build_config.py#L80-L98), [tests/unit_tests/test_build_config.py:L308–L331](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_build_config.py#L308-L331)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":98,"path":"tests/unit_tests/test_build_config.py","sha256":"a4e6bbcda0e3cccd65a7cd433d1afac3cb0a52a0b4e746739dfaf5f872fd6145","start":80},{"end":331,"path":"tests/unit_tests/test_build_config.py","sha256":"2492b6ef892d9630afbf3faa910113a773672a358174b8ada50ee9b32099d88b","start":308}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deployment facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=87590f05078c081f8f15b4cac6fcedc41acc0b1a43d347fda6c26fa66ff79029 -->
**FrontendOnly 开关：macOS 脚本在 FRONTEND_ONLY=true 时写 `.frontend-only` 标记、后端复制段以 =false 守卫跳过；Windows 文档记载为不打包后端**
macOS 脚本在 `FRONTEND_ONLY`=true 时向 `$APP_DIR` 写入 `.frontend-only` 标记，PyInstaller 后端复制段位于 `if [ "$FRONTEND_ONLY" = false ]` 守卫内——所示行仅证明该复制段被跳过；Windows 打包文档另记载 `-Test -FrontendOnly` 为"写入 `.frontend-only` 标记，不打包后端"。

来源：[scripts/build-electron-exe.sh:L214–L219](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L214-L219), [scripts/build-electron-exe.sh:L260–L261](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L260-L261), [docs/zh/desktop-electron-packaging.md:L49–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/desktop-electron-packaging.md#L49-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":219,"path":"scripts/build-electron-exe.sh","sha256":"3fd4aacc5e77318fb6e777a8887c06a60bf36943ea8c9a1beba6f7b307391063","start":214},{"end":261,"path":"scripts/build-electron-exe.sh","sha256":"f1d157ef800cfe889b2a4a32ad61347d4e580c6fd67d1f1917771229f9024c3e","start":260},{"end":51,"path":"docs/zh/desktop-electron-packaging.md","sha256":"cccb6749a064602574eb75a75f45c1637bb062ce4d2882cef94f8a250d95dac2","start":49}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deployment facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a8f84767c157a8ad91dbd418af9f5270d4a4cd23220c2bae4b892566108c1332 -->
**CDP 自绑端口免竞态、不阻塞首屏；代价是 5s 未回读 DevToolsActivePort 即禁用浏览器 sideview**
packaged 版以 --remote-debugging-port=0 让 Chromium 自选端口并回读 DevToolsActivePort：免竞态窗口、不占启动关键路径（旧同步预留端口方案冷启动被杀软拖到数秒且串行阻塞首屏）；代价是文件 5s 未出现即禁用浏览器 sideview。

来源：[docs/zh/desktop-electron-packaging.md:L97–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/desktop-electron-packaging.md#L97-L108)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":108,"path":"docs/zh/desktop-electron-packaging.md","sha256":"e69dae0e60cb5f7244a0381df953976f60e694b945ef35c4a72f10b27726b44f","start":97}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=deployment facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9d5037545da3ca662658478f87ba23d857d6cffa74a29dfbe3bacda14346e740 -->
**ELECTRON_DIR 未设且无候选 Electron.app 目录、或目录内二进制非文件时 exit 1**
ELECTRON_DIR 为空时按 DESKTOP_DIR、PROJECT_ROOT、HOME 下 node_modules/electron/dist/Electron.app 依次取第一个存在目录；结果为空或路径非目录时输出 ERROR 与 npm install/ELECTRON_DIR 提示并 exit 1；目录存在但 $ELECTRON_APP_SOURCE/Contents/MacOS/Electron 非文件时输出含路径的 ERROR 并 exit 1。

来源：[scripts/build-electron-exe.sh:L55–L75](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L55-L75), [scripts/build-electron-exe.sh:L77–L81](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.sh#L77-L81)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":75,"path":"scripts/build-electron-exe.sh","sha256":"88af427364647c3f83a4dfe5f385c86091889e99ec3de04a8378be59b4c76ff9","start":55},{"end":81,"path":"scripts/build-electron-exe.sh","sha256":"ceb871c2e5c9b0f2fb7c99d2f2414aa7b39a61636c671b31d988df230a74d60c","start":77}],"trace":[]} -->
<!-- /kb:depth -->
