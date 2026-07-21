# Extending the knowledge base (`knowledge/`)

A practical guideline for users and developers who want to **add or change a page**
in the curated Markdown wiki at repo-root `knowledge/`.

`knowledge/` is a **vendored** copy of `zuiho-kai/claude-workflow-starter`
(provenance and copy authorization in [KNOWLEDGE.md](KNOWLEDGE.md)); it is
maintained in-repo as ordinary tracked files. The wiki's own short entry point is
[`knowledge/CONTRIBUTING.md`](../knowledge/CONTRIBUTING.md), which routes to one
topic page in [`knowledge/contributing/`](../knowledge/contributing/) per action —
read it when you need the authoritative rule. **This guide adds copy-paste
templates and a decision tree on top of that**, plus how the copilot actually
*consumes* the wiki so you know what to keep tight.

> The same workflow is distilled into a retrievable skill,
> [`skills/knowledge-base-contribution/SKILL.md`](../skills/knowledge-base-contribution/SKILL.md),
> so the copilot's own agents follow it during retrospectives.

---

## 0. TL;DR — the four-step loop

1. **Pick the owner directory** (§1). Route by the *verified root cause*, never by
   where the symptom first showed.
2. **Write/edit one page** of the right type (rules / architecture / guide /
   incident). Keep exactly **one canonical copy** of each fact; everything else
   links to it.
3. **Register it in the same change**: add a `遇到什么 → 查看哪里` row (or a
   child-dir link) in the **nearest `_index.md`**. An unregistered page fails the gate.
4. **Validate** (both gates must print 0 errors):

   ```bash
   python knowledge/tools/check_knowledge_tree.py    # structure / index / links / incidents
   python knowledge/tools/check_wiki_lint.py         # synthesis-layer frontmatter + tag taxonomy
   ```

Deliver via PR (the wiki gate runs in review); never direct-push. See §5.

---

## 1. Where does it go? — the owner decision tree

### Layer 1 — general vs repo-specific

| The lesson is… | Put it under |
|---|---|
| True on **any** repo (review, ci, debug, git, planning, remote, docs, benchmark, agents, environment) | `knowledge/general/<topic>/` |
| Specific to **one repo** | `knowledge/repos/<repo>/` |
| A **current-machine** fact (host, path, account, cache, venv, token) | `knowledge/local/` — git-ignored, never tracked |

### Layer 2 — inside a repo slice

| The lesson is about… | Put it under |
|---|---|
| A repo-wide workflow topic (review, ci, git, benchmark, remote, rebase…) | `repos/<repo>/<topic>/` |
| **Shared source code** used by several models (diffusion, scheduler, serving…) | `repos/<repo>/components/<module>/` |
| **One model's** own implementation / config / checkpoint | `repos/<repo>/models/<model>/` |

Route by the **verified** root cause. "Frontend saw a 404" does not mean the root
cause lives in frontend — sink the page where the cause was proven, not where the
symptom appeared.

### Layer 3 — which page type

| You have… | Page type | Notes |
|---|---|---|
| A rule that must change the **next** run (trigger → do → don't → how to verify) | `rules.md` in the nearest owner dir | The default product of a retrospective. Always-on (see §2) — keep it tight. |
| A **stable** data-flow / responsibility / boundary description | `architecture.md` | No title-only stubs. |
| A longer method that isn't a hard gate | a page in `guides/` | Pulled on demand, so depth is welcome here. |
| **Complex reproducible history** a rule can't carry | `incidents/YYYY-MM-DD-short-name.md` | Optional. Only when the repro chain / evidence still has independent lookup value. |

**Retrospective rule of thumb:** the default output of "复盘 / record a lesson" is a
**rule**, not an incident. Add an incident only when the evidence chain is complex
enough that the rule alone can't carry it.

---

## 2. How the copilot consumes it (so you know what to optimize)

Wiring lives in `src/omni_copilot/engine/agent_runtime/knowledge.py` +
`src/omni_copilot/config.py` + each `adapters/<repo>/manifest.yaml`.

- **Always-on briefing** — injected into *every* run, each capped:
  - the general slice `settings.knowledge_general_docs` (`general/_index.md`);
  - the adapter's `briefing_docs` — for vllm-omni: `repos/vllm-omni/rules.md` +
    `repos/vllm-omni/_index.md`;
  - `performance_briefing_docs` for strong models (compact review patterns).
- **On demand** — the `doc_search` / `doc_read` tools reach every deeper `guides/`,
  `incidents/`, `components/`, and `models/` page in `general/` **plus the active
  adapter's `repo_subdir` only** (other repos' slices are refused; path traversal
  is blocked; `doc_read` windows 24k chars and pages with an offset).
