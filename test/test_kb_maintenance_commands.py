"""Offline operator queue, authenticated owner resolution and explicit oracles."""
import json
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from infermatrix_copilot.kb_service import cli, maintenance_commands as commands
from infermatrix_copilot.kb_service.maintenance_audit import source_evidence
from infermatrix_copilot.kb_service.maintenance_store import MaintenanceStore
from infermatrix_copilot.kb_service.runtime import KbRuntime
from infermatrix_copilot.knowledge_service.signing import verify

from test_kb_maintenance_flow import configured_runtime, standard_answer


@pytest.fixture
def setup(tmp_path, monkeypatch):
    rt, lifecycle, source, unit, _ = configured_runtime(tmp_path, standard_answer)
    rt.outbox = SimpleNamespace(_key=Ed25519PrivateKey.generate())
    store = MaintenanceStore(rt.ledger, lease_owner=rt.lease_owner)
    run = store.begin_cycle(snapshot=unit["snapshot"], policy_sha256="fixture")
    store.add_items(run["id"], [unit])
    store.record_outcome(run["id"], unit["unit_id"], "contradicted", detail={"reason": "wrong capacity"})
    finding = store.findings()[0]
    monkeypatch.setenv("KB_MAINTENANCE_OWNERS", "owner")
    monkeypatch.setenv("KB_MAINTENANCE_CASES_DIR", str(tmp_path / "cases"))
    monkeypatch.setattr(commands, "subprocess", SimpleNamespace(run=lambda argv, **kwargs: SimpleNamespace(stdout="owner\n")))
    monkeypatch.setattr(KbRuntime, "from_env", classmethod(lambda cls, settings, **kwargs: rt))
    monkeypatch.setattr(rt.ledger, "close", lambda: None)
    return rt, store, finding, source


def args(*values):
    return ["--state-dir", "/unused", *values]


@pytest.mark.parametrize("action", ["plan", "status"])
def test_read_only_operator_commands_do_not_dispatch_or_queue(setup, action, capsys):
    rt, store, _, _ = setup
    before = store.runs()
    assert cli.main(args("maintain", action, "--all")) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["snapshot"] == rt.ledger.active_snapshot()
    if action == "status":
        assert report["findings"][0]["id"] == store.findings()[0]["id"]
        assert report["findings"][0]["outcome"] == "contradicted"
    assert not rt.gateway.calls and not store.pending_requests()
    assert store.runs() == before


def test_run_only_queues_and_stable_identity_rejects_changed_input(setup):
    rt, store, _, _ = setup
    before = store.runs()
    assert cli.main(args("maintain", "run", "--repo", "demo", "--request-id", "night-recovery", "--calibrate")) == 0
    assert cli.main(args("maintain", "run", "--repo", "demo", "--request-id", "night-recovery", "--calibrate")) == 0
    assert len(store.pending_requests()) == 1
    assert store.pending_requests()[0]["detail"] == {"kind": "maintenance", "calibrate": True, "drill": False}
    assert cli.main(args("maintain", "run", "--repo", "demo", "--request-id", "night-recovery", "--drill")) == 1
    assert store.runs() == before and not rt.gateway.calls


def test_selectors_required_and_unknown_repo_rejected(setup):
    with pytest.raises(SystemExit):
        cli.main(args("maintain", "plan"))
    with pytest.raises(SystemExit):
        cli.main(args("maintain", "run", "--all", "--request-id", "x", "--calibrate", "--drill"))
    assert cli.main(args("maintain", "plan", "--repo", "missing")) == 1


def test_queue_does_not_claim_the_scheduler_lease(setup):
    rt, store, _, _ = setup
    held = rt.ledger.live_lease()
    rt.lease_owner = None
    assert cli.main(args("maintain", "run", "--all", "--request-id", "while-scheduler-runs")) == 0
    assert rt.ledger.live_lease() == held
    assert len(store.pending_requests()) == 1 and not rt.gateway.calls


def evidence_for(rt, finding):
    sources = source_evidence(rt, rt.registry[finding["unit"]["repo"]], finding["unit"])
    return {"reason": "The pinned source assigns eight.", "expected": "contradicted",
            "witnesses": [{key: value for key, value in row.items() if key in commands.PROOF_FIELDS}
                          for row in sources]}


def queue(rt, finding, evidence, decision="confirm"):
    return cli.main(args("correction", "resolve", "--id", finding["id"], "--decision", decision,
                         "--evidence", json.dumps(evidence)))


