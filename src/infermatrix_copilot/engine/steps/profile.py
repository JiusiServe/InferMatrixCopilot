"""Profile establishment + Stage-4 maintenance steps (doc/DESIGN.md §V2.3.3).
Read-only toward the TARGET repo; writes land only under adapters/<repo>/
(knowledge risk, curator/human-gated downstream):

- profile.fingerprint    Stage 0: deterministic fingerprint; draft adapter for
                         unknown repos (stops at `status: draft` — human gate)
- profile.structure_scan Stage 0: deterministic module draft into manifest.yaml
- profile.ingest_docs    Stage 1.5 input: existing AGENTS.md/CLAUDE.md et al.
                         ingested as human-authored briefing facts
- agent.profile_repo     Stage 1: governed agent derives non-obvious facts
- profile.detect_drift / decay_stale / consolidate / judge  Stage 4 maintenance
"""

from __future__ import annotations

from pathlib import Path

from ...adapters.base import (AdapterRegistry, RepoAdapter, draft_adapter,
                            fingerprint_repo, load_adapter, update_manifest)
from ...profiles.establish import (HUMAN_DOC_NAMES, build_doc_corpus,
                                  extract_directives, fact_id, is_redundant,
                                  scan_modules)
from ...profiles.store import ProfileStore
from ..step import FailureKind, StepContext, StepResult
from ._common import no_llm_gap
from ._common import repo_path as _repo_path
from ._common import step


def _adapter_from_state(ctx: StepContext) -> RepoAdapter | StepResult:
    """Load the RepoAdapter from the `adapter_root` that `profile.fingerprint`
    published to state. Returns a BLOCKED StepResult when no `adapter_root` is set
    (fingerprint must run first) — every Stage-1/Stage-4 step guards on this."""
    root = ctx.state.get("adapter_root")
    if not root:
        return StepResult(False, FailureKind.BLOCKED,
                          "no adapter_root in state — run profile.fingerprint first")
    return load_adapter(root)


@step("profile.fingerprint", "deterministic", "knowledge",
      "Stage 0: deterministic repo fingerprint; draft adapter for unknown "
      "repos (stops at status: draft).")
async def _fingerprint(ctx: StepContext) -> StepResult:
    """Stage 0: deterministically fingerprint the target repo and ensure a adapter
    exists for it. Resolves the adapter from the registry by repo path; for an
    unknown repo, drafts one (which stops at `status: draft` — a human gate before
    it is trusted). A missing repo checkout is BLOCKED.

    Publishes `adapter_root` and `repo_language` to state (B2 `state_updates`) so
    the later profile stages can load the adapter; records `profile_fingerprint`
    in the trace."""
    repo = _repo_path(ctx)
    if repo is None or not repo.exists():
        return StepResult(False, FailureKind.BLOCKED,
                          f"repo checkout not configured (repo_path={repo})")
    fp = fingerprint_repo(repo)
    registry = AdapterRegistry(ctx.settings.adapters_dir)
    adapter = registry.resolve(repo_path=str(repo))
    created = False
    if adapter is None:
        adapter = load_adapter(draft_adapter(fp, ctx.settings.adapters_dir))
        created = True
    updates = {"adapter_root": str(adapter.root),
               "repo_language": fp["language"]}
    ctx.state.update(updates)
    ctx.trace.record("profile_fingerprint", adapter=adapter.name,
                     created=created, language=fp["language"])
    return StepResult(True,
                      summary=f"adapter '{adapter.name}' "
                              f"({'drafted' if created else adapter.status}), "
                              f"language={fp['language']}",
                      outputs={"fingerprint": fp, "adapter": adapter.name,
                               "created": created, "state_updates": updates})


@step("profile.structure_scan", "deterministic", "knowledge",
      "Stage 0: deterministic module draft into manifest.yaml (never overwrites "
      "declared modules).")
