# knowledge_view.py —— 规范

<!-- verified-against: 2026-09-28 -->

`LOC ~170 · 每请求的知识树视图（打包知识或激活快照） · refactor-status: stable`

## 职责
为每个请求解析**一个**知识根，并让本请求内所有读取经过它。知识服务通过原子
切换符号链接激活新快照；导入期常量会一直服务旧树（包括已退役规则）直到进程
重启，因此视图必须在请求开始时解析。

## 公开契约
- `KnowledgeView.current()`：`KNOWLEDGE_ROOT` 未设置 → 打包知识，
  `snapshot="packaged"`；已设置 → 对其 `realpath` **只取一次**。含
  `MANIFEST.json` 的目录是激活快照，根为其 `knowledge/`；只含 `AGENTS.md` 的
  目录作为开发用未校验树（`snapshot="unverified:<path>"`）；其余 fail-closed。
- `view.path(rel)` / `view.read_text(rel)`：拒绝逃逸与缺失；快照模式下文件必须
  在清单中且 sha256 一致，否则抛 `KnowledgeViewError`。
- `view.relative(path)`：绝对路径 → 知识相对 id。
- `build_manifest(root, snapshot)`：生成 schema_version 1 清单
  （`files` 逐文件 sha256、`tree_sha256`）。

## 不变量
- 一个请求不混用两棵树：解析后使用真实目录，不再经过符号链接。
- 快照首次加载时校验：磁盘文件集合与清单完全一致、`tree_sha256` 与文件列表
  一致；每次读取再校验单文件 sha256。
- 快照不可变，因此按解析后的目录缓存加载结果是安全的：新激活是另一个目录。

## 依赖（允许）
stdlib + `.sdk._resources`。叶子模块。

## 测试
`test_knowledge_view_routing.py`。
