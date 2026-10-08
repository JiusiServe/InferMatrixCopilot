"""Source observation never substitutes for a semantic knowledge review."""
from dataclasses import replace
import json

import pytest

from infermatrix_copilot.kb_service.config import ReleaseConfig
from infermatrix_copilot.kb_service.maintenance import operational_status
from infermatrix_copilot.kb_service.maintenance_store import MaintenanceStore
from infermatrix_copilot.kb_service.scheduler import Scheduler
from test_kb_maintenance_flow import configured_runtime


@pytest.mark.parametrize("trigger,expected", [("github_release", "no_code_update"),
                                               ("none", "not_observed")])
def test_release_observation_is_separate_from_semantic_coverage(tmp_path, trigger, expected):
    rt, lifecycle, _source, _unit, _now = configured_runtime(tmp_path, lambda *_: pytest.fail("reporting must not call a model"))
    try:
        lifecycle = replace(lifecycle, release=ReleaseConfig(trigger=trigger))
        rt.registry[lifecycle.repo] = lifecycle
        rt.github.latest_release = lambda _: {"tag": "v1"}
        rt.ledger.set_cursor(lifecycle.repo, "release", "v1")
        rt.ledger.set_cursor(lifecycle.repo, "sweep_baseline", "a" * 40)
        rt.ledger.set_cursor(lifecycle.repo, "last_sweep_at", str(rt.clock()))
        scheduler = Scheduler(rt)
        scheduler._due = lambda key, _: key.startswith("release:")
        scheduler._repo_tick(lifecycle)

        observation = json.loads(rt.ledger.get_cursor(lifecycle.repo, "maintenance_source_observation"))
        assert observation["status"] == expected
        assert observation["scope"] == "release_baseline"
        assert observation["from_sha"] == observation["to_sha"] == "a" * 40
        assert observation["observation_status"] == ("observed" if trigger == "github_release" else "disabled")
        assert observation["observed_tag"] == ("v1" if trigger == "github_release" else "")
        store = MaintenanceStore(rt.ledger, lease_owner=rt.lease_owner)
        result = operational_status(rt, store, [])
        assert result["source_updates"][0]["code_update_status"] == expected
        assert store.report(now=rt.clock())["coverage"]["successful"] == 0
        assert not store.runs()
    finally:
        rt.ledger.close()


@pytest.mark.parametrize("trigger,lookup_status", [("github_release", "missing_release"),
                                                   ("tag_pattern", "missing_matching_tag")])
def test_missing_upstream_release_does_not_claim_cached_baseline_was_observed(tmp_path, trigger, lookup_status):
    rt, lifecycle, _source, _unit, _now = configured_runtime(tmp_path, lambda *_: pytest.fail("reporting must not call a model"))
    try:
        lifecycle = replace(lifecycle, release=ReleaseConfig(trigger=trigger, tag_pattern="v*"))
        rt.registry[lifecycle.repo] = lifecycle
        rt.github.latest_release = lambda _: None
        rt.github.tags = lambda *_: []
        rt.ledger.set_cursor(lifecycle.repo, "release", "v1")
        rt.ledger.set_cursor(lifecycle.repo, "sweep_baseline", "a" * 40)
        rt.ledger.set_cursor(lifecycle.repo, "last_sweep_at", str(rt.clock()))
        scheduler = Scheduler(rt)
        scheduler._due = lambda key, _: key.startswith("release:")
        scheduler._repo_tick(lifecycle)

        observation = json.loads(rt.ledger.get_cursor(lifecycle.repo, "maintenance_source_observation"))
        assert observation["status"] == "not_observed"
        assert observation["observation_status"] == lookup_status
        assert observation["observed_tag"] == ""
        assert observation["from_sha"] == observation["to_sha"] == "a" * 40
        result = operational_status(rt, MaintenanceStore(rt.ledger, lease_owner=rt.lease_owner), [])
        assert result["source_updates"][0]["code_update_status"] == "not_observed"
    finally:
        rt.ledger.close()


def test_resuming_saved_sweep_does_not_claim_a_fresh_upstream_observation(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service import scheduler as scheduler_module

    rt, lifecycle, _source, _unit, _now = configured_runtime(tmp_path, lambda *_: pytest.fail("reporting must not call a model"))
    try:
        lifecycle = replace(lifecycle, release=ReleaseConfig(trigger="github_release"))
        rt.registry[lifecycle.repo] = lifecycle
        rt.github.latest_release = lambda _: pytest.fail("saved sweep resumes without a fresh lookup")
        rt.ledger.set_cursor(lifecycle.repo, "release", "v1")
        rt.ledger.set_cursor(lifecycle.repo, "sweep_baseline", "a" * 40)
        rt.ledger.set_cursor(lifecycle.repo, "sweep_progress", json.dumps({"key": ["v2", "a" * 40, "b" * 40]}))
        monkeypatch.setattr(scheduler_module, "audit_sweep", lambda *_: ([], None))
        monkeypatch.setattr(scheduler_module, "stage_baseline_companion", lambda *_: None)
        resumed = []
        monkeypatch.setattr(scheduler_module, "run_sweep", lambda *_args, **_kwargs:
                            resumed.append(_args[3]) or {"changesets": [], "breaker": False})
        scheduler = Scheduler(rt)
        scheduler._due = lambda key, _: key.startswith("release:")
        scheduler._repo_tick(lifecycle)

        assert resumed == [{"tag": "v2", "from_sha": "a" * 40, "to_sha": "b" * 40, "reason": "release"}]
        observation = json.loads(rt.ledger.get_cursor(lifecycle.repo, "maintenance_source_observation"))
        assert observation["status"] == "not_observed"
        assert observation["observation_status"] == "resuming_prior_sweep"
        assert observation["observed_tag"] == ""
        assert observation["to_sha"] == "b" * 40
    finally:
        rt.ledger.close()
