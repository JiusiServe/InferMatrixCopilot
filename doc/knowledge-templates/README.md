# Knowledge-base page templates

Ready-to-copy skeletons for the curated wiki at repo-root `knowledge/`. Full
workflow, decision tree, and gate rules: [`../EXTENDING-KNOWLEDGE.md`](../EXTENDING-KNOWLEDGE.md).

These files live **outside** `knowledge/`, so they don't run through the wiki gate
(their placeholders would otherwise fail it). Copy one into the right owner
directory, fill in the `<...>` placeholders, delete the leading `<!-- TEMPLATE -->`
comment, register the page in the nearest `_index.md`, then validate.

## Which file for what

| Copy this | To create | Into |
|---|---|---|
| [`_index.md`](_index.md) | a directory's routing table | any new topic/component/model dir |
| [`repo-index.md`](repo-index.md) | a **repo** entry index | `knowledge/repos/<repo>/_index.md` |
| [`rules.md`](rules.md) | an always-on gate page | nearest owner dir |
| [`architecture-component.md`](architecture-component.md) | a shared-module architecture page | `repos/<repo>/components/<module>/architecture.md` |
| [`architecture-model.md`](architecture-model.md) | a model architecture page | `repos/<repo>/models/<model>/architecture.md` |
| [`guide.md`](guide.md) | a method/how-to page | a `guides/` dir |
| [`incident.md`](incident.md) | a retro / historical write-up | an `incidents/` dir — **rename to `YYYY-MM-DD-short-name.md`** |

## Copy + register + validate

```bash
# 1. copy (example: a new component page)
cp doc/knowledge-templates/architecture-component.md \
   knowledge/repos/vllm-omni/components/<module>/architecture.md

# 2. edit it: fill <...>, delete the <!-- TEMPLATE --> line
# 3. add a row for it in the sibling _index.md  (遇到什么 → 查看哪里)
# 4. validate — both must print 0 errors
python knowledge/tools/check_knowledge_tree.py    # structure / index / links / incidents
python knowledge/tools/check_wiki_lint.py         # synthesis-layer frontmatter + tag taxonomy
```

Reminders the gates enforce: every non-index page and child dir is linked
**exactly once** from the nearest `_index.md`; relative links must resolve; no real
host/IP/user-path/token/key in tracked pages (those go in git-ignored `local/`);
split a page at ≥500 non-empty lines or 32 KiB. Synthesis-layer pages
(`rule/guide/architecture/index` under `general/`+`repos/`) need frontmatter with a
`tags` value from [`SCHEMA.md`](../../knowledge/SCHEMA.md); the incident template is
evidence-layer and takes none. Deliver via PR — the tree is vendored; never edit
upstream.
