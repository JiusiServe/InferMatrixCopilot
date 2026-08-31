"""Offline guards for the monthly reviewbot review-quality probe."""
from __future__ import annotations

import base64
import hashlib
import importlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

DATASET_DIR = Path(__file__).resolve().parent.parent / "eval" / "dataset"
sys.path.insert(0, str(DATASET_DIR))

report = importlib.import_module("build_reviewbot_report")
arm = importlib.import_module("run_reviewbot_arm")


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
    env.pop("REVIEWBOT_PYTHON", None)
    env.pop("REVIEWBOT_RELEASE_MANIFEST", None)
    completed = subprocess.run(
        [sys.executable, str(DATASET_DIR / "run_reviewbot_arm.py"),
         "--dry-run"],
        env=env, capture_output=True, text=True, timeout=120,
        check=False,
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
        reviewbot_sha, provider_sha = "cafe" * 10, "beef" * 10
        (arm_dir / "manifest.json").write_text(json.dumps({
            "arm_tag": tag, "replicate": rep, "stems": list(stems),
            "judge_cap": report.CAP,
            "reviewed_heads": {stem: "1" * 40 for stem in stems},
            "started_at": "2026-08-29T00:00:00Z",
            "config": {
                "release": {
                    "paired": True,
                    "throwaway": False,
                    "manifest_fingerprint": "sha256:" + "d" * 64,
                    "release_id": f"{reviewbot_sha}-{provider_sha}",
                    "python": "3.12",
                    "reviewbot": {
                        "version": "0.1.0",
                        "git_sha": reviewbot_sha,
                        "sha256": "a" * 64,
                    },
                    "provider": {
                        "version": "0.2.0",
                        "git_sha": provider_sha,
                        "sha256": "b" * 64,
                        "resource_revision": "sha256:" + "c" * 64,
                    },
                },
                "env": {
                    "AGENT_PROVIDER": "codex",
                    "REVIEW_MODEL": "",
                    "CURSOR_MODEL": "",
                    "CODEX_COMMAND": "",
                    "CODEX_TIMEOUT_SECONDS": "",
                    "CURSOR_TIMEOUT_SECONDS": "",
                    "GITHUB_REPOSITORY": "",
                },
                "review_context_mode": "no_discussion",
                "post_mode": "shadow",
            },
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
    verdicts, stems, _config = report.load_campaign("reviewbot_2026-09", 1, 2)
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
    assert "sha256:dddddddddddd" in body
    assert not list(
        (campaign_root / "results" / "reviewbot").glob("*.tmp")
    )


def test_smoke_tags_never_touch_the_index(campaign_root):
    _write_campaign(campaign_root, tag="reviewbot_smoke")
    verdicts, stems, _config = report.load_campaign("reviewbot_smoke", 1, 2)
    report.analyze(verdicts, stems)
    assert report.MONTH_TAG.match("reviewbot_smoke") is None
    assert report.MONTH_TAG.match("reviewbot_2026-09")


@pytest.mark.parametrize(
    "tag",
    (
        "reviewbot_2026-09\n",
        "../reviewbot_2026-09",
        "reviewbot/2026-09",
    ),
)
def test_unsafe_or_ambiguous_tags_fail_before_any_output(
    campaign_root, monkeypatch, tag
):
    results = campaign_root / "results" / "reviewbot"
    results.mkdir(parents=True)
    index = results / "INDEX.md"
    index.write_text("existing monthly index\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_reviewbot_report.py",
            "--tag", tag,
            "--gen-reps", "1",
            "--judge-reps", "2",
        ],
    )

    with pytest.raises(report.CampaignError, match="campaign tag"):
        report.main()

    assert index.read_text() == "existing monthly index\n"
    assert list(results.glob("REVIEWBOT_*.md")) == []


def _mutate_campaign_manifest(root, mutator, *, tag="reviewbot_2026-09", rep=1):
    path = root / "arms" / f"{tag}_r{rep}" / "manifest.json"
    manifest = json.loads(path.read_text())
    mutator(manifest)
    path.write_text(json.dumps(manifest))


def test_monthly_manifest_identity_must_match_each_replicate(campaign_root):
    _write_campaign(campaign_root, gen_reps=2)
    _mutate_campaign_manifest(
        campaign_root,
        lambda manifest: manifest.__setitem__("replicate", 1),
        rep=2,
    )
    with pytest.raises(report.CampaignError, match=r"r2: replicate=1"):
        report.load_campaign("reviewbot_2026-09", 2, 2)

    _mutate_campaign_manifest(
        campaign_root,
        lambda manifest: manifest.__setitem__("replicate", 2),
        rep=2,
    )
    _mutate_campaign_manifest(
        campaign_root,
        lambda manifest: manifest.__setitem__("arm_tag", "other"),
        rep=2,
    )
    with pytest.raises(report.CampaignError, match=r"r2: arm_tag='other'"):
        report.load_campaign("reviewbot_2026-09", 2, 2)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("post_mode", "post", r"post_mode must be 'shadow'"),
        (
            "review_context_mode",
            "with_discussion",
            r"review_context_mode must be 'no_discussion'",
        ),
    ],
)
def test_monthly_behavior_modes_are_pinned(
    campaign_root, field, value, message
):
    _write_campaign(campaign_root)
    _mutate_campaign_manifest(
        campaign_root,
        lambda manifest: manifest["config"].__setitem__(field, value),
    )
    with pytest.raises(report.CampaignError, match=message):
        report.load_campaign("reviewbot_2026-09", 1, 2)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        pytest.param(
            lambda manifest: manifest.__setitem__("extra", True),
            r"manifest fields do not match",
            id="manifest-extra",
        ),
        pytest.param(
            lambda manifest: manifest.pop("started_at"),
            r"manifest fields do not match",
            id="manifest-missing",
        ),
        pytest.param(
            lambda manifest: manifest["config"].__setitem__("extra", True),
            r"config fields do not match",
            id="config-extra",
        ),
        pytest.param(
            lambda manifest: manifest["config"].pop("env"),
            r"config fields do not match",
            id="config-missing",
        ),
        pytest.param(
            lambda manifest: manifest["config"].__setitem__("env", []),
            r"config.env is not an object",
            id="env-not-object",
        ),
        pytest.param(
            lambda manifest: manifest["config"]["env"].__setitem__(
                "EXTRA", "value"
            ),
            r"config.env fields do not match",
            id="env-extra",
        ),
        pytest.param(
            lambda manifest: manifest["config"]["env"].pop("REVIEW_MODEL"),
            r"config.env fields do not match",
            id="env-missing",
        ),
        pytest.param(
            lambda manifest: manifest["config"]["env"].__setitem__(
                "AGENT_PROVIDER", 1
            ),
            r"config.env values must all be strings",
            id="env-value-type",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__("stems", "pr1"),
            r"stems must be a non-empty, increasing list",
            id="stems-wrong-type",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__("stems", ["pr2", "pr1"]),
            r"stems must be a non-empty, increasing list",
            id="stems-not-runner-order",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__("reviewed_heads", []),
            r"reviewed_heads is not an object",
            id="reviewed-heads-wrong-type",
        ),
        pytest.param(
            lambda manifest: manifest["reviewed_heads"].pop("pr2"),
            r"reviewed_heads keys must exactly match stems",
            id="reviewed-heads-incomplete",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__("judge_cap", "24000"),
            r"judge_cap must be integer 24000",
            id="judge-cap-wrong-type",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__(
                "started_at", "2026-99-29T00:00:00Z"
            ),
            r"started_at is not a runner UTC timestamp",
            id="started-at-invalid",
        ),
    ],
)
def test_monthly_runner_manifest_shape_aborts_before_outputs(
    campaign_root, monkeypatch, mutator, message
):
    _write_campaign(campaign_root)
    _mutate_campaign_manifest(campaign_root, mutator)
    results = campaign_root / "results" / "reviewbot"
    results.mkdir(parents=True)
    index = results / "INDEX.md"
    index.write_text("existing monthly index\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_reviewbot_report.py",
            "--tag", "reviewbot_2026-09",
            "--gen-reps", "1",
            "--judge-reps", "2",
        ],
    )

    with pytest.raises(report.CampaignError, match=message):
        report.main()

    assert index.read_text() == "existing monthly index\n"
    assert not (results / "REVIEWBOT_2026-09.md").exists()


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        pytest.param(
            lambda release: release.__setitem__("paired", False),
            r"paired must be true",
            id="not-paired",
        ),
        pytest.param(
            lambda release: release.__setitem__("throwaway", True),
            r"throwaway must be false",
            id="throwaway",
        ),
        pytest.param(
            lambda release: release.__setitem__(
                "manifest_fingerprint", "unpaired"
            ),
            r"manifest_fingerprint is invalid",
            id="manifest-fingerprint",
        ),
        pytest.param(
            lambda release: release["reviewbot"].__setitem__("version", ""),
            r"reviewbot.version is missing",
            id="reviewbot-version",
        ),
        pytest.param(
            lambda release: release["reviewbot"].__setitem__(
                "git_sha", "a" * 39
            ),
            r"reviewbot.git_sha is invalid",
            id="reviewbot-git-sha",
        ),
        pytest.param(
            lambda release: release["provider"].__setitem__(
                "sha256", "b" * 63
            ),
            r"provider.sha256 is invalid",
            id="provider-wheel-sha",
        ),
        pytest.param(
            lambda release: release["provider"].__setitem__(
                "resource_revision", "legacy"
            ),
            r"provider.resource_revision is invalid",
            id="provider-resource-revision",
        ),
        pytest.param(
            lambda release: release["reviewbot"].__setitem__("extra", True),
            r"reviewbot fields do not match",
            id="closed-component-shape",
        ),
        pytest.param(
            lambda release: release.__setitem__("extra", True),
            r"config.release fields do not match",
            id="closed-release-shape",
        ),
        pytest.param(
            lambda release: release.__setitem__("python", "3.12.1"),
            r"python is not major.minor",
            id="python-major-minor",
        ),
    ],
)
def test_monthly_paired_provenance_shape_is_fail_closed(
    campaign_root, mutator, message
):
    _write_campaign(campaign_root)

    def mutate(manifest):
        mutator(manifest["config"]["release"])

    _mutate_campaign_manifest(campaign_root, mutate)
    with pytest.raises(report.CampaignError, match=message):
        report.load_campaign("reviewbot_2026-09", 1, 2)


