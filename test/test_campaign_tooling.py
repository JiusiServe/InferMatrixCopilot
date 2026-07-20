"""Pre-campaign tooling gates (eval plan v3): spend ledger reservations,
replicate validation, and baseline aggregation — unit-tested BEFORE any paid
run, per the hook-reviewed plan."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
GOAL = ROOT / "eval" / "dataset" / "goal-eval"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    mod = _load("campaign_ledger", GOAL / "campaign_ledger.py")
    monkeypatch.setattr(mod, "LEDGER", tmp_path / "ledger.jsonl")
    return mod


def test_ledger_earmark_and_preventive_refusal(ledger):
    ledger.earmark_final(30.0)
    assert ledger.totals()["available"] == pytest.approx(120.0)
    assert ledger.reserve("r1", 100.0)
    assert not ledger.reserve("r2", 30.0)      # 100+30 > 120 — refused UP FRONT
    ledger.settle("r1", 40.0)
    assert ledger.totals()["settled"] == pytest.approx(40.0)
    assert ledger.reserve("r2", 30.0)          # freed headroom
    ledger.release("r2")
    t = ledger.totals()
    assert t["reserved_open"] == 0.0
    # failed paid invocations still get ledgered as settles with no artifact
    ledger.settle("r-failed", 0.7, note="failed invocation, no artifact")
    assert ledger.totals()["settled"] == pytest.approx(40.7)


def _mk_arm(tmp_path, stem, rc=0, body="ok " * 30, head=""):
    d = tmp_path / "arm"
    d.mkdir(exist_ok=True)
    text = body + (f"\nPR-TIME TREE (head {head})" if stem.startswith("pr") else "")
    (d / f"{stem}.md").write_text(text)
    (d / f"{stem}.cost.json").write_text(json.dumps({"rc": rc}))
    return d


def _mk_verdict(jdir, stem, rep, arm_dir, dims, bad=None):
    import hashlib
    jdir.mkdir(exist_ok=True)
    side = {d: 0.5 for d in dims}
    if stem.startswith("pr"):
        side["gap_hit"] = False
    text = (arm_dir / f"{stem}.md").read_text()[:24_000]
    v = {"x": dict(side), "y": dict(side), "winner": "X", "margin": "slight",
         "_blinding": {"X": "copilot_v2", "Y": "opus_baseline"},
         "_arm_meta": {"judge_rep": rep,
                       "arm_a_sha256": hashlib.sha256(text.encode()).hexdigest()}}
    if bad == "range":
        v["x"][dims[0]] = 1.7
    if bad == "hash":
        v["_arm_meta"]["arm_a_sha256"] = "0" * 64
    (jdir / f"{stem}.r{rep}.json").write_text(json.dumps(v))


def test_validate_replicate_detects_each_failure_class(tmp_path, monkeypatch):
    vr = _load("validate_replicate", GOAL / "validate_replicate.py")
    monkeypatch.setattr(vr, "VAL_STEMS", ["pr4810", "issue4842"])
    monkeypatch.setattr(vr, "HEADS", tmp_path / "heads.json")
    (tmp_path / "heads.json").write_text(json.dumps({"4810": "f" * 40}))
    arm = _mk_arm(tmp_path, "pr4810", head="f" * 40)
    _mk_arm(tmp_path, "issue4842")
    jdir = tmp_path / "judge"
    for rep in (1, 2, 3):
        _mk_verdict(jdir, "pr4810", rep, arm, ("recall", "precision",
                                               "actionability"))
        _mk_verdict(jdir, "issue4842", rep, arm, ("correctness", "grounding",
                                                  "completeness"))
    assert vr.validate(arm, jdir) == []             # fully valid

    # each failure class trips it
    _mk_verdict(jdir, "pr4810", 1, arm, ("recall", "precision",
                                         "actionability"), bad="range")
    errs = vr.validate(arm, jdir)
    assert any("out of [0,1]" in e for e in errs)
    _mk_verdict(jdir, "pr4810", 1, arm, ("recall", "precision",
                                         "actionability"), bad="hash")
    assert any("hash mismatch" in e for e in vr.validate(arm, jdir))
    (jdir / "issue4842.r3.json").unlink()
    assert any("missing verdict" in e for e in vr.validate(arm, jdir))
    (arm / "pr4810.cost.json").write_text(json.dumps({"rc": 3}))
    assert any("rc=3" in e for e in vr.validate(arm, jdir))


def test_validate_replicate_checkout_assertion(tmp_path, monkeypatch):
    vr = _load("validate_replicate", GOAL / "validate_replicate.py")
    monkeypatch.setattr(vr, "VAL_STEMS", ["pr4810"])
    monkeypatch.setattr(vr, "HEADS", tmp_path / "heads.json")
    (tmp_path / "heads.json").write_text(json.dumps({"4810": "a" * 40}))
    arm = _mk_arm(tmp_path, "pr4810", head="b" * 40)   # wrong pinned head
    jdir = tmp_path / "judge"
    for rep in (1, 2, 3):
        _mk_verdict(jdir, "pr4810", rep, arm,
                    ("recall", "precision", "actionability"))
    assert any("pinned head" in e for e in vr.validate(arm, jdir))


def test_baseline_aggregation_requires_split_and_items(tmp_path):
    sys.path.insert(0, str(ROOT / "eval" / "dataset"))
    ac = _load("aggregate_costs", ROOT / "eval" / "dataset" / "aggregate_costs.py")
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(SystemExit, match="missing expected item"):
        ac.aggregate_baseline(base, "val")
    for stem in ac.VAL_STEMS:
        (base / f"{stem}.cost.json").write_text(json.dumps(
            {"cost_usd": 1.0, "wall_s": 100, "input_tokens": 5,
             "output_tokens": 2}))
    out = ac.aggregate_baseline(base, "val")
    assert out["items"] == 10 and out["total_usd"] == pytest.approx(10.0)
    assert out["basis"] == "real_billed_final_attempt"
    with pytest.raises(SystemExit):
        ac.aggregate_baseline(base, "test")
