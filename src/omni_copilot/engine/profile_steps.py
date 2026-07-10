"""Profile-establishment steps (doc/DESIGN.md §V2.3.3, Stages 0–1.5) — the
`repo-profile` playbook. Read-only toward the TARGET repo; writes land only
under plugins/<repo>/ (knowledge risk, curator/human-gated downstream):

- profile.fingerprint    Stage 0: deterministic fingerprint; draft plugin for
                         unknown repos (stops at `status: draft` — human gate)
- profile.structure_scan Stage 0: deterministic module draft into plugin.yaml
- profile.ingest_docs    Stage 1.5 input: existing AGENTS.md/CLAUDE.md et al.
                         ingested as human-authored briefing facts
- agent.profile_repo     Stage 1: governed agent derives non-obvious facts
                         (evidence-cited, typed ops, redundancy-filtered)
"""

from __future__ import annotations

from pathlib import Path

from ..plugins.base import (PluginRegistry, RepoPlugin, draft_plugin,
                            fingerprint_repo, load_plugin, update_manifest)
from ..profiles.establish import (HUMAN_DOC_NAMES, build_doc_corpus,
                                  extract_directives, fact_id, is_redundant,
                                  scan_modules)
from ..profiles.store import ProfileStore
from .builtin_steps import _repo_path
from .registry import StepRegistry
from .step import FailureKind, StepContext, StepResult, StepSpec


def _plugin_from_state(ctx: StepContext) -> RepoPlugin | StepResult:
    root = ctx.state.get("plugin_root")
    if not root:
        return StepResult(False, FailureKind.BLOCKED,
                          "no plugin_root in state — run profile.fingerprint first")
    return load_plugin(root)