async def _structure_scan(ctx: StepContext) -> StepResult:
    """Stage 0: deterministically draft the repo's module list into manifest.yaml.
    Non-destructive — if the adapter already declares modules, they are kept as-is;
    otherwise `scan_modules` (by repo path + language) proposes candidates and
    `update_manifest` writes them (actor="agent"). No candidates found is a
    non-failure (left for the profiling agent or a human)."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    if adapter.modules:
        return StepResult(True, summary=f"modules already declared "
                                        f"({len(adapter.modules)}) — kept as-is")
    repo = Path(adapter.repo_path or ctx.state.get("repo_path", ""))
    language = str(ctx.state.get("repo_language")
                   or adapter.manifest.get("repo", {}).get("language") or "")
    modules = scan_modules(repo, language)
    if not modules:
        return StepResult(True, summary="no module candidates found "
                                        "(left for the profiling agent/human)")
    update_manifest(adapter, "modules", modules, actor="agent")
    ctx.trace.record("profile_modules_draft", modules=sorted(modules))
    return StepResult(True,
                      summary=f"module draft written ({sorted(modules)})",
                      outputs={"modules": modules})


@step("profile.ingest_docs", "deterministic", "knowledge",
      "Ingest AGENTS.md/CLAUDE.md-style human directives as briefing facts "
      "(doc-redundant lines dropped).")
async def _ingest_docs(ctx: StepContext) -> StepResult:
    """Stage 1.5: ingest human-authored directives from AGENTS.md/CLAUDE.md-style
    docs (`HUMAN_DOC_NAMES`) as `briefing`-channel, source=human profile facts.
    Directives already implied by the doc corpus (`is_redundant`) are dropped, and
    the set is capped at 20 to keep the briefing minimal (the budget trims the
    rest anyway). Applies the facts via typed `add_fact` ops to the ProfileStore;
    records counts in the trace."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    repo = Path(adapter.repo_path or ctx.state.get("repo_path", ""))
    corpus = build_doc_corpus(repo)
    store = ProfileStore(adapter.profile_dir)
    ops: list[dict] = []
    dropped = 0
    for name in HUMAN_DOC_NAMES:
        path = repo / name
        if not path.exists():
            continue
        for text in extract_directives(
                path.read_text(encoding="utf-8", errors="replace")):
            if is_redundant(text, corpus):
                dropped += 1
                continue
            ops.append({"op": "add_fact", "id": fact_id("doc", text),
                        "module": "repo-wide", "kind": "convention",
                        "channel": "briefing", "text": text,
                        "source": "human", "evidence": [name]})
    ops = ops[:20]  # briefing stays minimal; the budget trims the rest anyway
    applied = store.apply_ops(ops).count("") if ops else 0
    ctx.trace.record("profile_docs_ingested", applied=applied,
                     redundant_dropped=dropped)
    return StepResult(True,
                      summary=f"{applied} human directive(s) ingested, "
                              f"{dropped} doc-redundant dropped",
                      outputs={"applied": applied, "dropped": dropped})


_PROFILE_GUIDANCE = """You are profiling a repository so a maintenance copilot \
can work on it well. Derive the NON-OBVIOUS residue only — facts a competent \
agent would NOT discover by reading the README (which it always reads anyway). \
Auto-generated overviews measurably hurt agents; directory listings and \
project descriptions are FORBIDDEN outputs.

Hunt for, in priority order:
1. Exact tooling commands: how to run the checks that gate a merge (formatter,
   linter, test runner, type checker, pre-commit) with their real flags —
   verify each command exists in the config files before claiming it.
2. Hard constraints: protected branches, paths that must never be edited,
   license headers, commit/PR conventions actually enforced.
3. Traps: version pins that break when bumped, tests that need hardware or
   credentials, known-flaky suites, ordering requirements.
4. Conventions the code follows but no doc states (naming, error handling,
   import style) — cite the files you inferred them from.

Every fact MUST cite its evidence (the file you read or command you ran, and
what it showed) — facts without evidence are rejected by the store. Choose the
channel honestly: `briefing` only for directives every task needs (budget is
tight), `machine` for commands steps should run, `retrieved` for the rest.
Emit at most 15 facts. Also emit review_checklist lines ONLY for repo-specific
review concerns a generic checklist would miss (empty list is a fine answer)."""


@step("agent.profile_repo", "agent", "knowledge",
      "Stage 1: governed agent derives non-obvious, evidence-cited profile "
      "facts; redundancy-filtered, typed-op applied.")
