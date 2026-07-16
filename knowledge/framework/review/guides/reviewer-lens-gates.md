# Reviewer Lens Gates

This file holds workflow gates that are easy to forget when `reviewer_lens_audit.md` gets treated as a generic review checklist.

## Mini spec appendix

Before non-trivial work, write the canonical [mini_spec](../../planning/guides/mini-spec.md). Reviewer-lens can add this appendix, but it cannot replace the canonical mini spec.

Trigger when a change touches:

- new model / pipeline / backend;
- step / graph / cache / batching / serving / offline / benchmark path outside normal `forward()`;
- public API, CLI, `extra_args`, `mm_processor_kwargs`, multimodal key, AR-to-DiT bridge field;
- scheduler, decode, VAE latent, KV/cache, batch expansion semantics;
- performance claims or remote validation evidence.

Appendix fields:

```text
Reviewer-lens appendix
- Changed surfaces:
- Field contract:
  - ingress:
  - default semantics:
  - owner:
  - consumers:
  - failure policy:
- Path parity matrix:
  - normal path:
  - variant paths:
  - shared helper or intentional split:
- Non-default tests:
- Validation and PR evidence:
- Explicit non-goals:
```

If the mini spec cannot be written, do not start coding.

## Risk-classified lens selection

Before any non-trivial review, PR self-audit, or sub-agent delegation, classify the change. Do not assume module-owner + project-owner is sufficient.

```text
Risk tags:
- public API / user-facing contract:
- module semantic contract:
- producer-consumer contract:
- async / concurrency / scheduling:
- resource lifetime / cleanup:
- data format / serialization / IPC:
- performance / benchmark evidence:
- error / cancellation / timeout:
- feature flag / config / default behavior:
- backward compatibility:
- test / validation evidence:
Selected lenses:
```

Lens routing:

- Module semantic contract -> module owner.
- Repo fit, API/config/test/docs/PR evidence -> project owner.
- Async, scheduler, threads, processes, IPC, shared resources, locks, caches, GPU/CPU transfer, pinned memory, background work -> systems/runtime owner.
- Performance, quality, reliability, accuracy, or regression claims -> evidence/benchmark auditor.
- Public API, streaming, request/response schemas -> project owner + contract matrix.

If a required lens is skipped, the final answer must say `partial review` and name the missing lens. Never say `clean`, `ready`, or `fully reviewed` without risk tags and selected lenses.

## Path and lifecycle matrices

For any selected systems/runtime lens, build both matrices before writing findings.

```text
Path matrix
- normal old path:
- normal new path:
- feature disabled:
- feature enabled:
- single caller/request:
- concurrent callers/requests:
- streaming or async event-loop:
- low-resource/offload/constrained mode:
- public/direct caller:
- internal caller:
- error before allocation:
- error after partial allocation:
- consumer timeout:
- cancellation/shutdown:
- test/benchmark path:
```

```text
Resource lifecycle matrix
- resource:
- allocated where:
- owner:
- transferred/stored where:
- consumed where:
- released where:
- allocation failure:
- partial-allocation failure:
- worker/task/thread failure:
- timeout/cancellation/shutdown:
- concurrency bound:
- blocking point:
- evidence/test:
```

Missing rows are findings or explicit evidence gaps; do not silently drop paths because the happy path works.

## Design review before implementation

For runner / prefix cache / shared execution state / pipeline / public API / new model / batching / streaming / multi-module ownership changes, run owner framing before choosing a patch shape:

```text
Role A: module owner. Given the user request and relevant current code, propose
how this module should be changed before implementation. Identify the owning
module/data boundary, required contracts, state matrix, edge cases, and tests.
Return P0/P1 risks in the proposed approach, and name the simplest acceptable
implementation shape. Do not review an already-written patch.

Role B: project/integration owner. Given the user request and relevant current
code, review the intended change at repo level before implementation. Check
whether the change belongs in this module, whether it expands public/internal
surface, whether it needs docs/PR evidence, and what validation matrix protects
other pipelines/backends. Return P0/P1 risks and the smallest repo-aligned plan.
Do not review an already-written patch.
```

Pure typo, formatting, and non-behavior docs edits can skip this gate.

## Committer pre-review

When the user wants "no committer surprises" or you are preparing merge, module-owner review is not enough. Add a project owner / committer framing for:

- public API / `extra_body` / `extra_args` / `mm_processor_kwargs` contract matrix;
- endpoint-layer structured error, not just helper-level exceptions;
- test placement in behavior owner files;
- PR body / Test Plan / Test Result matching current head and current test surface;
- current unresolved / non-outdated reviewer threads.

Module owner says whether the model semantics are right. Committer owner asks whether the public surface, tests, wording, and bad paths can merge.

## Fix closure is not full review

After fixing a sub-agent finding, send the new diff back through the same framing:

```text
Prior findings 是否真的 resolved？
这次修复有没有引入新的 API/test/PR-body surface？
只返回 P0/P1/P2 或 no further findings。
```

Finding closure does not mean full PR clean.

## Full diff review

Run this gate for a full-project review, a large or suspicious diff, the independent review after development, and every pre-push or pre-PR review. First confirm the real target base from the current branch, PR, or user request. Do not assume the default branch is `main` or that the remote is `origin`.

Record the target ref and resolve it once to `<target-base-sha>`; every command in the same review must use that frozen SHA, not the movable ref. If the task provides only an exact baseline SHA and no target ref, record `TARGET REF: n/a` and use that SHA as `<target-base-sha>`. Then resolve one comparison commit:

