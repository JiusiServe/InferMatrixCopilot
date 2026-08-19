"""v3 knowledge steps — schema prep, phase-5 report, curate, compare.

Realizes the Rev 8 §2.2 pipeline tail for the v3 playbook
(`phase5_report → curate → compare → report.final_summary`) plus the
schema-preparation step that must precede the first agent write (design
D4/D5, round-4 F4). `ensure_schema_v2()` is invoked from exactly the three
sanctioned writable maintenance entry points: the knowledge-migration CLI,
`rebase.v3_knowledge_prep`, and `rebase.v3_curate` — pinned by test.

`rebase.v3_compare` realizes Rev 8's `compare_with_locked` slot for the v3
pipeline natively (substate-driven; the v1 backend keeps its own untouched
step) and computes the CLOSING knowledge attestation: parent read-compat
layers must digest identically to the prelude's opening block — v3 never
writes them, so drift means outside interference and stamps the §8
comparison gate-ineligible (copilot-store changes are expected outputs and
are excluded by construction).
"""

from __future__ import annotations

from pathlib import Path

from ..step import FailureKind, StepContext, StepResult
from ._common import step
from .rebase_v3 import _adapter_manifest, _substate, _task_params


def _repo_run_dirs(ctx: StepContext, repo_slug: str,
                   *, newest_first: bool = True) -> list[Path]:
    """Run dirs whose `task.json` names THIS repo — both the dormancy
    window and the decision harvest are repo-scoped (a sweep across every
    repo would cross-pollinate state logs and evict the target's recent
    run ids)."""
    import json as _json

    run_root = Path(ctx.settings.run_root)
    if not run_root.exists():
        return []
    matched: list[Path] = []
    for run_dir in sorted(run_root.glob("run-*"), reverse=newest_first):
        try:
            spec = _json.loads((run_dir / "task.json").read_text(
                encoding="utf-8")).get("spec") or {}
        except (OSError, ValueError):
            continue
        if str(spec.get("repo", "")) == repo_slug:
            matched.append(run_dir)
    return matched


def _recent_repo_runs(ctx: StepContext, repo_slug: str,
                      *, limit: int = 12) -> list[str]:
    """The newest `limit` run ids FOR THIS REPO (task.json-matched)."""
    newest = [d.name for d in _repo_run_dirs(ctx, repo_slug)[:limit]]
    return list(reversed(newest))


def _kpaths(ctx: StepContext):
    from ...memory.paths import KnowledgePaths

    repo_slug = (ctx.state.get("task_spec") or {}).get("repo", "")
    return KnowledgePaths.resolve(
        ctx.settings, repo_slug,
        adapter_root=Path(ctx.settings.adapters_dir)
        / repo_slug.replace("-", "_"))


def _knowledge_layer_paths(manifest: dict) -> dict | StepResult:
    """The DECLARED parent read-compat layers, expanded — BLOCKED when a
    declared key's env var did not expand (the silent knowledge-bare run
    the §8 gate can never allow; same rule the prelude enforces)."""
    from ...adapters.base import expand_path

    cfg = (manifest.get("rebase") or {}).get("knowledge") or {}
    out: dict[str, str] = {}
    for key in ("parent_debug_db", "parent_skills_dir"):
        raw = str(cfg.get(key) or "")
        expanded = expand_path(raw)
        if raw and not expanded:
            return StepResult(False, FailureKind.BLOCKED,
                              f"declared knowledge layer {key}={raw!r} did "
                              "not expand (env var unset)")
        out[key] = expanded
    return out


@step("rebase.v3_knowledge_prep", "deterministic", "knowledge",
      "Explicit schema-v2 preparation of the rebase debug store.")
async def _v3_knowledge_prep(ctx: StepContext) -> StepResult:
    """Runs BEFORE any agent can record (right after the guard): the
    additive v2 columns must exist or the first validation run silently
    drops key/tags/watch_outs/provenance (round-4 F4). One of the three
    sanctioned `ensure_schema_v2()` entry points; report_only never reaches
    this step (its stores stay strictly read-only)."""
    from ...memory.debug_memory import DebugMemory

    db = _kpaths(ctx).rebase_backend_db
    try:
        upgraded = DebugMemory(db).ensure_schema_v2()
    except Exception as exc:  # noqa: BLE001 — store corruption = failed run
        return StepResult(False, summary=f"debug store {db} cannot reach "
                                         f"schema v2: {exc}")
    return StepResult(True, summary=("schema upgraded to v2"
                                     if upgraded else "schema already v2"),
                      outputs={"state_updates": {"knowledge_prepped": True}})


@step("rebase.v3_phase5_report", "deterministic", "read",
      "Rebase-specific FINAL_SUMMARY.md from substate (parent phase 5).")