async def _profile_repo_agent(ctx: StepContext) -> StepResult:
    """Stage 1: a governed agent derives the NON-OBVIOUS maintenance facts of the
    repo (tooling commands, hard constraints, traps, undocumented conventions —
    `_PROFILE_GUIDANCE`), seeded with the fingerprint and key config files as
    evidence. No LLM degrades to a recorded capability gap (`no_llm_gap`) — the
    deterministic stages already produced the draft.

    Each returned fact must cite evidence; briefing-channel facts redundant with
    the doc corpus are dropped, and the rest are applied as typed `add_fact` ops
    (capped at 15) — malformed/evidence-less facts are rejected by the store. Any
    `review_checklist` lines are written to `review.md`. Writes land only under
    adapters/<repo>/ (knowledge risk, curator/human-gated downstream)."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    if ctx.llm is None or not ctx.llm.available:
        return no_llm_gap(ctx, "agent.profile_repo",
                          "only deterministic profile stages ran",
                          summary="agent profiling skipped (no LLM) — "
                                  "deterministic stages already produced the "
                                  "draft profile")
    from ..agent_runtime import run_agent_step

    repo = Path(adapter.repo_path or ctx.state.get("repo_path", ""))
    evidence: dict[str, str] = {
        "fingerprint": str(ctx.state.get("outputs", {})
                           .get("fingerprint", {}).get("fingerprint", "")),
    }
    for name in ("pyproject.toml", "setup.cfg", "Makefile", "package.json",
                 ".pre-commit-config.yaml", "CONTRIBUTING.md"):
        path = repo / name
        if path.exists():
            evidence[name] = path.read_text(encoding="utf-8",
                                            errors="replace")[:4_000]

    result, output = await run_agent_step(
        ctx, step_name="agent.profile_repo",
        purpose=f"Derive the non-obvious maintenance facts of the repo at {repo}.",
        guidance=_PROFILE_GUIDANCE,
        expected="profile_facts (evidence-cited) + optional review_checklist",
        evidence=evidence,
        output_extension={
            "profile_facts": "list of {module, kind: command|constraint|"
                             "convention|trap|note, channel: machine|briefing|"
                             "retrieved, text, evidence: list of strings}",
            "review_checklist": "list of repo-specific review checklist lines",
        },
    )
    if not result.ok:
        return result

    corpus = build_doc_corpus(repo)
    store = ProfileStore(adapter.profile_dir)
    ops: list[dict] = []
    redundant = 0
    for fact in output.get("profile_facts") or []:
        if not isinstance(fact, dict):
            continue
        text = str(fact.get("text", "")).strip()
        if not text:
            continue
        if str(fact.get("channel")) == "briefing" and is_redundant(text, corpus):
            redundant += 1
            continue
        ops.append({"op": "add_fact", "id": fact_id("agent", text),
                    "module": str(fact.get("module") or "repo-wide"),
                    "kind": str(fact.get("kind") or "note"),
                    "channel": str(fact.get("channel") or "retrieved"),
                    "text": text, "source": "agent",
                    "evidence": list(fact.get("evidence") or [])})
    results = store.apply_ops(ops[:15])
    applied = results.count("")
    rejected = [r for r in results if r]

    checklist = [str(line) for line in output.get("review_checklist") or []
                 if str(line).strip()]
    if checklist:
        adapter.profile_dir.mkdir(parents=True, exist_ok=True)
        (adapter.profile_dir / "review.md").write_text(
            "# Repo-specific review checklist (agent-derived draft)\n\n"
            + "\n".join(f"- {line}" for line in checklist[:12]) + "\n",
            encoding="utf-8")
        ctx.trace.record("profile_review_checklist", lines=len(checklist))

    ctx.trace.record("profile_facts_applied", applied=applied,
                     rejected=len(rejected), redundant_dropped=redundant)
    result.summary = (f"{applied} fact(s) applied, {len(rejected)} rejected "
                      f"(no evidence/malformed), {redundant} doc-redundant "
                      f"dropped"
                      + (f", review checklist ({len(checklist)} lines)"
                         if checklist else ""))
    result.outputs.update(applied=applied, rejected=rejected,
                          redundant_dropped=redundant)
    return result


# -- Stage 4: scheduled consolidation & audit (design §V2.3.3) -----------------

@step("profile.detect_drift", "deterministic", "read",
      "Stage 4: deterministic drift report (moved module paths, orphaned fact "
      "joins) — refresh material, never auto-fixed.")
async def _detect_drift(ctx: StepContext) -> StepResult:
    """Stage 4: deterministically report profile drift (moved module paths,
    facts whose join keys no longer resolve) against the current repo. Findings
    are refresh material for the consolidation pass — surfaced, never auto-fixed.
    Publishes `profile_drift` to state (B2 `state_updates`)."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    from ...profiles.consolidate import detect_drift

    findings = detect_drift(adapter, ProfileStore(adapter.profile_dir))
    if findings:
        ctx.trace.record("profile_drift", findings=findings[:20])
    return StepResult(True,
                      summary=(f"{len(findings)} drift finding(s)" if findings
                               else "no drift detected"),
                      outputs={"drift": findings,
                               "state_updates": {"profile_drift": findings}})