- **MCP** — the same repo-scoped `doc_search` / `doc_read` are exposed read-only
  over MCP, so a host model can query the wiki without starting a run.

**Practical implication for authors:** `rules.md` and `_index.md` are *budget* —
they load on every task. Keep them to triggers + gates + navigation. Push
narrative, long repros, and step-by-step method into `guides/` / `incidents/`,
which are pulled only when a run actually needs them.

To register a **new repo's** slice, point its adapter manifest at it
(`knowledge.repo_subdir`, `briefing_docs`, `performance_briefing_docs`) — see §3.8.

---

## 3. Templates (copy-paste)

**Ready-to-copy files live in [`knowledge-templates/`](knowledge-templates/)** (see
its [README](knowledge-templates/README.md) for the copy → register → validate
recipe) — `cp` one into place instead of retyping the blocks below. The blocks
here are the same skeletons, inline for reading in context.

All templates are gate-valid once you (a) replace placeholders and (b) register
the page in the nearest `_index.md`. **Frontmatter is required on synthesis-layer
pages** — `rule` / `guide` / `architecture` / `index` under `general/` and
`repos/` — and enforced by `knowledge/tools/check_wiki_lint.py`: it needs `title`,
`created` + `updated` (both `YYYY-MM-DD`), `type` (one of those four), and a
non-empty `tags` list drawn from the taxonomy in
[`knowledge/SCHEMA.md`](../knowledge/SCHEMA.md) (`## 标签分类法`); `confidence`, if
present, must be `high|medium|low`. **Evidence-layer pages** (`incidents/`,
`history/`, `results/`) take **no** frontmatter — the incident template uses plain
`- 编号/…` fields instead (checked by `check_knowledge_tree.py`). Directory names
use lowercase
`a-z0-9-`; `_index`, `local`, `components`, `models`, `incidents`, `guides` are
reserved role names — don't reuse them as custom topics.

### 3.1 `_index.md` — any topic / directory (the required routing table)

```markdown
---
title: "<Human title>"
created: 2026-07-20
updated: 2026-07-20
type: index
tags: [<repo-or-topic>]
sources: []
---

# <Human title>

## 什么时候查这里

- <one line: when a task should open this directory>

## 不放什么

- <what belongs elsewhere> → `<other/owner/path>`

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| <symptom / task> | [<page>](<page>.md) | <one-line scope> |
| <deeper history> | [incidents](incidents/_index.md) | optional |
```

Every non-index page and every child directory in this folder **must** appear
exactly once as a link in this table (that link is what the gate checks).

### 3.2 `_index.md` — a **repo** entry (`repos/<repo>/_index.md`)

Same as 3.1, plus an identity header before the tables:

```markdown
# <Repo display name>

- 上游仓库：`<owner>/<repo>`
- 常用分支：默认分支 `<main>`；<other branches>
- 适用范围：<what work this slice covers>
- 组件源码映射已按 `<repo> main @ <sha>` 校验

## 什么时候查这里
- 当前 Git 仓库或用户明确目标是 <repo>。

## 不放什么
- 跨仓库通用方法（放 `general/`）；其他仓库的规则。

## 当前入口
| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 开始任何 <repo> 修改、测试、发布任务 | [硬门禁](rules.md) | 仓库硬规则 |
| 查看共享代码模块 | [components](components/_index.md) | 模块职责地图 |
| 查看某个模型 | [models](models/_index.md) | 模型入口 |
```