def test_resolution_authenticates_actual_gh_user_and_queues_only(setup, monkeypatch):
    rt, store, finding, _ = setup
    observed = []
    def actual_user(argv, **kwargs):
        observed.append(argv)
        return SimpleNamespace(stdout="intruder\n")
    monkeypatch.setattr(commands.subprocess, "run", actual_user)
    assert queue(rt, finding, evidence_for(rt, finding)) == 1
    assert observed == [["gh", "api", "user", "--jq", ".login"]]
    assert not store.pending_requests()
    monkeypatch.setattr(commands.subprocess, "run", lambda argv, **kwargs: SimpleNamespace(stdout="owner\n"))
    assert queue(rt, finding, evidence_for(rt, finding)) == 0
    assert len(store.pending_requests()) == 1
    assert not list(commands.cases_directory().glob("*/cases/*.json"))
    assert rt.ledger._conn.execute("SELECT COUNT(*) FROM maintenance_resolutions").fetchone()[0] == 0
    assert not rt.gateway.calls


def test_scheduler_resolution_is_idempotent_and_preserves_original_verdict(setup):
    rt, store, finding, _ = setup
    evidence = evidence_for(rt, finding)
    assert queue(rt, finding, evidence) == queue(rt, finding, evidence) == 0
    request = store.pending_requests()[0]
    before = store.finding(finding["id"])
    result = commands.apply_resolution(rt, store, request)
    assert commands.apply_resolution(rt, store, request) == result
    assert store.finding(finding["id"]) == before
    case_file = commands.cases_directory() / "demo" / "cases" / (result["calibration_case"].split("/")[-1])
    case = verify("kb-maintenance-human-case", json.loads(case_file.read_text()), rt.outbox._key.public_key())
    assert case["expected"] == "contradicted" and case["actor"] == "owner"
    assert case["source_evidence"][0]["excerpt"] and case["original_outcome"] == "contradicted"
    assert store.report()["valid_nights"] == 0 and not rt.gateway.calls


@pytest.mark.parametrize("change", ["missing_label", "forged_hash", "tampered_signature", "wrong_lease", "removed_owner"])
def test_confirmation_needs_explicit_label_and_verified_source(setup, monkeypatch, change):
    rt, store, finding, _ = setup
    evidence = evidence_for(rt, finding)
    if change == "missing_label":
        evidence.pop("expected")
        assert queue(rt, finding, evidence) == 1
        return
    if change == "forged_hash":
        evidence["witnesses"][0]["content_sha256"] = "0" * 64
    assert queue(rt, finding, evidence) == 0
    request = store.pending_requests()[0]
    if change == "tampered_signature":
        request["detail"]["resolution"]["payload"]["actor"] = "intruder"
    if change == "wrong_lease":
        rt.lease_owner = "expired"
    if change == "removed_owner":
        monkeypatch.setenv("KB_MAINTENANCE_OWNERS", "another-owner")
    with pytest.raises(ValueError):
        commands.apply_resolution(rt, store, request)
    assert not list(commands.cases_directory().glob("*/cases/*.json"))
    assert rt.ledger._conn.execute("SELECT COUNT(*) FROM maintenance_resolutions").fetchone()[0] == 0


def test_dismiss_is_append_only_and_does_not_create_oracle(setup):
    rt, store, finding, _ = setup
    assert queue(rt, finding, {"reason": "Needs narrower applicability evidence."}, "dismiss") == 0
    result = commands.apply_resolution(rt, store, store.pending_requests()[0])
    assert result["decision"] == "dismiss" and result["calibration_case"] is None
    assert store.finding(finding["id"])["outcome"] == "contradicted"
    assert not list(commands.cases_directory().glob("*/cases/*.json"))


def test_correction_oracle_is_explicit_and_preserved(setup):
    rt, store, finding, _ = setup
    evidence = {**evidence_for(rt, finding), "calibration_kind": "correction"}
    assert queue(rt, finding, evidence) == 1
    evidence["correction_oracle"] = {"expected_gate": "pass", "expected_page_sha256": "c" * 64}
    assert queue(rt, finding, evidence) == 0
    result = commands.apply_resolution(rt, store, store.pending_requests()[0])
    with open(result["calibration_case"]) as handle:
        case = verify("kb-maintenance-human-case", json.load(handle), rt.outbox._key.public_key())
    assert case["correction_oracle"] == evidence["correction_oracle"]
