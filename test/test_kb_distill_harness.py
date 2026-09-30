"""The knowledge-distillation benchmark harness: the incumbent's operations
under the production drafting's checks, and the paired report."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.trace_store import TraceStore

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("kb_distill_harness", ROOT / "eval" / "kb_distill" / "harness.py")
harness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(harness)

PAGE = "repos/demo/core/rules.md"


def _rule(rule_id: str) -> str:
    return (f"## {rule_id} — keep the demo queue bounded\n\n- 触发：修改 demo queue 的容量时。\n"
            "- 强制：队列满时拒绝新请求。\n- 验收：测试覆盖满队列拒绝路径。 ^[PR #10]\n")


def _tree() -> dict[str, str]:
    return {
        "repos/demo/core/_index.md": "# core\n\n- [rules](rules.md)\n",
        PAGE: ("---\ntitle: \"Demo core rules\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
               "type: rule\ntags: [demo]\nsources: [\"PR #10\"]\n---\n\n# Demo core rules\n\n"
               + _rule("DEMO-1a") + '<!-- kb:rule status="active" since="r1" -->\n'),
    }


def _reply(page: str, rule_id: str = "DEMO-2b") -> str:
    return json.dumps({"operations": [{"kind": "add", "page": page, "rule_id": rule_id,
                                       "section_markdown": _rule(rule_id)}], "rationale": "contract"})


def test_incumbent_operations_apply_the_production_checks():
    files = _tree()
    ops, rejected, error, rationale = harness.incumbent_operations(
        _reply(PAGE), files, repo_dir="repos/demo", release="r2", today="2026-10-01")
    assert len(ops) == 1 and not rejected and error == "" and rationale == "contract"
    # a destination outside the repository is what production refused: rejected, never replayed as a draft
    ops, rejected, error, _ = harness.incumbent_operations(
        _reply("repos/other/core/rules.md"), files, repo_dir="repos/demo", release="r2", today="2026-10-01")
    assert ops == [] and rejected and "outside repos/demo/" in error
    # a draft production rejected after repairs stays rejected whatever the last reply says
    ops, rejected, error, _ = harness.incumbent_operations(
        _reply(PAGE), files, repo_dir="repos/demo", release="r2", today="2026-10-01", production_rejected=True)
    assert ops == [] and rejected and "production rejected" in error
    # a colliding rule ID does not apply (the base already has DEMO-1a)
    ops, rejected, error, _ = harness.incumbent_operations(
        _reply(PAGE, "DEMO-1a"), files, repo_dir="repos/demo", release="r2", today="2026-10-01")
    assert ops == [] and rejected and "no longer applies" in error
    # nothing to learn is not a rejection
    ops, rejected, error, _ = harness.incumbent_operations(
        json.dumps({"operations": [], "rationale": "docs"}), files, repo_dir="repos/demo", release="r2",
        today="2026-10-01")
    assert ops == [] and not rejected and error == ""


def _bench(tmp_path: Path) -> "harness.Bench":
    bench = harness.Bench.__new__(harness.Bench)
    bench.store = TraceStore(tmp_path / "traces", environ={})
    bench.settings = None
    bench.items = {"demo#1": {"item": "demo#1"}, "demo#2": {"item": "demo#2"}}
    bench.units = {}
    return bench


def _judged(bench, unit_id, item, arm, *, judgings):
    summaries = [{"type": "gate_summary", "gate_version": 2, "judge_rep": i + 1, "pass": p, "fail": f, "human": h,
                  "empty": (p + f + h) == 0, "rejected": False, "l1_ok": True, "rule_blocks": p + f + h,
                  "gate_status": "pass" if f == 0 else "fail"} for i, (p, f, h) in enumerate(judgings)]
    bench.units[unit_id] = {"unit_id": unit_id, "item": item, "arm": arm, "replicate": 1, "status": "judged",
                            "summary": summaries[-1], "judgings": summaries}


def test_report_pairs_arms_against_the_incumbent_over_averaged_judgings(tmp_path):
    bench = _bench(tmp_path)
    _judged(bench, "inc:demo#1:1", "demo#1", "inc", judgings=[(1, 0, 0)])
    _judged(bench, "inc:demo#2:1", "demo#2", "inc", judgings=[(0, 1, 0)])
    _judged(bench, "arm:demo#1:1", "demo#1", "arm", judgings=[(1, 0, 0), (0, 1, 0)])   # two judge votes: net 0
    _judged(bench, "arm:demo#2:1", "demo#2", "arm", judgings=[(1, 0, 0)])
    report = bench.report("inc", ["arm"])
    inc, arm = report["arms"]["inc"], report["arms"]["arm"]
    assert inc["units"] == 2 and inc["net_pass"] == 0.0 and inc["gate_fail_units"] == 1 and inc["judgings_per_unit"] == 1
    assert arm["judgings_per_unit"] == 1.5 and arm["net_pass"] == 0.5 and arm["gate_fail_units"] == 0.5
    paired = arm["paired_vs_incumbent"]["net_pass"]
    assert paired["n_items"] == 2 and paired["mean"] == pytest.approx(0.5)   # (0 - 1) and (1 - (-1)) averaged
    assert set(arm["paired_vs_incumbent"]) == set(harness.METRICS)
    assert bench.unit_scores(bench.units["arm:demo#1:1"])["precision"] == 0.5


def test_only_a_sample_of_the_incumbent_fingerprint_is_replayed():
    good = {"provider": "claude-code", "model": "claude-opus-5-5", "system_verified": True}
    assert harness.incumbent_sample_problem(good) == ""
    assert "not the incumbent" in harness.incumbent_sample_problem({**good, "model": "claude-sonnet-5"})
    assert "not the incumbent" in harness.incumbent_sample_problem({**good, "provider": "zcode"})
    assert "system prompt" in harness.incumbent_sample_problem({**good, "system_verified": False})
    assert "user prompt" in harness.incumbent_sample_problem(good, prompt_verified=False)
    assert harness.incumbent_sample_problem({"provider": "zcode", "model": "GLM-5.3-Flash", "system_verified": True},
                                            generator="zcode:GLM-5.3-Flash") == ""


def test_concurrent_judge_replicates_are_all_retained(tmp_path):
    import threading

    bench = _bench(tmp_path)
    bench.dir = tmp_path
    bench.units_path = tmp_path / "units.json"
    bench._lock = threading.RLock()
    bench.units["u:demo#1:1"] = {"unit_id": "u:demo#1:1", "item": "demo#1", "arm": "u", "replicate": 1}
    unit = bench.units["u:demo#1:1"]
    barrier = threading.Barrier(4)

    def record(rep):
        barrier.wait()
        for _ in range(20):
            bench._record_judging(unit, {"type": "gate_summary", "gate_version": 2, "judge_rep": rep,
                                         "pass": rep, "fail": 0, "human": 0, "empty": False, "rejected": False,
                                         "l1_ok": True, "rule_blocks": rep, "gate_status": "pass"})

    threads = [threading.Thread(target=record, args=(rep,)) for rep in (1, 2, 3, 4)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    reps = sorted(s["judge_rep"] for s in bench.judgings(unit))
    assert reps == [1, 2, 3, 4]
    persisted = json.loads(bench.units_path.read_text(encoding="utf-8"))
    assert sorted(s["judge_rep"] for s in persisted["u:demo#1:1"]["judgings"]) == [1, 2, 3, 4]