### 3.3 `_index.md` — a **component** or **model** (extra required fields)

Component `components/<module>/_index.md` must additionally list: the source
paths it owns, its responsibility / IO boundary, its test entry, and which
models/features it affects. Model `models/<model>/_index.md` must additionally
list: canonical name + aliases, source paths, which shared components it depends
on, and how checkpoints/sizes/quantizations differ.

### 3.4 `rules.md` — the always-on gate page

```markdown
---
title: "<Owner> 硬门禁"
created: 2026-07-20
updated: 2026-07-20
type: rule
tags: [<repo-or-topic>]
sources: []
---

# <Owner> 硬门禁

只在当前任务明确属于 <owner> 时应用本页。先遵守根 `CLAUDE.md` 的通用 P0。

## 场景触发器

| 用户提到 | 必读 | 硬约束 |
|---|---|---|
| <trigger phrase> | [<guide>](guides/<guide>.md) | <what MUST/ MUST-NOT happen + how to verify> |

## 规则（每条给稳定 ID）

### <RULE-ID> <short name>
- 触发：<when this applies>
- 必须：<the required action>
- 禁止：<the forbidden action>
- 验收：<the exact check proving compliance>
```

Give every independent, auditable constraint a **stable ID** (e.g. `HY3-2c`).
One ID = one behavioral invariant. Keep rules readable without knowing any
incident number. Don't pre-create an empty `rules.md`; create it when the first
rule exists and link it from the sibling `_index.md`.

### 3.5 `architecture.md` — stable boundaries (no title-only stubs)

Synthesis-layer, so it needs frontmatter (`type: architecture`). Component variant:

```markdown
---
title: "<Module> 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [<tag-from-SCHEMA.md>]
sources: []
---

# <Module> 架构

## 职责和边界
## 主要源码和调用入口
## 数据怎样流动
## 怎样验证
```

Model variant (same frontmatter, `type: architecture`):

```markdown
# <Model> 架构

## 模型专有部分与共享模块的边界
## 配置、checkpoint 和兼容范围
## 从输入到输出的主要流程
## 怎样验证功能、精度和性能
```

### 3.6 An ordinary `guides/` page

```markdown
---
title: "<Guide title>"
created: 2026-07-20
updated: 2026-07-20
type: guide
tags: [<repo-or-topic>]
sources: []
---

# <Guide title>

## 什么时候用
- <trigger>

## 步骤 / 方法
1. <step, with the file:line or command it touches>

## 怎样验证
- <the check that proves it worked>
```

Then add a row for it in the sibling `guides/_index.md`.

### 3.7 An `incidents/` page (validator-checked fields)

File name **must** match `YYYY-MM-DD-short-name.md`. The body must contain these
exact field labels, and the state must be one of
`待归类 / 处理中 / 已验证 / 已提炼 / 仅历史`. The `编号` must be unique across the tree.

```markdown
# <人能读懂的现象标题>

- 编号：`inc-2026-07-20-short-name`
- 归属：`repos/<repo>/<topic>`
- 状态：处理中
- 搜索词：<term1>、<term2>、<term3>
- 影响范围：<what breaks>

## 现象
## 根因（live 证据）
## 修复
## 验收
## 已提炼的规则
- 见 [<owner> rules](../rules.md#<rule-id>)
```

One incident = one canonical write-up; other places link to it. Normal work still
starts from rules, never from an incident path.

### 3.8 Onboarding a **new repo** slice

1. Create the wiki skeleton and register each level up the chain:

   ```text
   knowledge/repos/<repo>/_index.md      # from template 3.2
   knowledge/repos/<repo>/rules.md       # only if a real per-repo gate exists
   # add a row for <repo> in knowledge/repos/_index.md
   ```

