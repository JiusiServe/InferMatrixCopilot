# Reviewer Lens Prompt

Use this when spawning a read-only review sub-agent. Do not add a suspected root cause unless the task is explicitly finding-closure for an already accepted finding.

正常独立审查先执行 [review execution contract](review-execution-contract.md)，并使用其固定 Markdown 报告和检查脚本。本页是需要完整风险 lens 或专项 owner prompt 时才追加的详细 prompt；只返回本页末尾两行、不交付执行合同中的两张矩阵，仍是 partial review。

```text
Static review this PR/diff/change. Do not stop after the first valid finding.
First classify the change by risk type, then audit every selected risk type.

Scope stop: once the frozen base, complete diff including in-scope untracked
files, and owner chain are verified, stop navigation. Do not recursively read
unrelated owners, incidents, or history. Read contribution/layout rules only
when the diff changes the knowledge tree. Add each additional owner only when
the live producer-consumer trace crosses that boundary.

For every owner in that proven chain, read its existing rules.md if present.
Inventory every stable constraint ID and mark each PASS / FAIL /
MISSING_EVIDENCE / NOT_APPLICABLE with file/function/test/run evidence. N/A
also needs evidence; omission cannot produce a clean result. Group/namespace
headings do not count as IDs. For an ID with a fixed evidence matrix, report
every row; one missing row prevents PASS. When an old rules
page has no stable sub-IDs, treat each bullet or prose paragraph as one source
unit, quote it, and list every normative requirement you identify inside it.
Report that page as legacy-unstructured; do not claim exact clause coverage or
try to infer cardinality from keywords. If the current diff materially edits
that rule, require stable IDs under the contribution rules. If no owner rules.md exists, write
"OWNER RULES: none" and continue. Do not search incidents/history to invent
hidden rules. Novel findings do not offset a missed owner invariant.

Return all matching risk tags with one file/function evidence each:
- public API / user-facing contract
- module semantic contract
- cross-module producer-consumer contract
- async / concurrency / scheduling
- resource lifetime / cleanup
- data format / serialization / IPC
- performance claim / benchmark evidence
- error handling / cancellation / timeout
- feature flag / config / default behavior
- backward compatibility
- test or validation evidence

Then list selected review lenses. For EACH of the four base audits below,
return findings (P0 blocker / P1 should-fix / P2 low-severity substantive issue)
OR explicitly write
"none found" — do not skip any audit and do not pre-focus on one over another.

Pure style preferences that do not affect behavior, maintainability, contract,
or evidence are `nit`, not P2, and do not block a clean verdict.

# Audit 1 — Duplication
Grep both the repo (project source dirs, scripts, tests, docs as applicable) and
any upstream/reference implementation for functions / classes / algorithms /
constants that overlap with anything new in this PR. List each match with:
  - file:line of the existing implementation
  - file:line of the new implementation
  - 1-line judgment: should reuse / cannot reuse + why

# Audit 2 — Layering
For each new piece of logic, identify which module persistently holds the data
it operates on. If logic and data live in different modules, list:
  - new logic location
  - data owner location
  - proposed correct home

# Audit 3 — Edge cases
List every range / boundary / default value the new code touches. For each,
name which branches handle:
  - empty / single-element / max-size extremes
  - non-contiguous ID ranges, off-by-one
  - None vs 0 vs sentinel
  - feature-flag matrix and old/new execution modes
Flag any boundary not explicitly handled.
For every added or changed selector, filter, guard, or routing predicate, verify
through the same public or production entry point at least one case that should
enter and one that should not enter, including each observable result. Flag a
test suite that still passes when the selected behavior is disabled entirely.

# Audit 4 — Surface area
List every new public knob (CLI arg / API field / extra_args key / config
option / public function / SSE or OpenAI-compatible response chunk). For each:
  - If this is a request parameter, extra_body/extra_args key, processor kwarg,
    multimodal key, or cross-module bridge field, provide a contract matrix:
    ingress path(s), allowed value shapes, normalization point, owner module,
    downstream consumer(s), no-op cases, docs, and tests.
  - Can it be derived from existing knobs? If yes, why expose it?
  - Why is the default what it is? Can the help text be shorter?
  - Is the same value also expressible via another path?
  - If this is a public API field or response schema, where is the protocol type
    defined, where is it documented, and what bad-path tests cover it?
  - If this is streaming/SSE/WebSocket, which existing endpoint pattern and
    output-processor mechanism does it reuse?
  - If this is an internal optional fast-path parameter, what are its data
    contract and execution-context contract, and where does a wrong caller fail?
  - If this changes a shared state/schema type, list every constructor, unpack
    site, and consumer found by grep, and state how positional arity remains
    compatible.
Flag knobs that are accreted/over-defensive.

# Conditional audit — Public ingress and producer-consumer behavior
Run this for public API, CLI/example, multimodal input, request normalization,
or cross-stage handoff changes. Enumerate every live public/internal ingress
that reaches the changed consumer. For each ingress, state where validation
happens and whether it is before file/network load, decode, allocation, or GPU
work. Then trace each changed value from producer through every transformation
to its final consumer, stop/truncation boundary, and failure owner. A field
being present in a downstream dict is not evidence that behavior is aligned.
Flag untested or bypassing ingress paths as findings.

# Conditional audit — Path matrix
Run this when the change touches execution flow, feature flags, public contracts,
runtime behavior, async/concurrency, resources, or performance. For each
applicable path, provide checked evidence or "missing":
  - normal old path
  - normal new path
  - feature disabled
  - feature enabled
  - single request / single caller
  - concurrent requests / multiple callers
  - streaming or async event-loop path
  - low-resource / offload / constrained mode
  - public/direct caller and internal caller
  - test/benchmark path
Flag paths that only work on the happy path.

# Conditional audit — Resource lifecycle
Run this when the change allocates or passes files, memory, shared memory,
sockets, threads, tasks, processes, GPU buffers, pinned memory, locks, caches,
temp dirs, handles, or background work. For each resource, list:
  - allocated where
  - owner
  - passed to whom
  - consumed where
  - released where
  - allocation-failure behavior
  - failure-after-partial-allocation behavior
  - timeout/cancellation/shutdown behavior
  - concurrency bound
  - blocking point
  - test or evidence
Flag leaks, unbounded work, blocked event loops, swallowed failures, and
consumer hangs.

# Conditional audit — Evidence / benchmark
Run this when the change claims performance, quality, reliability, accuracy,
compatibility, or regression safety. Verify:
  - baseline and current runs are same hardware/input/config
  - warmup/compile/cold-start are separated
  - concurrency/request rate matches the claim
  - metric definition and sample count are clear
  - mean/median/stddev or repeated runs are sufficient for the claim
  - quality/accuracy/VRAM/resource regressions are ruled out
  - PR body evidence matches current head
  - screenshots are not the only proof
Flag unproven claims as findings.

Return findings in markdown. For each finding, first state:
1. what bad thing can happen;
2. why this PR owns it;
3. the smallest acceptable fix.
End with:
"OWNER RULE COVERAGE: <path or none>: X/Y stable IDs inventoried — A pass / B fail / C missing evidence / D not applicable" or "OWNER RULE COVERAGE: <legacy path>: X source units inventoried — A pass / B fail / C missing evidence / D not applicable — legacy-unstructured, no exact clause-coverage claim" (one line per owner), then
"RISK TAGS: ...; LENSES: ..." and then on a separate line "AUDITS RUN: coverage,ingress,producer-consumer,duplication,layering,edge-cases,surface-area[,path,lifecycle,evidence] — N findings (Pa P0, Pb P1, Pc P2)".
```