@pytest.mark.parametrize("kind", ["legacy", "unpaired"])
def test_monthly_legacy_or_unpaired_manifest_aborts_before_outputs(
    campaign_root, monkeypatch, kind
):
    _write_campaign(campaign_root)

    def mutate(manifest):
        if kind == "legacy":
            manifest["config"].pop("release")
        else:
            release = manifest["config"]["release"]
            release.update(
                paired=False,
                throwaway=True,
                manifest_fingerprint="unpaired",
            )

    _mutate_campaign_manifest(campaign_root, mutate)
    results = campaign_root / "results" / "reviewbot"
    results.mkdir(parents=True)
    index = results / "INDEX.md"
    index.write_text("existing monthly index\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_reviewbot_report.py",
            "--tag", "reviewbot_2026-09",
            "--gen-reps", "1",
            "--judge-reps", "2",
        ],
    )
    with pytest.raises(report.CampaignError):
        report.main()
    assert index.read_text() == "existing monthly index\n"
    assert not (results / "REVIEWBOT_2026-09.md").exists()


def test_smoke_campaign_retains_legacy_manifest_compatibility(campaign_root):
    _write_campaign(campaign_root, tag="reviewbot_smoke")

    def make_legacy(manifest):
        for field in ("judge_cap", "reviewed_heads", "started_at"):
            manifest.pop(field)
        manifest["legacy_extra"] = "accepted only for non-month smoke"
        manifest["config"] = {
            "bot_sha": "cafe" * 10,
            "infermatrix_sha": "beef" * 10,
            "review_context_mode": "no_discussion",
        }

    _mutate_campaign_manifest(
        campaign_root, make_legacy, tag="reviewbot_smoke"
    )
    verdicts, stems, config = report.load_campaign("reviewbot_smoke", 1, 2)
    assert len(verdicts) == len(stems) * 2
    assert "release" not in config


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
    _write_campaign(campaign_root, stems=("pr2", "pr4810"))
    verdicts, stems, config = report.load_campaign("reviewbot_2026-09", 1, 2)
    _agg, _items, _wins, gap_rows = report.analyze(verdicts, stems)
    assert gap_rows == {"pr4810": {"arm": 0, "baseline": 0, "n": 2}}
    text = report.render("reviewbot_2026-09", _agg, _items, _wins,
                         gap_rows, config, 1, 2)
    assert "pr4810: arm hit 0/2, baseline 0/2" in text