2. Point the adapter at the slice (`adapters/<repo>/manifest.yaml`):

   ```yaml
   knowledge:
     repo_subdir: repos/<repo>              # its slice under knowledge/
     briefing_docs:                          # always-on: keep tiny
     - repos/<repo>/rules.md
     - repos/<repo>/_index.md
     performance_briefing_docs:              # optional, strong-model only
     - repos/<repo>/review/guides/<patterns>.md
   ```

3. If you forked the wiki from upstream, delete the `repos/` slices that aren't
   yours and update `repos/_index.md` accordingly.

---

## 4. Gate cheat-sheet — what the two gates enforce

`check_knowledge_tree.py` (structure) and `check_wiki_lint.py` (frontmatter/schema)
both run in review; both must be clean.

| Check | Gate | Rule |
|---|---|---|
| Index present | tree | Every directory containing Markdown has an `_index.md`. |
| Registration | tree | Every non-index page **and** every child dir is linked **exactly once** from the nearest `_index.md`. |
| Links | tree | Relative links must resolve; absolute paths are rejected. |
| Size | tree | Warn at ≥300 non-empty lines or 16 KiB; **must split** at ≥500 lines or 32 KiB (or note `暂不拆分` + a review date in the index). |
| Directory fan-out | tree | Non-group dir warns above 7 ordinary pages; group dirs (`guides` `incidents` `history` `references` `results` `rfcs`) hard-fail above 20. |
| Incident format | tree | `YYYY-MM-DD-short-name.md` + the five `- 编号/归属/状态/搜索词/影响范围` fields + a valid state + a unique 编号. |
| Privacy | tree | No real IPv4, Windows `C:\Users\…`, remote user home, or private-key blocks in tracked pages. |
| Safety | tree | No `StrictHostKeyChecking=no`, global `safe.directory *`, `--gpus all`, `pkill`, `rm -rf`, or `find … -exec rm`. |
| `local/` | tree | Must stay git-ignored (untracked). |
| Root entry | tree | `knowledge/CONTRIBUTING.md` stays ≤100 non-empty lines / ≤8 KiB (detail sinks into `contributing/`). |
| Frontmatter | lint | Synthesis pages (`rule/guide/architecture/index` in `general/`+`repos/`) need `title`, `created`+`updated` (`YYYY-MM-DD`), `type` (those four), non-empty `tags`; optional `confidence: high\|medium\|low`. |
| Tag taxonomy | lint | Every `tags` value must appear in `SCHEMA.md`'s `## 标签分类法`. |
| Evidence layer | lint | `incidents/` `history/` `results/` pages are **not** frontmatter-checked (they use the plain incident fields). |
| Adapter briefings | lint | `manifest.yaml` `knowledge:` allows only `source`/`repo_subdir`/`briefing_docs`/`performance_briefing_docs`, and briefing docs must not point at evidence-layer pages. |

`rules.md`, `architecture.md`, `_index.md` are "special" pages and don't count
toward the 7-page fan-out warning.

---

## 5. Delivery

- Edit `knowledge/` in place like any tracked content; ship via **PR**. The wiki
  gate runs in review — don't direct-push to a protected branch.
- The tree is **vendored** — never edit upstream. To pull a future upstream page,
  diff against `zuiho-kai/claude-workflow-starter` and import the specific pages
  deliberately (there is no submodule link).
- Machine facts (host, path, account, token, cache, venv) go **only** in the
  git-ignored `knowledge/local/`; keep tracked pages free of them (the gate
  enforces this, but check before you commit anyway).

---

## 6. The retrieval skill

[`skills/knowledge-base-contribution/SKILL.md`](../skills/knowledge-base-contribution/SKILL.md)
encodes this workflow for the copilot's own agents (owner routing, page-type
choice, `_index.md` registration, always-on tightness, and the validator). It is
retrieved via `skill_search` and surfaces during retrospectives when an agent is
told to record a lesson. Update it in the same PR whenever this guideline changes.
