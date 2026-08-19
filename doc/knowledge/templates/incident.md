<!-- 模板：incidents/ 目录下的一次复盘 / 历史记录。

     **先读这段：** incident **不是**复盘的默认产物 —— 规则才是。PR/review 学习
     **永远不**创建 incident。其他事故也只有在
     knowledge/contributing/incidents.md#incident-准入门禁 的三项同时成立时才创建；
     任一项为空，就不要建这个文件。

     把本文件**改名**为 YYYY-MM-DD-short-name.md（小写，a-z0-9-）。
     **不带 frontmatter**：incident 属于证据层，check_wiki_lint.py 不检查它们；
     改由 check_knowledge_tree.py 检查下面五个 `- 编号/…` 字段。
     状态 必须是 待归类 / 处理中 / 已验证 / 已提炼 / 仅历史 之一，
     编号 必须在全树唯一。
     在同级 incidents/_index.md 里注册，然后删掉本注释。
     示例：knowledge/repos/vllm-omni/ci/incidents/ -->
# <YYYY-MM-DD> — <人能读懂的现象标题>

- 编号：`inc-<YYYY-MM-DD>-<topic>-<n>`
- 归属：`<repos/<repo>/<topic> | general/<topic>>`
- 状态：<待归类 | 处理中 | 已验证 | 已提炼 | 仅历史>
- 搜索词：<the words someone would actually search for — usually the title>
- 影响范围：<repos/<repo>/<topic>>

**症状**：<what was observed, concretely enough to recognise again>
**根因**：<the verified cause — not the first hypothesis>
**解法**：<what actually fixed it, with the real symbol/file>
**对未来的提醒**：<the generalisable lesson>

## 已提炼的规则

- `<PREFIX>-<id>` in [<owner>/rules.md](../rules.md) — <what the rule now enforces>

<!-- 如果这一节会是空的，说明复盘**还没做完**：先把规则提炼出来。
     不带任何规则往前走的 incident，只是一篇日记。 -->