async def _fingerprint(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    if repo is None or not repo.exists():
        return StepResult(False, FailureKind.BLOCKED,
                          f"repo checkout not configured (repo_path={repo})")
    fp = fingerprint_repo(repo)
    registry = PluginRegistry(ctx.settings.plugins_dir)
    plugin = registry.resolve(repo_path=str(repo))
    created = False
    if plugin is None:
        plugin = load_plugin(draft_plugin(fp, ctx.settings.plugins_dir))
        created = True
    updates = {"plugin_root": str(plugin.root),
               "repo_language": fp["language"]}
    ctx.state.update(updates)
    ctx.trace.record("profile_fingerprint", plugin=plugin.name,
                     created=created, language=fp["language"])
    return StepResult(True,
                      summary=f"plugin '{plugin.name}' "
                              f"({'drafted' if created else plugin.status}), "
                              f"language={fp['language']}",
                      outputs={"fingerprint": fp, "plugin": plugin.name,
                               "created": created, "state_updates": updates})


async def _structure_scan(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    if plugin.modules:
        return StepResult(True, summary=f"modules already declared "
                                        f"({len(plugin.modules)}) — kept as-is")
    repo = Path(plugin.repo_path or ctx.state.get("repo_path", ""))
    language = str(ctx.state.get("repo_language")
                   or plugin.manifest.get("repo", {}).get("language") or "")
    modules = scan_modules(repo, language)
    if not modules:
        return StepResult(True, summary="no module candidates found "
                                        "(left for the profiling agent/human)")
    update_manifest(plugin, "modules", modules, actor="agent")
    ctx.trace.record("profile_modules_draft", modules=sorted(modules))
    return StepResult(True,
                      summary=f"module draft written ({sorted(modules)})",
                      outputs={"modules": modules})


async def _ingest_docs(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    repo = Path(plugin.repo_path or ctx.state.get("repo_path", ""))
    corpus = build_doc_corpus(repo)
    store = ProfileStore(plugin.profile_dir)
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


async def _profile_repo_agent(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    if ctx.llm is None or not ctx.llm.available:
        ctx.trace.record("capability_gap", capability="llm",
                         step="agent.profile_repo",
                         effect="only deterministic profile stages ran")
        return StepResult(True, summary="agent profiling skipped (no LLM) — "
                                        "deterministic stages already produced "
                                        "the draft profile")
    from .agent_runtime import run_agent_step

    repo = Path(plugin.repo_path or ctx.state.get("repo_path", ""))
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
    store = ProfileStore(plugin.profile_dir)
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
        plugin.profile_dir.mkdir(parents=True, exist_ok=True)
        (plugin.profile_dir / "review.md").write_text(
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

async def _detect_drift(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    from ..profiles.consolidate import detect_drift

    findings = detect_drift(plugin, ProfileStore(plugin.profile_dir))
    if findings:
        ctx.trace.record("profile_drift", findings=findings[:20])
    return StepResult(True,
                      summary=(f"{len(findings)} drift finding(s)" if findings
                               else "no drift detected"),
                      outputs={"drift": findings,
                               "state_updates": {"profile_drift": findings}})


async def _decay_stale(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    from ..profiles.consolidate import decay_stale

    stale = decay_stale(ProfileStore(plugin.profile_dir),
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


async def _profile_consolidate(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    if ctx.llm is None or not ctx.llm.available:
        ctx.trace.record("capability_gap", capability="llm",
                         step="agent.profile_consolidate",
                         effect="only deterministic decay/drift ran")
        return StepResult(True, summary="consolidation skipped (no LLM); "
                                        "decay and drift detection already ran")
    from .agent_runtime import run_agent_step

    store = ProfileStore(plugin.profile_dir)
    if not store.facts:
        return StepResult(True, summary="empty profile — nothing to consolidate")
    profile_text = store.profile_file.read_text(encoding="utf-8") \
        if store.profile_file.exists() else ""
    result, output = await run_agent_step(
        ctx, step_name="agent.profile_consolidate",
        purpose=f"Consolidate the '{plugin.name}' repo profile: dedupe, merge, "
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


async def _profile_judge(ctx: StepContext) -> StepResult:
    plugin = _plugin_from_state(ctx)
    if isinstance(plugin, StepResult):
        return plugin
    if ctx.llm is None or not ctx.llm.available:
        ctx.trace.record("capability_gap", capability="llm",
                         step="profile.judge", effect="profile audit skipped")
        return StepResult(True, summary="profile audit skipped (no LLM)")
    from .agent_runtime import run_agent_step

    store = ProfileStore(plugin.profile_dir)
    profile_text = store.profile_file.read_text(encoding="utf-8") \
        if store.profile_file.exists() else "(empty)"
    result, output = await run_agent_step(
        ctx, step_name="profile.judge",
        purpose=f"Audit the '{plugin.name}' repo profile for contradictions "
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
    plugin.profile_dir.mkdir(parents=True, exist_ok=True)
    (plugin.profile_dir / "JUDGE_REPORT.md").write_text(
        "# Profile audit (read-only; nothing auto-fixed)\n\n"
        + ("\n".join(f"- **{f.get('fact_id', '?')}**: {f.get('issue', '')} — "
                     f"{f.get('why', '')}" for f in findings)
           or "No findings.") + "\n", encoding="utf-8")
    ctx.trace.record("profile_judged", findings=len(findings))
    result.summary = f"audit: {len(findings)} finding(s) — JUDGE_REPORT.md"
    result.outputs.update(findings=findings)
    return result


def register_profile_steps(registry: StepRegistry) -> StepRegistry:
    add = registry.register
    add(StepSpec("profile.fingerprint", "deterministic", "knowledge", _fingerprint,
                 "Stage 0: deterministic repo fingerprint; draft plugin for "
                 "unknown repos (stops at status: draft)."))
    add(StepSpec("profile.structure_scan", "deterministic", "knowledge",
                 _structure_scan,
                 "Stage 0: deterministic module draft into plugin.yaml "
                 "(never overwrites declared modules)."))
    add(StepSpec("profile.ingest_docs", "deterministic", "knowledge", _ingest_docs,
                 "Ingest AGENTS.md/CLAUDE.md-style human directives as "
                 "briefing facts (doc-redundant lines dropped)."))
    add(StepSpec("agent.profile_repo", "agent", "knowledge", _profile_repo_agent,
                 "Stage 1: governed agent derives non-obvious, evidence-cited "
                 "profile facts; redundancy-filtered, typed-op applied."))
    add(StepSpec("profile.detect_drift", "deterministic", "read", _detect_drift,
                 "Stage 4: deterministic drift report (moved module paths, "
                 "orphaned fact joins) — refresh material, never auto-fixed."))
    add(StepSpec("profile.decay_stale", "deterministic", "knowledge", _decay_stale,
                 "Stage 4: dormancy decay — unconfirmed facts flip to stale "
                 "(excluded, never deleted)."))
    add(StepSpec("agent.profile_consolidate", "agent", "knowledge",
                 _profile_consolidate,
                 "Stage 4: the ONLY rewrite/merge tier — whole-profile "
                 "consolidation via typed ops, stability gates enforced."))
    add(StepSpec("profile.judge", "agent", "read", _profile_judge,
                 "Stage 4: read-only profile audit -> JUDGE_REPORT.md; "
                 "findings surfaced, never auto-applied."))
    return registry