- If the user or task froze an exact baseline SHA, use that SHA.
- For a feature branch or PR, use `git merge-base <target-base-sha> HEAD` and record the resulting SHA.
- If neither is known, stop and determine the target branch or baseline; do not guess from the current branch name.

For an uncommitted implementation, collect the working-tree surface:

```powershell
git status --short
git diff --stat <comparison-commit>
git diff --name-status <comparison-commit>
git diff --numstat <comparison-commit>
git ls-files --others --exclude-standard
```

`git diff <comparison-commit>` covers committed, staged, and unstaged tracked content relative to that commit, but not untracked files. Every untracked file that belongs to the task must be opened and reviewed in full; unrelated untracked files remain out of scope and must not be silently included or deleted.

For a committed branch or PR with a clean worktree, collect the branch surface:

```powershell
git status --short
git diff --stat <target-base-sha>...HEAD
git diff --name-status <target-base-sha>...HEAD
git diff --numstat <target-base-sha>...HEAD
```

If committed changes and working-tree changes coexist, review `<comparison-commit> -> working tree` first; a `<target-base-sha>...HEAD` review alone is incomplete.

Then run:

1. **Diff census:** top tracked and in-scope untracked files by added lines or file size, owner, why in scope, whether split is possible.
2. **Semantic trace:** every new helper / dataclass / parser / scheduler / docs default traced to public consumer.
3. **Garbage pass:** duplicate logic, tensor-valued `or`, silent fallback, unused knob, docs/perf overclaim, helper-only tests, horizontal misses.

Output must include:

```text
DIFF REVIEW SURFACE: <actual resolved target ref/SHA and comparison commit -> reviewed head or working tree>
TOP FILES REVIEWED: ...
IN-SCOPE UNTRACKED REVIEWED: <file, owner, size/lines, why it belongs>
UNRELATED UNTRACKED EXCLUDED: <file, why it does not belong>
AUDITS RUN: diff-census, semantic-trace, garbage-pass, reviewer-lens-1..4
KNOWN FINDINGS CLOSED != FULL DIFF CLEAN
```

Unless all three passes ran, do not say `full PR reviewed` or `clean`.

## Authoring-time delta audit

When another Codex process, bot, or reviewer can point out multiple issues in a diff I wrote, treat that as authoring-time self-review failure. The issue is not just missing CI and not that the other process is stricter; it means I wrote code without continuously applying the same reviewer lens to the files and behavior surface I was changing.

The retro must answer:

```text
Why did authoring not catch it?
- File/owner surface I failed to enumerate while editing:
- Producer-consumer or semantic/user path I did not trace:
- State matrix / edge / public surface I did not test:
- Test, harness, docs, CI, artifact behavior I treated as secondary:
- Authoring-time guard added so this is caught before another process/user next time:
```

During authoring, run this extra pass as soon as a change touches multi-file UI, provider/serving/runtime bridge, CI/workflow, harness, public wording, or reviewer-follow-up code. Do not wait until the PR is ready.

1. **Changed-file census while editing:** assign every changed file to an owner before adding the next file. Tests, harnesses, workflows, and docs are behavior surfaces, not supporting cleanup.
2. **Producer-to-consumer trace:** trace from the user/public entrypoint to final consumer before implementing the helper-only fix. Include fake/real, success/failure, blocked/running, restart/abort, and stale-state branches that apply.
3. **Reviewer-comment simulation at the line:** for each touched file, ask which exact line another Codex/bot/reviewer would comment on. Focus on mismatched state text, skipped branches, stale docs, tests that do not exercise the changed path, and CI skip logic that hides the risky path.
4. **Guard landing in the same diff:** every real miss must become the nearest test, harness, CI gate, artifact inspection requirement, or explicit manual checklist item before continuing to broaden the patch. A later chat promise is not a guard.

If time is insufficient to run this pass during authoring, report only `implementation draft`; do not say `ready`, `clean`, `fully checked`, or `mergeable`.

## Scope triage for sub-agent findings

Before coding each P0/P1 finding, answer:

- Root cause owner file/function?
- Evidence source: grep, reviewer anchor, test failure, live run?
- Minimal repair files?
- Is it required for the current PR?
- Test owner?

Default conclusion format:

```text
root owner = X; downstream affected = Y; current PR patch = X only; test owner = Z
```

If you cannot write that, do not edit yet.

## Rebase / cherry-pick gate

After rebase, cherry-pick, or conflict resolution, old audits are stale. Review:

- conflict files;
- auto-merged files in touched functions;
- current non-outdated reviewer threads.

Minimum evidence:

```powershell
git range-diff <old-base-sha>...<old-head-sha> <new-base-sha>...HEAD
git diff --stat <new-base-sha>...HEAD
git diff <new-base-sha>...HEAD -- <conflict-or-auto-merged-files>
gh pr view <PR> --json headRefOid
```

Ask whether mainline semantics were overwritten, shared paths got caller-specific rules, or a reviewer "why revert" comment is really pointing at a bug.

## Inline review action mapping

For GitHub inline comments, anchor code is source of truth. Before editing:

```text
Comment: <reviewer 原文>
Anchor: <file:line + 锚点代码实际行为>
Pronoun target: <this / it / here / strategy 指向锚点里的哪个实体>
Reviewer asks: <按锚点语义拆成 1-3 个具体要求>
Code action: <要改哪个 owner/module，什么逻辑从哪里移到哪里>
Done check: <回到锚点附近看 diff，reviewer 是否会认为正面解决>
```

Never fix by keyword alone.
