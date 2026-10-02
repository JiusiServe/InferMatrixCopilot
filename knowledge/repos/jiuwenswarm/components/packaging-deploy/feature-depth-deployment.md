---
title: "打包与部署：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L144-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:Dockerfile.claw:L78-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L55-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:scripts/build-electron-exe.sh:L301-L307]
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
