---
title: "packaging-deploy"
created: 2026-10-01
updated: 2026-10-09
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
- [packaging-deploy：冻结入口、容器与 yuanrong 部署链路](knowledge-packaging-deploy.md)

- [packaging-deploy 审查规则](rules.md) — 解除有兼容性说明的依赖上限前，核对调用方并同步锁文件；分层业务镜像必须保持基础镜像注入与部署身份一致；外部依赖构建参数和可选文件守卫必须分别验证；发行包更名不能连带改写 Python 模块和 CLI 入口。