# --- paired artifact provenance ---


def _wheel(path: Path, distribution: str, version: str) -> dict:
    dist_info = distribution.replace("-", "_") + f"-{version}.dist-info"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.3\nName: {distribution}\n"
            f"Version: {version}\n",
        )
    return {
        "path": f"wheelhouse/{path.name}",
        "distribution": distribution,
        "version": version,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    }


def _runnable_wheel(
    path: Path,
    distribution: str,
    version: str,
    package_files: dict[str, str],
) -> dict:
    """A minimal standards-compliant pure-Python wheel for offline smoke."""
    dist_info = distribution.replace("-", "_") + f"-{version}.dist-info"
    entries = {
        **{
            name: content.encode("utf-8")
            for name, content in package_files.items()
        },
        f"{dist_info}/METADATA": (
            f"Metadata-Version: 2.1\nName: {distribution}\n"
            f"Version: {version}\n"
        ).encode(),
        f"{dist_info}/WHEEL": (
            b"Wheel-Version: 1.0\nGenerator: eval-test\n"
            b"Root-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }
    record_name = f"{dist_info}/RECORD"
    rows = []
    for name, content in entries.items():
        digest = base64.urlsafe_b64encode(
            hashlib.sha256(content).digest()
        ).rstrip(b"=").decode()
        rows.append(f"{name},sha256={digest},{len(content)}\n")
    entries[record_name] = (
        "".join(rows) + f"{record_name},,\n"
    ).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return {
        "path": f"wheelhouse/{path.name}",
        "distribution": distribution,
        "version": version,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    }


def _paired_manifest(root: Path) -> tuple[Path, dict]:
    wheelhouse = root / "wheelhouse"
    wheelhouse.mkdir(parents=True)
    reviewbot = _wheel(
        wheelhouse / "omni_reviewbot-0.1.0-py3-none-any.whl",
        "omni-reviewbot",
        "0.1.0",
    )
    provider = _wheel(
        wheelhouse / "infermatrix_copilot-0.2.0-py3-none-any.whl",
        "infermatrix-copilot",
        "0.2.0",
    )
    capabilities = {
        "distribution_version": "0.2.0",
        "sdk_api_version": "1.0.0",
        "direct_api_version": "1.0.0",
        "strict_api_version": "1.0.0",
        "knowledge_api_version": "1.0.0",
        "resource_revision": "sha256:" + "3" * 64,
        "supported_repositories": ["afd-plugin", "vllm-omni"],
        "supports_expected_head": True,
        "supports_structured_result": True,
        "supports_post_false": True,
        "supports_file_locking": True,
        "supports_idempotent_strict_start": True,
        "supports_knowledge_curation": True,
        "max_strict_workers": 1,
    }
    reviewbot_sha, provider_sha = "a" * 40, "b" * 40
    manifest = {
        "schema_version": 1,
        "release_id": f"{reviewbot_sha}-{provider_sha}",
        "created_at": "2026-08-29T00:00:00Z",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "reviewbot": {
            "distribution": reviewbot["distribution"],
            "version": reviewbot["version"],
            "git_sha": reviewbot_sha,
            "wheel": reviewbot["path"],
            "sha256": reviewbot["sha256"],
        },
        "provider": {
            "distribution": provider["distribution"],
            "version": provider["version"],
            "git_sha": provider_sha,
            "wheel": provider["path"],
            "sha256": provider["sha256"],
        },
        "api_expectations": {
            "direct_api_version": "1.0.0",
            "strict_api_version": "1.0.0",
            "knowledge_api_version": "1.0.0",
            "required_capabilities": sorted(arm._REQUIRED_CAPABILITIES),
        },
        "provider_capabilities": capabilities,
        "wheelhouse": [reviewbot, provider],
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    runtime = {
        "python": manifest["python"],
        "reviewbot_version": "0.1.0",
        "provider_version": "0.2.0",
        "provider_capabilities": capabilities,
    }
    return path, runtime


def test_paired_manifest_binds_versions_shas_wheels_and_public_resources(
    tmp_path,
):
    path, runtime = _paired_manifest(tmp_path)

    release = arm.validate_paired_release(path, runtime)

    assert release["paired"] is True and release["throwaway"] is False
    assert release["manifest_fingerprint"].startswith("sha256:")
    assert release["reviewbot"]["git_sha"] == "a" * 40
    assert release["provider"]["git_sha"] == "b" * 40
    assert release["reviewbot"]["sha256"]
    assert release["provider"]["sha256"]
    assert release["provider"]["resource_revision"] == "sha256:" + "3" * 64


def test_manifest_discovery_is_confined_to_selected_release_root(tmp_path):
    path, _runtime = _paired_manifest(tmp_path)
    python = tmp_path / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o700)

    selected = arm._release_python(str(python))

    assert arm._release_manifest_path(selected, "") == path.resolve()
    outside = tmp_path.parent / "manifest.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(arm.ReleaseValidationError, match="outside"):
        arm._release_manifest_path(selected, str(outside))


def test_manifest_refuses_runtime_resource_or_wheel_drift(tmp_path):
    path, runtime = _paired_manifest(tmp_path)
    drifted = json.loads(json.dumps(runtime))
    drifted["provider_capabilities"]["resource_revision"] = (
        "sha256:" + "4" * 64
    )
    with pytest.raises(arm.ReleaseValidationError, match="capabilities differ"):
        arm.validate_paired_release(path, drifted)

    wheel = tmp_path / "wheelhouse/omni_reviewbot-0.1.0-py3-none-any.whl"
    wheel.write_bytes(wheel.read_bytes() + b"tampered")
    with pytest.raises(arm.ReleaseValidationError, match="artifact mismatch"):
        arm.validate_paired_release(path, runtime)


def test_paired_runner_uses_private_offline_venv_not_selected_install(
    tmp_path, monkeypatch
):
    _manifest, runtime = _paired_manifest(tmp_path)
    selected = tmp_path / ".venv/bin/python"
    selected.parent.mkdir(parents=True)
    selected.write_text("tampered same-version selected install\n")
    selected.chmod(0o700)
    monkeypatch.setenv("ARM_TAG", "reviewbot_2026-09")
    monkeypatch.setenv("REVIEWBOT_PYTHON", str(selected))
    commands = []

    def fake_release_command(command, **kwargs):
        commands.append((command, kwargs))
        if "venv" in command:
            venv = Path(command[-1])
            python = venv / "bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("#!/bin/sh\n")
            python.chmod(0o700)

    runtime_pythons = []

    def fake_runtime(python, child_env):
        runtime_pythons.append(python)
        return runtime

    monkeypatch.setattr(arm, "_run_release_command", fake_release_command)
    monkeypatch.setattr(arm, "_runtime_identity", fake_runtime)
    runner = arm.Runner()
    try:
        config = runner.ensure_config()
        fresh = Path(runner.python)

        assert config["release"]["paired"] is True
        assert fresh != selected and fresh.parent.parent.name == ".venv"
        assert runtime_pythons == [fresh]
        install = next(command for command, _ in commands if "pip" in command)
        assert "--no-index" in install and "--only-binary=:all:" in install
        root_wheels = install[-2:]
        assert all(str(tmp_path / "wheelhouse") not in value for value in root_wheels)
        assert all("/release/wheelhouse/" in value for value in root_wheels)
    finally:
        runner.close()


def test_real_offline_fresh_venv_installs_and_probes_both_root_wheels(
    tmp_path,
):
    manifest_path, runtime = _paired_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    wheelhouse = tmp_path / "wheelhouse"
    reviewbot = _runnable_wheel(
        wheelhouse / "omni_reviewbot-0.1.0-py3-none-any.whl",
        "omni-reviewbot",
        "0.1.0",
        {"omni_reviewbot/__init__.py": '__version__ = "0.1.0"\n'},
    )
    capabilities = runtime["provider_capabilities"]
    provider = _runnable_wheel(
        wheelhouse / "infermatrix_copilot-0.2.0-py3-none-any.whl",
        "infermatrix-copilot",
        "0.2.0",
        {
            "infermatrix_copilot/__init__.py": "",
            "infermatrix_copilot/sdk/__init__.py": "",
            "infermatrix_copilot/sdk/v1/__init__.py": (
                "class Capabilities:\n"
                "    def to_dict(self):\n"
                f"        return {capabilities!r}\n\n"
                "def get_capabilities():\n"
                "    return Capabilities()\n"
            ),
        },
    )
    manifest["wheelhouse"] = [reviewbot, provider]
    for name, artifact in (("reviewbot", reviewbot), ("provider", provider)):
        manifest[name]["wheel"] = artifact["path"]
        manifest[name]["sha256"] = artifact["sha256"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    child_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    child_env["PYTHONNOUSERSITE"] = "1"
    temporary, python, staged_manifest = arm._fresh_release_venv(
        Path(sys.executable), manifest_path, child_env
    )
    try:
        installed = arm._runtime_identity(python, child_env)
        release = arm.validate_paired_release(staged_manifest, installed)

        assert release["paired"] is True
        assert installed["reviewbot_version"] == "0.1.0"
        assert installed["provider_version"] == "0.2.0"
        assert installed["provider_capabilities"] == capabilities
        assert str(python).startswith(temporary.name)
    finally:
        temporary.cleanup()


def test_staging_rejects_wheel_changed_after_manifest_validation(tmp_path):
    manifest, runtime = _paired_manifest(tmp_path)
    arm.validate_paired_release(manifest, runtime)
    wheel = tmp_path / "wheelhouse/infermatrix_copilot-0.2.0-py3-none-any.whl"
    wheel.write_bytes(wheel.read_bytes() + b"post-validation tamper")

    with pytest.raises(arm.ReleaseValidationError, match="staging"):
        arm._stage_release(manifest, tmp_path / "private-release")


def test_runner_scrubs_source_and_python_import_overrides(monkeypatch):
    monkeypatch.setenv("ARM_TAG", "reviewbot_smoke")
    monkeypatch.setenv("REVIEWBOT_PYTHON", "/release/.venv/bin/python")
    monkeypatch.setenv("INFERMATRIX_PATH", "/source/provider")
    monkeypatch.setenv("PYTHONPATH", "/source/bot/src")
    monkeypatch.setenv("PYTHONHOME", "/source/python")

    runner = arm.Runner()

    assert "INFERMATRIX_PATH" not in runner.child_env
    assert "PYTHONPATH" not in runner.child_env
    assert "PYTHONHOME" not in runner.child_env
    assert runner.child_env["PYTHONNOUSERSITE"] == "1"
    assert runner.child_env["PYTHONSAFEPATH"] == "1"


def test_runner_source_has_no_reverse_checkout_coupling():
    source = (DATASET_DIR / "run_reviewbot_arm.py").read_text()
    for forbidden in (
        "REVIEWBOT_DIR",
        "INFERMATRIX_PATH",
        "git_state",
        'self.bot_dir / "src"',
    ):
        assert forbidden not in source
    assert '[self.python, "-m", "omni_reviewbot"' in source


def test_unpaired_escape_is_recorded_and_forbidden_for_months(monkeypatch):
    monkeypatch.setenv("ARM_TAG", "reviewbot_smoke")
    monkeypatch.setenv("REVIEWBOT_PYTHON", "/release/.venv/bin/python")
    monkeypatch.setenv("REVIEWBOT_EVAL_ALLOW_UNPAIRED", "1")
    runtime = {
        "reviewbot_version": "0.1.0",
        "provider_version": "0.2.0",
        "provider_capabilities": {"resource_revision": "sha256:" + "3" * 64},
    }
    monkeypatch.setattr(arm, "_release_python", lambda value: Path(value))
    monkeypatch.setattr(arm, "_runtime_identity", lambda python, env: runtime)
    monkeypatch.setattr(
        arm,
        "_release_manifest_path",
        lambda python, configured: (_ for _ in ()).throw(
            arm.ReleaseValidationError("manifest missing")
        ),
    )

    runner = arm.Runner()
    assert runner.ensure_config()["release"]["throwaway"] is True
    assert runner.config["release"]["manifest_fingerprint"] == "unpaired"

    monkeypatch.setenv("ARM_TAG", "reviewbot_2026-09")
    monthly = arm.Runner()
    with pytest.raises(SystemExit, match="forbidden for monthly"):
        monthly.ensure_config()


def test_config_fingerprint_covers_behavior_env_and_release():
    child = {
        "AGENT_PROVIDER": "codex",
        "REVIEW_MODEL": "gpt-5.6-luna",
        "GITHUB_TOKEN": "SECRET-MUST-NOT-APPEAR",
    }
    release = {
        "paired": True,
        "manifest_fingerprint": "sha256:" + "f" * 64,
    }
    config = arm.build_config(child, release)
    assert config["release"] == release
    assert config["env"]["REVIEW_MODEL"] == "gpt-5.6-luna"
    assert "SECRET-MUST-NOT-APPEAR" not in json.dumps(config)
    other = arm.build_config(dict(child, REVIEW_MODEL="other"), release)
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