async def _v3_phase5_report(ctx: StepContext) -> StepResult:
    """The parent's phase-5 artifact: per-module outcomes, test pipeline
    verdicts, and CI state, from SUBSTATE (the single source the finalize
    row also rules from). Runs before curate so curation can never mask
    what the run actually did."""
    sub = _substate(ctx)
    data = sub.read()
    mods = data.get("modules") or {}
    tests = (data.get("tests") or {})
    pipeline = tests.get("pipeline") or {}
    ci = data.get("ci") or {}
    lines = ["# FINAL_SUMMARY — repo-rebase v3", "",
             f"- run: {ctx.state.get('run_id', ctx.run_dir.name)}",
             f"- mode: {_task_params(ctx).get('rebase_mode', '')}",
             f"- upstream commit: {data.get('upstream_commit', '')}", "",
             "## Modules"]
    for name, spec in sorted(mods.items()):
        spec = spec or {}
        lines.append(f"- {name}: {spec.get('status', '?')}"
                     + (f" — {spec.get('detail')}" if spec.get("detail")
                        else ""))
    if not mods:
        lines.append("- (none)")
    lines += ["", "## Local tests",
              f"- passed {pipeline.get('passed', 0)} / failed "
              f"{pipeline.get('failed', 0)} / skipped "
              f"{pipeline.get('skipped', 0)}"]
    for t in pipeline.get("failed_tests") or []:
        lines.append(f"  - failed: {t}")
    for i in tests.get("infra_failures") or []:
        lines.append(f"  - infra: {i}")
    precommit = (tests.get("precommit") or {}).get("result", "")
    if precommit:
        lines.append(f"- precommit: {precommit}")
    if ci:
        lines += ["", "## Remote CI",
                  f"- result: {ci.get('result', '')}"
                  + (f" ({ci.get('reason')})" if ci.get("reason") else "")]
        for name in ci.get("unfixed") or []:
            lines.append(f"  - unfixed: {name}")
    path = ctx.run_dir / "FINAL_SUMMARY.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return StepResult(True, summary=f"FINAL_SUMMARY.md: {len(mods)} modules")


@step("rebase.v3_curate", "script", "knowledge",
      "Debug-memory curation + watchdog harvest/promotion (runtime stores).")
async def _v3_curate(ctx: StepContext) -> StepResult:
    """Rev 8 §5's full-curate slot: repo-scoped debug-memory curation
    (merge→retire with lineage, stale/dormant marking, skill candidates),
    then the EXACTLY-ONCE watchdog-decision harvest (run dir → state log,
    the state log itself as dedup authority) and noise promotion into the
    runtime overlay. Copilot runtime stores only — parent read-compat
    layers and the adapter tree are never written. A failure here is a
    typed run failure (knowledge-store corruption must not hide behind a
    green report)."""
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    from ...memory.curator import DebugMemoryCurator
    from ...memory.debug_memory import DebugMemory
    from ...memory.skills import SkillStore
    from ...testing import watchdog_learn

    kp = _kpaths(ctx)
    repo_slug = (ctx.state.get("task_spec") or {}).get("repo", "")
    layers = _knowledge_layer_paths(manifest)
    if isinstance(layers, StepResult):
        return layers
    try:
        dm = DebugMemory(kp.rebase_backend_db)
        dm.ensure_schema_v2()  # belt: resumed old runs, standalone stores
        skill_layers = [SkillStore(kp.skills_runtime_dir),
                        SkillStore(kp.skills_seed_dir)]
        if layers.get("parent_skills_dir"):
            skill_layers.append(SkillStore(layers["parent_skills_dir"]))
        recent = _recent_repo_runs(ctx, repo_slug, limit=12)
        sub = _substate(ctx)
        curator = DebugMemoryCurator(
            dm, repo=repo_slug,
            upstream_path=str(ctx.state.get("upstream_origin_path") or ""),
            current_upstream_commit=str(
                ctx.state.get("upstream_commit")
                or sub.read().get("upstream_commit") or ""),
            skill_layers=tuple(skill_layers),
            propose_to=SkillStore(kp.skills_runtime_dir))
        report = curator.curate(recent_runs=recent)

        # exactly-once watchdog harvest + promotion (design D4). Every
        # run dir OF THIS REPO is a source — local_ci runs never curate
        # and a crashed full run dies before its tail, so their decisions
        # would otherwise never reach the state log; task.json scoping
        # keeps other repos' decisions out of this repo's log, and the
        # state log's identity set + the per-file digest checkpoint keep
        # the sweep exact and cheap.
        sources = [d / "watchdog_decisions.jsonl"
                   for d in _repo_run_dirs(ctx, repo_slug,
                                           newest_first=False)]
        own = ctx.run_dir / "watchdog_decisions.jsonl"
        if own not in sources:
            sources.append(own)
        harvested = watchdog_learn.harvest(
            kp.watchdog_decisions, kp.watchdog_harvest_checkpoint,
            sources, lock_path=kp.state_lock)
        seed_noise: list[str] = []
        seed_file = kp.skills_seed_dir.parent / "testing" / \
            "watchdog_patterns.yaml"
        if seed_file.is_file():
            import yaml
            seed_noise = list((yaml.safe_load(
                seed_file.read_text(encoding="utf-8")) or {})
                .get("noise") or [])
        promoted = watchdog_learn.promote(
            kp.watchdog_decisions, kp.watchdog_overlay,
            seed_noise=seed_noise)

        # PROMOTION.md — the human curation surface (state dir)
        kp.state_dir.mkdir(parents=True, exist_ok=True)
        promo = ["# Knowledge curation — pending human review", "",
                 f"- run: {ctx.state.get('run_id', ctx.run_dir.name)}",
                 f"- merged: {report.merged}, stale: {report.stale}, "
                 f"dormant: {report.dormant}",
                 f"- watchdog: {harvested} decisions harvested, "
                 f"{len(promoted)} noise patterns promoted", ""]
        if report.candidates:
            promo.append("## Skill candidates (promote via SkillStore)")
            promo += [f"- {c.key} (module={c.module}, {c.occurrences}x): "
                      f"{c.trigger}" for c in report.candidates]
        if report.actions:
            promo.append("")
            promo.append("## Actions")
            promo += [f"- {a}" for a in report.actions]
        (kp.state_dir / "PROMOTION.md").write_text(
            "\n".join(promo) + "\n", encoding="utf-8")
        ctx.trace.record("knowledge_write", surface="curate",
                         merged=report.merged, stale=report.stale,
                         dormant=report.dormant,
                         candidates=len(report.candidates),
                         harvested=harvested, promoted=len(promoted))
        sub.update({"curation": report.to_dict()})
    except Exception as exc:  # noqa: BLE001 — typed run failure (row 4)
        return StepResult(False, summary=f"curation failed: {exc}")
    return StepResult(
        True,
        summary=f"curated: {report.merged} merged, {report.stale} stale, "
                f"{len(report.candidates)} candidates; watchdog "
                f"{harvested} harvested/{len(promoted)} promoted")