@step("profile.decay_stale", "deterministic", "knowledge",
      "Stage 4: dormancy decay — unconfirmed facts flip to stale (excluded, "
      "never deleted).")
async def _decay_stale(ctx: StepContext) -> StepResult:
    """Stage 4: dormancy decay — facts unconfirmed for longer than
    `settings.profile_stale_days` flip to `stale` (excluded from retrieval, never
    deleted, so they can be revived). Deterministic; records the decayed ids in
    the trace."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    from ...profiles.consolidate import decay_stale

    stale = decay_stale(ProfileStore(adapter.profile_dir),
                        days=ctx.settings.profile_stale_days)
    if stale:
        ctx.trace.record("profile_decay", stale=stale)
    return StepResult(True,
                      summary=f"{len(stale)} fact(s) decayed to stale "
                              f"(window {ctx.settings.profile_stale_days}d)",
                      outputs={"stale": stale})


_CONSOLIDATE_GUIDANCE = """You are the scheduled consolidation pass over a repo \
profile — the ONLY writer allowed to rewrite or merge. You see the whole \
profile at once plus drift findings. Emit typed ops:
- merge_facts {into, from} when two facts state the same thing (the most
  precise text survives; evidence unions automatically);
- rewrite_fact {id, text} to make a kept fact crisper and imperative — never
  drop the substance; stable facts refuse rewrites that lose evidence;
