"""Knowledge service core: lifecycle config, ledger, signing, outbox, kb CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from infermatrix_copilot.adapters.base import AdapterError, RepoAdapter, update_manifest
from infermatrix_copilot.kb_service.config import (
    LifecycleConfigError, general_lifecycle, load_registry, parse_lifecycle,
)
from infermatrix_copilot.kb_service.ledger import Ledger, LeaseError
from infermatrix_copilot.kb_service.outbox import (
    CONTROL_MAX_AGE, Outbox, OutboxError, check_item,
)
from infermatrix_copilot.knowledge_service.signing import (
    SignatureError, generate_private_key, load_private_key, load_public_key,
    public_key_text, sign, verify,
)

ROOT = Path(__file__).resolve().parents[1]


class Clock:
    def __init__(self, now: float = 1_000_000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def _adapter(tmp_path: Path, section: dict, *, auditor: bool = False) -> RepoAdapter:
    root = tmp_path / "demo_adapter"
    root.mkdir(exist_ok=True)
    if auditor:
        (root / "audit.py").write_text("def audit_for_knowledge(**kw): return {}\n", encoding="utf-8")
    manifest = {
        "name": "demo_adapter",
        "repo": {"full_name": "org/demo", "path": "/x"},
        "knowledge": {"repo_subdir": "repos/demo"},
        "knowledge_lifecycle": section,
    }
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return RepoAdapter(name="demo_adapter", root=root, manifest=manifest)


# -- config ----------------------------------------------------------------------

def test_shipped_adapters_register_with_repo_neutral_config():
    registry = load_registry(ROOT / "adapters", general=general_lifecycle(enabled=False))
    omni = registry["vllm-omni"]
    assert omni.enabled and omni.mode == "auto_merge" and omni.auto_merge
    assert omni.release.trigger == "github_release" and omni.release.auditor == "release_audit.py"
    assert (omni.adapter_dir / omni.release.auditor).is_file()
    afd = registry["afd-plugin"]
    assert afd.mode == "auto_merge" and afd.auto_merge
    jiuwen = registry["jiuwenswarm"]
    assert jiuwen.enabled and jiuwen.mode == "auto_merge" and jiuwen.auto_merge
    assert all(registry[repo].calibration_set for repo in ("vllm-omni", "afd-plugin", "jiuwenswarm"))
    assert registry["general"].intake.merged_prs is False


@pytest.mark.parametrize("section,message", [
    ({"enabled": True, "mode": "yolo"}, "mode must be one of"),
    ({"enabled": True, "mode": "auto_merge", "upstream_visibility": "private",
      "calibration_set": "x"}, "private upstream can only run in shadow"),
    ({"enabled": True, "mode": "auto_merge"}, "requires a calibration_set"),
    ({"enabled": True, "release": {"trigger": "tag_pattern"}}, "tag_pattern is required"),
    ({"enabled": True, "release": {"auditor": "missing.py"}}, "auditor does not exist"),
    ({"enabled": True, "knowledge_dir": "repos/other"}, "must equal the adapter repo_subdir"),
    ({"enabled": True, "surprise": 1}, "unknown keys"),
    ({"enabled": "yes"}, "must be true or false"),
    ({"enabled": True, "circuit_breaker": {"retire_ratio": 2}}, "out of range"),
])
def test_invalid_lifecycle_sections_are_refused(tmp_path, section, message):
    with pytest.raises(LifecycleConfigError, match=message):
        parse_lifecycle(_adapter(tmp_path, section))


def test_private_upstream_never_publishes(tmp_path):
    lifecycle = parse_lifecycle(_adapter(tmp_path, {"enabled": True, "upstream_visibility": "private"}))
    assert not lifecycle.publishes and not lifecycle.auto_merge


def test_lifecycle_section_is_human_only(tmp_path):
    adapter = _adapter(tmp_path, {"enabled": True})
    with pytest.raises(AdapterError, match="high-risk"):
        update_manifest(adapter, "knowledge_lifecycle", {"enabled": True, "mode": "auto_merge"},
                               actor="agent")


# -- ledger ----------------------------------------------------------------------

def test_ledger_lease_is_exclusive_until_stale(tmp_path):
    clock = Clock()
    a = Ledger(tmp_path / "kb.db", clock=clock)
    b = Ledger(tmp_path / "kb.db", clock=clock)
    owner = a.acquire_lease("a", ttl=60)
    with pytest.raises(LeaseError):
        b.acquire_lease("b", ttl=60)
    clock.now += 61
    assert b.acquire_lease("b", ttl=60) == "b"
    with pytest.raises(LeaseError):
        a.heartbeat(owner)


def test_ledger_generations_events_and_repo_isolation(tmp_path):
    ledger = Ledger(tmp_path / "kb.db", clock=Clock())
    ledger.ensure_repo("demo", "shadow")
    ledger.ensure_repo("other", "shadow")
    assert ledger.record_event("demo", "merged_pr", "7", {"n": 7}) is not None
    assert ledger.record_event("demo", "merged_pr", "7", {"n": 7}) is None  # idempotent
    assert ledger.bump_generation("demo", pause=True, reason="breaker") == 2
    assert ledger.repo_state("demo")["paused"] == 1
    assert ledger.repo_state("other")["generation"] == 1  # untouched
    assert ledger.resume("demo") == 3 and ledger.repo_state("demo")["paused"] == 0
    cs = ledger.create_changeset("demo", "intake")
    assert ledger.changeset(cs)["generation"] == 3
    ledger.record_retirement("demo", "DEMO-1a", "repos/demo/rules.md", "v1")
    assert [r["rule_id"] for r in ledger.purge_eligible("demo", "v2")] == ["DEMO-1a"]
    assert ledger.purge_eligible("demo", "v1") == []


# -- signing ---------------------------------------------------------------------

def test_signing_roundtrip_purpose_binding_and_key_permissions(tmp_path):
    key = generate_private_key(tmp_path / "k.pem")
    assert os.stat(tmp_path / "k.pem").st_mode & 0o077 == 0
    public = load_public_key(public_key_text(key.public_key()))
    envelope = sign("kb-gate-verdict", {"pr": 1, "head": "a" * 40}, key)
    assert verify("kb-gate-verdict", envelope, public) == {"pr": 1, "head": "a" * 40}
    with pytest.raises(SignatureError, match="signed for"):
        verify("kb-outbox-item", envelope, public)  # no cross-purpose replay
    forged = {**envelope, "payload": {"pr": 2, "head": "a" * 40}}
    with pytest.raises(SignatureError, match="does not verify"):
        verify("kb-gate-verdict", forged, public)
    other = generate_private_key(tmp_path / "o.pem")
    with pytest.raises(SignatureError, match="different key"):
        verify("kb-gate-verdict", sign("kb-gate-verdict", {}, other), public)
    with pytest.raises(SignatureError, match="refusing to overwrite"):
        generate_private_key(tmp_path / "k.pem")
    os.chmod(tmp_path / "k.pem", 0o644)
    with pytest.raises(SignatureError, match="readable by group"):
        load_private_key(tmp_path / "k.pem")


# -- outbox ----------------------------------------------------------------------

@pytest.fixture
def world(tmp_path):
    clock = Clock()
    key = generate_private_key(tmp_path / "service.pem")
    ledger = Ledger(tmp_path / "state" / "kb.db", clock=clock)
    ledger.ensure_repo("demo", "auto_merge")
    outbox = Outbox(tmp_path / "state", key, ledger, clock=clock)
    public = load_public_key(public_key_text(key.public_key()))
    return clock, ledger, outbox, public, tmp_path / "state"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _check(world, item, **kw):
    clock, _ledger, _outbox, public, state = world
    options = {"repo_publishes": True, "repo_auto_merge": True}
    options.update(kw)
    return check_item(_read(state / "outbox" / f"{item.id}.json"), _read(state / "outbox" / "control.json"),
                      public, now=clock.now, **options)


def test_publisher_accepts_a_fresh_item(world):
    _clock, _ledger, outbox, _public, _state = world
    item = outbox.issue("demo", "merge", {"pr": 5, "head": "b" * 40})
    outbox.refresh_control()
    assert _check(world, item).body["pr"] == 5


def test_generation_bump_voids_everything_issued_before_it(world):
    _clock, ledger, outbox, _public, _state = world
    merge = outbox.issue("demo", "merge", {"pr": 5})
    close = outbox.issue("demo", "close", {"pr": 5})
    ledger.bump_generation("demo", pause=False, reason="")  # rollback / shadow switch
    outbox.refresh_control()
    with pytest.raises(OutboxError, match="stale generation"):
        _check(world, merge)
    assert _check(world, close).kind == "close"  # stopping is always allowed
    global_old = outbox.issue("demo", "open_pr", {})
    ledger.bump_generation("*", pause=False, reason="")
    outbox.refresh_control()
    with pytest.raises(OutboxError, match="stale generation"):
        _check(world, global_old)


@pytest.mark.parametrize("case,message", [
    ("expired", "expired"),
    ("stale_control", "control record is stale"),
    ("paused", "paused"),
    ("private", "private upstream"),
    ("shadow", "not in auto_merge"),
])
def test_publisher_refusals(world, case, message):
    clock, ledger, outbox, _public, _state = world
    kw = {}
    item = outbox.issue("demo", "merge", {"pr": 5})
    if case == "paused":
        ledger.bump_generation("demo", pause=True, reason="x")
        item = outbox.issue("demo", "merge", {"pr": 5})
    outbox.refresh_control()
    if case == "expired":
        clock.now += 31 * 60
        outbox.refresh_control()
    if case == "stale_control":
        clock.now += CONTROL_MAX_AGE + 1
    if case == "private":
        kw["repo_publishes"] = False
    if case == "shadow":
        kw["repo_auto_merge"] = False
    with pytest.raises(OutboxError, match=message):
        _check(world, item, **kw)


def test_forged_item_is_refused(world):
    _clock, _ledger, outbox, _public, state = world
    item = outbox.issue("demo", "open_pr", {"title": "ok"})
    outbox.refresh_control()
    path = state / "outbox" / f"{item.id}.json"
    envelope = _read(path)
    envelope["payload"]["body"]["title"] = "evil"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(SignatureError):
        _check(world, item)


def test_acks_must_be_signed_by_the_publisher(world, tmp_path):
    _clock, ledger, outbox, _public, state = world
    publisher = generate_private_key(tmp_path / "publisher.pem")
    publisher_public = load_public_key(public_key_text(publisher.public_key()))
    item = outbox.issue("demo", "open_pr", {})
    acks = state / "inbox" / "acks"
    acks.mkdir(parents=True)
    (acks / f"{item.id}.json").write_text(json.dumps(
        sign("kb-ack", {"item_id": item.id, "ok": True, "pr": 9}, publisher)), encoding="utf-8")
    impostor = generate_private_key(tmp_path / "impostor.pem")
    (acks / "forged.json").write_text(json.dumps(
        sign("kb-ack", {"item_id": item.id, "ok": False}, impostor)), encoding="utf-8")
    results = outbox.collect_acks(publisher_public)
    assert any(r.get("pr") == 9 for r in results)
    assert any("invalid" in r for r in results)
    assert ledger.outbox_items("demo", "acked")[0]["id"] == item.id
    assert (acks / "forged.invalid").exists()


# -- CLI -------------------------------------------------------------------------

def test_kb_cli_pause_resume_refreshes_signed_control(tmp_path, monkeypatch, capsys):
    from infermatrix_copilot.cli.entry import main as cli_main

    key_path = tmp_path / "service.pem"
    assert cli_main(["kb", "keygen", "--out", str(key_path)]) == 0
    public = load_public_key(capsys.readouterr().out.strip())
    monkeypatch.setenv("KB_SIGNING_KEY", str(key_path))
    monkeypatch.setenv("KB_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("ADAPTERS_DIR", str(ROOT / "adapters"))
    assert cli_main(["kb", "pause", "--repo", "vllm-omni", "--reason", "drill"]) == 0
    control = verify("kb-control", _read(tmp_path / "state" / "outbox" / "control.json"), public)
    assert control["repos"]["vllm-omni"]["paused"] is True
    assert cli_main(["kb", "resume", "--repo", "vllm-omni"]) == 0
    control = verify("kb-control", _read(tmp_path / "state" / "outbox" / "control.json"), public)
    assert control["repos"]["vllm-omni"]["paused"] is False
    assert control["repos"]["vllm-omni"]["generation"] == 3
    assert cli_main(["kb", "pause", "--repo", "nope", "--reason", "x"]) == 2
    capsys.readouterr()
    assert cli_main(["kb", "status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert {row["repo"] for row in status["repos"]} >= {"vllm-omni", "afd-plugin", "*"}


def test_mode_round_trip_voids_items_issued_before_it(world):
    _clock, ledger, outbox, _public, _state = world
    merge = outbox.issue("demo", "merge", {"pr": 5})
    assert ledger.ensure_repo("demo", "shadow") is True
    assert ledger.ensure_repo("demo", "shadow") is False  # no change, no bump
    assert ledger.ensure_repo("demo", "auto_merge") is True
    outbox.refresh_control()
    with pytest.raises(OutboxError, match="stale generation"):
        _check(world, merge)


@pytest.mark.parametrize("mode", ["disabled", "shadow"])
@pytest.mark.parametrize("kind", ["open_pr", "open_companion_pr", "merge", "post_findings"])
def test_only_auto_merge_repos_get_non_stop_writes(world, mode, kind):
    _clock, ledger, outbox, _public, _state = world
    ledger.ensure_repo("demo", mode)
    item = outbox.issue("demo", kind, {})
    stop = outbox.issue("demo", "close", {})
    outbox.refresh_control()
    with pytest.raises(OutboxError, match="not in auto_merge"):
        _check(world, item)
    assert _check(world, stop).kind == "close"


def test_overlapping_refresh_cannot_undo_a_completed_pause(world, tmp_path):
    """Two "processes" (threads with their own ledger connections): a refresh
    that read the pre-pause state must not publish after the pause does."""
    import threading

    clock, _ledger, outbox, public, state = world
    stale_merge = outbox.issue("demo", "merge", {"pr": 5})
    key = outbox._key
    read_done, may_write = threading.Event(), threading.Event()
    errors: list[BaseException] = []

    def refresher():
        try:
            slow = Outbox(state, key, Ledger(state / "kb.db", clock=clock), clock=clock)
            original = slow._control_payload

            def stalled():
                payload = original()      # reads the pre-pause state ...
                read_done.set()
                may_write.wait(timeout=5)  # ... then stalls before writing
                return payload

            slow._control_payload = stalled
            slow.refresh_control()
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    def pauser():
        try:
            ledger = Ledger(state / "kb.db", clock=clock)
            Outbox(state, key, ledger, clock=clock).transition(
                lambda: ledger.bump_generation("demo", pause=True, reason="breaker"))
        except BaseException as exc:  # pragma: no cover
            errors.append(exc)

    first = threading.Thread(target=refresher)
    first.start()
    assert read_done.wait(timeout=5)
    second = threading.Thread(target=pauser)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive()  # the pause waits for the in-flight publication
    may_write.set()
    first.join(timeout=5)
    second.join(timeout=5)
    assert not errors, errors
    control = verify("kb-control", _read(state / "outbox" / "control.json"), public)
    assert control["repos"]["demo"]["paused"] is True
    with pytest.raises(OutboxError):
        _check(world, stale_merge)