@step("rebase.v3_compare", "report", "read",
      "Closing knowledge attestation + baseline comparison artifact.")
async def _v3_compare(ctx: StepContext) -> StepResult:
    """Runs AFTER curate and BEFORE report.final_summary (Rev 8 tail): the
    parent layers' closing digests either match the prelude's opening block
    (fair world) or raise `knowledge_drift` — recorded in substate so the
    final report and the §8 comparison tool see it. Also writes the
    COMPARISON.md skeleton against an optional locked/ext baseline status
    file (task param `baseline_status`)."""
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    from ...rebase_engine import knowledge_attest

    sub = _substate(ctx)
    data = sub.read()
    knowledge = data.get("knowledge") or {}
    drift = False
    layers = _knowledge_layer_paths(manifest)
    if isinstance(layers, StepResult):
        return layers
    if knowledge.get("open"):
        try:
            close = knowledge_attest.attest_layers(**layers)
        except Exception as exc:  # noqa: BLE001
            close = {"error": str(exc)}
            drift = True
        else:
            drift = any(
                close.get(k, {}).get("digest")
                != knowledge["open"].get(k, {}).get("digest")
                for k in knowledge["open"])
        sub.update({"knowledge": {**knowledge, "close": close,
                                  "drift": drift}})
        ctx.trace.record("knowledge_provenance", when="close", drift=drift)

    lines = ["# COMPARISON — v3 run vs baseline", "",
             f"- run: {ctx.state.get('run_id', ctx.run_dir.name)}",
             f"- knowledge drift (parent layers, open→close): "
             f"{'DETECTED — gate-ineligible without owner waiver' if drift else 'none'}",
             "", "## Modules (this run)"]
    for name, spec in sorted((data.get("modules") or {}).items()):
        lines.append(f"- {name}: {(spec or {}).get('status', '?')}")
    baseline_file = str(_task_params(ctx).get("baseline_status") or "")
    if baseline_file and Path(baseline_file).exists():
        import json
        try:
            baseline = json.loads(Path(baseline_file)
                                  .read_text(encoding="utf-8"))
            lines += ["", "## Baseline", f"- source: {baseline_file}"]
            for name, spec in sorted((baseline.get("modules")
                                      or {}).items()):
                status = spec.get("status", spec) if isinstance(spec, dict) \
                    else spec
                lines.append(f"- {name}: {status}")
        except ValueError as exc:
            lines += ["", f"## Baseline unreadable: {exc}"]
    else:
        lines += ["", "## Baseline", "- no baseline supplied "
                  "(pass --task-param baseline_status=<status.json> for the "
                  "side-by-side; the §8 gate uses scripts/"
                  "compare_validation.py over both worlds' artifacts)"]
    (ctx.run_dir / "COMPARISON.md").write_text("\n".join(lines) + "\n",
                                               encoding="utf-8")
    if drift:
        return StepResult(True, summary="COMPARISON.md written; knowledge "
                                        "DRIFT detected (gate-ineligible)")
    return StepResult(True, summary="COMPARISON.md written; no drift")