- mark_stale {id} for facts the drift findings contradict;
- add_evidence / bump_confirmed for facts the drift findings support.
Do NOT invent new facts here (that is the establishment pass's job). Fewer,
sharper facts beat many vague ones — the briefing channel has a hard word
budget. Emit an empty ops list when the profile is already clean."""


@step("agent.profile_consolidate", "agent", "knowledge",
      "Stage 4: the ONLY rewrite/merge tier — whole-profile consolidation via "
      "typed ops, stability gates enforced.")
async def _profile_consolidate(ctx: StepContext) -> StepResult:
    """Stage 4: the ONLY tier allowed to rewrite or merge facts. A governed agent
    sees the whole profile plus the drift findings from state and emits typed ops
    (`merge_facts`/`rewrite_fact`/`mark_stale`/`add_evidence`/`bump_confirmed` —
    `_CONSOLIDATE_GUIDANCE`); it may not invent new facts. No LLM degrades to a
    capability gap (`no_llm_gap`); an empty profile is a no-op.

    Ops are applied with `tier="consolidate"` so the store's stability gates can
    reject rewrites that would lose evidence or substance; rejected ops are
    reported, not silently dropped."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    if ctx.llm is None or not ctx.llm.available:
        return no_llm_gap(ctx, "agent.profile_consolidate",
                          "only deterministic decay/drift ran",
                          summary="consolidation skipped (no LLM); decay and "
                                  "drift detection already ran")
    from ..agent_runtime import run_agent_step

    store = ProfileStore(adapter.profile_dir)
    if not store.facts:
        return StepResult(True, summary="empty profile — nothing to consolidate")
    profile_text = store.profile_file.read_text(encoding="utf-8") \
        if store.profile_file.exists() else ""
    result, output = await run_agent_step(
        ctx, step_name="agent.profile_consolidate",
        purpose=f"Consolidate the '{adapter.name}' repo profile: dedupe, merge, "
                "sharpen; keep provenance intact.",
        guidance=_CONSOLIDATE_GUIDANCE,
        expected="ops list (may be empty)",
        evidence={"profile_yaml": profile_text,
                  "drift_findings": "\n".join(ctx.state.get("profile_drift")
                                              or []) or "(none)"},
        output_extension={"ops": 'list of {"op": "rewrite_fact|merge_facts|'
                                 'mark_stale|add_evidence|bump_confirmed", '
                                 '...op-specific fields}'},
    )
    if not result.ok:
        return result
    ops = [op for op in output.get("ops") or [] if isinstance(op, dict)]
    results = store.apply_ops(ops, tier="consolidate")
    applied = results.count("")
    rejected = [r for r in results if r]
    ctx.trace.record("profile_consolidated", applied=applied,
                     rejected=rejected[:10])
    result.summary = (f"{applied}/{len(ops)} consolidation op(s) applied"
                      + (f", {len(rejected)} rejected by gates" if rejected
                         else ""))
    result.outputs.update(applied=applied, rejected=rejected)
    return result


_JUDGE_GUIDANCE = """You are a READ-ONLY auditor of a repo profile. Report — \
never fix — facts that look wrong: internally contradictory facts, claims the \
evidence does not support, commands that look malformed, briefing lines that \
are vague or read like generated overview prose. For each finding cite the \
fact id and WHY. An empty findings list is a fine answer."""


@step("profile.judge", "agent", "read",
      "Stage 4: read-only profile audit -> JUDGE_REPORT.md; findings surfaced, "
      "never auto-applied.")
async def _profile_judge(ctx: StepContext) -> StepResult:
    """Stage 4: a READ-ONLY agent audit of the profile — reports contradictory,
    unsupported, malformed, or overview-prose facts (`_JUDGE_GUIDANCE`), each
    citing the offending fact id. No LLM degrades to a capability gap
    (`no_llm_gap`). Findings are written to JUDGE_REPORT.md and surfaced for the
    human/next cycle; this handler never calls `apply_ops`, so the profile cannot
    change here."""
    adapter = _adapter_from_state(ctx)
    if isinstance(adapter, StepResult):
        return adapter
    if ctx.llm is None or not ctx.llm.available:
        return no_llm_gap(ctx, "profile.judge", "profile audit skipped",
                          summary="profile audit skipped (no LLM)")
    from ..agent_runtime import run_agent_step

    store = ProfileStore(adapter.profile_dir)
    profile_text = store.profile_file.read_text(encoding="utf-8") \
        if store.profile_file.exists() else "(empty)"
    result, output = await run_agent_step(
        ctx, step_name="profile.judge",
        purpose=f"Audit the '{adapter.name}' repo profile for contradictions "
                "and unsupported claims (report only).",
        guidance=_JUDGE_GUIDANCE, expected="findings (may be empty)",
        evidence={"profile_yaml": profile_text},
        output_extension={"audit_findings":
                          'list of {"fact_id", "issue", "why"}'},
    )
    if not result.ok:
        return result
    findings = [f for f in output.get("audit_findings") or []
                if isinstance(f, dict)]
    # findings are surfaced, never auto-applied (the human/next cycle acts) —
    # this handler never calls apply_ops, so the profile cannot change here
    adapter.profile_dir.mkdir(parents=True, exist_ok=True)
    (adapter.profile_dir / "JUDGE_REPORT.md").write_text(
        "# Profile audit (read-only; nothing auto-fixed)\n\n"
        + ("\n".join(f"- **{f.get('fact_id', '?')}**: {f.get('issue', '')} — "
                     f"{f.get('why', '')}" for f in findings)
           or "No findings.") + "\n", encoding="utf-8")
    ctx.trace.record("profile_judged", findings=len(findings))
    result.summary = f"audit: {len(findings)} finding(s) — JUDGE_REPORT.md"
    result.outputs.update(findings=findings)
    return result