## Owner prompts

New model / pipeline / backend work needs two owner framings before the first public push:

```text
Role A: module owner. Review semantic parity against upstream. Treat shape-clean
and strict load as weak evidence. Check scheduler / denoising loop, embedding
order, activation, token order, special token + pad/eos attention mask,
preprocess, noise/action contracts, and real-checkpoint fail-fast behavior.
Return P0/P1/P2 findings only.

Role B: project/integration owner. Review whether this integration matches the
repository architecture. Check file/module ownership, public API surface, test
placement, stub-vs-real evidence separation, PR body reproducibility, and
whether any generic helper leaks caller-specific semantics. Return P0/P1/P2
findings only.
```

Rule: Role A answers "does it preserve the module/domain semantics"; Role B
answers "does it fit the project". Either side looking only at shape / smoke is
not enough.

## Specialist owner prompts

Add these when risk tags require them. Do not replace Role A/B unless the change
is purely in that specialty.

```text
Role C: systems / runtime owner. Review resource lifetime, concurrency, failure
propagation, blocking behavior, thread/process/task boundaries, IPC or
serialization, GPU/CPU transfer, scheduler/event-loop impact, locks, caches,
and cleanup. Build a lifecycle table for every resource and a path matrix for
normal, disabled, concurrent, error, timeout, cancellation, and shutdown paths.
Return P0/P1/P2 findings only with file/function evidence.

Role D: evidence / benchmark auditor. Review whether the PR evidence proves the
claim. Check baseline parity, workload/config/request propagation, warmup or
compile exclusion, concurrency/request-rate semantics, sample count, mean/stddev,
quality/accuracy/VRAM/resource regressions, artifact provenance, and current-head
PR-body consistency. Return P0/P1/P2 findings only with concrete missing evidence.
```
