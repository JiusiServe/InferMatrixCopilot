"""Offline guards for the monthly reviewbot review-quality probe."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

DATASET_DIR = Path(__file__).resolve().parent.parent / "eval" / "dataset"
sys.path.insert(0, str(DATASET_DIR))

import build_reviewbot_report as report  # noqa: E402
import run_reviewbot_arm as arm  # noqa: E402


TRAIN_VAL_PRS = [4804, 4810, 4816, 4817, 4825, 4837, 4859, 4870, 4893,
                 4923, 4926, 4950, 4970, 4977, 5009]


# --- runner: pure pieces ---


def test_sanitize_strips_markers_and_arm_identifying_heading():
    body = (
        "## Omni ReviewBot review\n\nfinding text\n\n"
        "<!-- omni-reviewbot:v1 repo=r pr=1 head=h -->\n"
        "<!-- omni-reviewbot:mode-assignment:v1 x -->\n"
    )
    clean = arm.sanitize(body)
    assert clean.startswith("## Review\n")
    assert "omni-reviewbot" not in clean
    assert "<!--" not in clean
    assert "finding text" in clean


def test_dataset_items_are_train_val_only_and_pinned():
    items = arm.dataset_items()
    assert items == TRAIN_VAL_PRS
    expected = {
        int(k): v
        for k, v in json.loads(arm.EXPECTED_HEADS.read_text()).items()
    }
    assert all(n in expected for n in items)


def test_dry_run_plans_without_touching_anything(tmp_path):
    env = dict(
        os.environ,
        ARM_TAG="reviewbot_drytest",
        ONLY_ITEMS="4893",
        GEN_REPLICATES="2",
    )
    completed = subprocess.run(
        [sys.executable, str(DATASET_DIR / "run_reviewbot_arm.py"),
         "--dry-run"],
        env=env, capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert "pr4893 x2" in completed.stdout
    assert "dry run" in completed.stdout
    assert not (DATASET_DIR / "arms" / "reviewbot_drytest_r1").exists()


# --- report builder: synthetic campaign fixtures ---


def _write_campaign(
    root: Path,
    *,
    tag="reviewbot_2026-09",
    stems=("pr1", "pr2"),
    gen_reps=1,
    judge_reps=2,
    deltas=(0.1, -0.05),
    judge_model="claude-sonnet-5",
    mutate=None,
):
    """A minimal valid campaign. `deltas[i]` is every verdict's paired
    delta for stems[i] on every dim (arm = 0.5 + d, baseline = 0.5)."""
    (root / "baselines" / report.BASELINE).mkdir(parents=True, exist_ok=True)
    for rep in range(1, gen_reps + 1):
        arm_dir = root / "arms" / f"{tag}_r{rep}"
        judge_dir = root / "judgments" / f"{tag}_r{rep}"
        arm_dir.mkdir(parents=True, exist_ok=True)
        judge_dir.mkdir(parents=True, exist_ok=True)
        (arm_dir / "manifest.json").write_text(json.dumps({
            "arm_tag": tag, "replicate": rep, "stems": list(stems),
            "config": {"bot_sha": "cafe" * 10, "agent_provider": "codex",
                       "review_context_mode": "no_discussion"},
        }))
        for stem, delta in zip(stems, deltas):
            arm_text = f"arm review for {stem}"
            base_text = f"baseline review for {stem}"
            (arm_dir / f"{stem}.md").write_text(arm_text)
            base_file = root / "baselines" / report.BASELINE / f"{stem}.md"
            base_file.write_text(base_text)
            for k in range(1, judge_reps + 1):
                arm_label = f"{tag}_r{rep}"
                scores_arm = {d: 0.5 + delta for d in report.DIMS}
                scores_base = {d: 0.5 for d in report.DIMS}
                scores_arm["gap_hit"] = False
                scores_base["gap_hit"] = False
                verdict = {
                    "x": scores_arm, "y": scores_base,
                    "winner": "X" if delta > 0 else "Y",
                    "_blinding": {"X": arm_label, "Y": report.BASELINE},
                    "_roles": {"arm": arm_label,
                               "baseline": report.BASELINE},
                    "_arm_meta": {
                        "judge_backend": "claude",
                        "judge_model": judge_model,
                        "arm_a_sha256": hashlib.sha256(
                            arm_text[:report.CAP].encode()).hexdigest(),
                        "arm_b_sha256": hashlib.sha256(
                            base_text[:report.CAP].encode()).hexdigest(),
                    },
                }
                path = judge_dir / f"{stem}.r{k}.json"
                path.write_text(json.dumps(verdict))
                if mutate:
                    mutate(rep, stem, k, path)
    return root


@pytest.fixture()
def campaign_root(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "DS", tmp_path)
    return tmp_path


def test_verify_and_paired_math(campaign_root):
    _write_campaign(campaign_root)
    verdicts, stems, config = report.load_campaign("reviewbot_2026-09", 1, 2)
    assert len(verdicts) == 4  # 2 stems x 1 gen x 2 judge reps
    aggregate, item_rows, wins, _gap = report.analyze(verdicts, stems)
    # Hand-computed: item deltas are +0.100 and -0.050 on every dim.
    assert aggregate["recall"]["delta"] == pytest.approx(0.025)
    assert aggregate["recall"]["n"] == 2
    assert aggregate["recall"]["pos"] == 1
    assert aggregate["recall"]["neg"] == 1
    assert item_rows["pr1"]["recall"] == pytest.approx(0.1)
    assert wins == {"arm": 2, "baseline": 2, "tie": 0}


def test_missing_verdict_aborts_with_its_identity(campaign_root):
    _write_campaign(campaign_root)
    victim = (campaign_root / "judgments" / "reviewbot_2026-09_r1"
              / "pr2.r2.json")
    victim.unlink()
    with pytest.raises(report.CampaignError, match="MISSING pr2.r2.json"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_extra_verdict_aborts(campaign_root):
    _write_campaign(campaign_root)
    (campaign_root / "judgments" / "reviewbot_2026-09_r1"
     / "pr9.r1.json").write_text("{}")
    with pytest.raises(report.CampaignError, match="EXTRA pr9.r1.json"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_stale_verdict_is_detected_by_sha(campaign_root):
    _write_campaign(campaign_root)
    # The arm text changes after judging — the old verdict must not count.
    (campaign_root / "arms" / "reviewbot_2026-09_r1" / "pr1.md").write_text(
        "regenerated text"
    )
    with pytest.raises(report.CampaignError, match="STALE"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_wrong_judge_model_aborts(campaign_root):
    _write_campaign(campaign_root, judge_model="claude-haiku-4-5")
    with pytest.raises(report.CampaignError, match="pinned"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_report_written_atomically_and_index_upsert_is_idempotent(
    campaign_root,
):
    _write_campaign(campaign_root)
    for _ in range(2):  # running a month twice must not duplicate its row
        verdicts, stems, config = report.load_campaign(
            "reviewbot_2026-09", 1, 2
        )
        aggregate, item_rows, wins, gap = report.analyze(verdicts, stems)
        text = report.render("reviewbot_2026-09", aggregate, item_rows,
                             wins, gap, config, 1, 2)
        report.write_atomic(
            campaign_root / "results" / "reviewbot"
            / "REVIEWBOT_2026-09.md", text,
        )
        report.upsert_index("2026-09", aggregate, wins, config)
    index = (campaign_root / "results" / "reviewbot"
             / "INDEX.md").read_text()
    assert index.count("| 2026-09 |") == 1
    assert "never merge" in index.casefold()
    body = (campaign_root / "results" / "reviewbot"
            / "REVIEWBOT_2026-09.md").read_text()
    assert "Monitoring probe, not a gate" in body
    assert "+0.025" in body
    assert not list(
        (campaign_root / "results" / "reviewbot").glob("*.tmp")
    )


def test_smoke_tags_never_touch_the_index(campaign_root):
    _write_campaign(campaign_root, tag="reviewbot_smoke")
    verdicts, stems, config = report.load_campaign("reviewbot_smoke", 1, 2)
    aggregate, item_rows, wins, gap = report.analyze(verdicts, stems)
    assert report.MONTH_TAG.match("reviewbot_smoke") is None
    assert report.MONTH_TAG.match("reviewbot_2026-09")


def _mutate_verdict(campaign_root, mutator):
    path = (campaign_root / "judgments" / "reviewbot_2026-09_r1"
            / "pr1.r1.json")
    verdict = json.loads(path.read_text())
    mutator(verdict)
    path.write_text(json.dumps(verdict))


def test_malformed_scores_abort_instead_of_shrinking_denominators(
    campaign_root,
):
    _write_campaign(campaign_root)
    _mutate_verdict(campaign_root, lambda v: v["x"].pop("recall"))
    with pytest.raises(report.CampaignError, match=r"x\.recall"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_broken_blinding_aborts_instead_of_defaulting_the_side(
    campaign_root,
):
    _write_campaign(campaign_root)
    # A corrupt map would otherwise silently score the arm as side Y.
    _mutate_verdict(
        campaign_root,
        lambda v: v.__setitem__("_blinding", {"X": "garbage", "Y": "junk"}),
    )
    with pytest.raises(report.CampaignError, match="blinding"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_invalid_winner_and_missing_gap_hit_abort(campaign_root):
    _write_campaign(campaign_root)
    _mutate_verdict(campaign_root, lambda v: v.__setitem__("winner", "Z"))
    with pytest.raises(report.CampaignError, match="winner"):
        report.load_campaign("reviewbot_2026-09", 1, 2)

    _write_campaign(campaign_root)  # restore
    _mutate_verdict(campaign_root, lambda v: v["y"].pop("gap_hit"))
    with pytest.raises(report.CampaignError, match="gap_hit"):
        report.load_campaign("reviewbot_2026-09", 1, 2)


def test_gold_item_missed_by_both_sides_still_appears(campaign_root):
    # pr4810 is a GOLD latent-gap item; both sides missing it must be
    # reported as 0/n, not hidden.
    _write_campaign(campaign_root, stems=("pr4810", "pr2"))
    verdicts, stems, config = report.load_campaign("reviewbot_2026-09", 1, 2)
    _agg, _items, _wins, gap_rows = report.analyze(verdicts, stems)
    assert gap_rows == {"pr4810": {"arm": 0, "baseline": 0, "n": 2}}
    text = report.render("reviewbot_2026-09", _agg, _items, _wins,
                         gap_rows, config, 1, 2)
    assert "pr4810: arm hit 0/2, baseline 0/2" in text


# --- provenance fingerprinting ---


def test_git_state_reports_dirt_and_unknown(tmp_path):
    assert arm.git_state(tmp_path / "not-a-repo") == ("unknown", True)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t",
                    "-c", "user.email=t@e", "commit", "--allow-empty",
                    "-q", "-m", "x"], check=True)
    sha, dirty = arm.git_state(repo)
    assert len(sha) == 40 and dirty is False
    (repo / "uncommitted.py").write_text("x = 1\n")
    _sha2, dirty = arm.git_state(repo)
    assert dirty is True


def test_dirty_source_state_refuses_without_the_escape_hatch(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(arm, "git_state", lambda p: ("f" * 40, True))
    monkeypatch.delenv("REVIEWBOT_EVAL_ALLOW_DIRTY", raising=False)
    with pytest.raises(SystemExit, match="not clean"):
        arm.build_config({"INFERMATRIX_PATH": str(tmp_path)}, tmp_path)
    monkeypatch.setenv("REVIEWBOT_EVAL_ALLOW_DIRTY", "1")
    config = arm.build_config({"INFERMATRIX_PATH": str(tmp_path)}, tmp_path)
    assert config["bot_dirty"] is True  # recorded, not hidden


def test_config_fingerprint_covers_behavior_env_and_both_revisions(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(arm, "git_state", lambda p: ("a" * 40, False))
    child = {
        "INFERMATRIX_PATH": str(tmp_path),
        "AGENT_PROVIDER": "codex",
        "REVIEW_MODEL": "gpt-5.6-luna",
        "GITHUB_TOKEN": "SECRET-MUST-NOT-APPEAR",
    }
    config = arm.build_config(child, tmp_path)
    assert config["bot_sha"] == "a" * 40
    assert config["infermatrix_sha"] == "a" * 40
    assert config["env"]["AGENT_PROVIDER"] == "codex"
    assert config["env"]["REVIEW_MODEL"] == "gpt-5.6-luna"
    assert "SECRET-MUST-NOT-APPEAR" not in json.dumps(config)
    # A model change is a different arm.
    other = arm.build_config(dict(child, REVIEW_MODEL="other"), tmp_path)
    assert other != config


def test_resume_refuses_a_changed_configuration(tmp_path, monkeypatch):
    runner = object.__new__(arm.Runner)
    runner.tag = "reviewbot_fpr"
    runner.items = [4893]
    runner.config = {"bot_sha": "a" * 40, "env": {"REVIEW_MODEL": "m1"}}
    monkeypatch.setattr(arm, "ARMS", tmp_path)
    runner._init_manifest(1)

    runner2 = object.__new__(arm.Runner)
    runner2.tag = "reviewbot_fpr"
    runner2.items = [4893]
    runner2.config = {"bot_sha": "b" * 40, "env": {"REVIEW_MODEL": "m2"}}
    with pytest.raises(SystemExit, match="different configuration"):
        runner2._init_manifest(1)
