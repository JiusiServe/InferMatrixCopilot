---
title: "packaging-deploy"
created: 2026-10-01
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# packaging-deploy

理解该代码 owner 的职责、接口、配置与相关功能时查这里；通用审查方法不属于本目录。
- [打包与部署 功能知识](feature-deployment.md)
- [deploy-observability](deploy-observability/_index.md)
- [deploy-yuanrong](deploy-yuanrong/_index.md)
- [scripts](scripts/_index.md)
- [scripts-nfs](scripts-nfs/_index.md)
- [打包与部署：实现深读](feature-depth-deployment.md)
- [scripts/ — 打包构建与冻结产物校验](scripts.md)
- [NFS 共享工作区脚本 (scripts/nfs/)](scripts-nfs.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：打包、build、exe、dmg、installer、PyInstaller、Electron、HarmonyOS、hap、wheel、frozen bundle、签名公证。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| 打包、build、exe、dmg、installer、PyInstaller、Electron、HarmonyOS、hap、wheel、frozen bund… | 入口 | `scripts/build-electron-exe.ps1`、`scripts/build-electron-exe.sh`、`scripts/build-exe.bat` |
