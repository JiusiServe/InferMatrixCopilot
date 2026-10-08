"""Strict receipts must cover the actual configured tree consumed by the child."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.app.run_service import RunService
from infermatrix_copilot.kb_service.containment import record_hold
from infermatrix_copilot.kb_service.maintenance_units import page_units
from infermatrix_copilot.knowledge_service.containment import knowledge_availability_check
from infermatrix_copilot.knowledge_view import KnowledgeView
from test_kb_containment import containment, finding, install


@pytest.mark.parametrize("same_repo", [False, True])
def test_strict_custom_tree_scope_binds_actual_bytes(containment, tmp_path, monkeypatch, same_repo):
    c = containment
    install(c)
    monkeypatch.setattr(KnowledgeView, "current", classmethod(lambda cls: c.view))
    repo = "demo" if same_repo else "custom-only"
    custom = tmp_path / "configured-knowledge"
    page = f"repos/{repo}/component/rules.md"
    target = custom / page
    target.parent.mkdir(parents=True)
    text = "## CUSTOM-1a — configured contract\n\nPreserve the configured capacity of eight.\n"
    target.write_text(text)
    (target.parent.parent / "_index.md").write_text("# Custom repository\n")
    (custom / "AGENTS.md").write_text("# Configured knowledge\n")
    if same_repo:
        (c.view.root / "repos/demo/_index.md").write_text("# Packaged repository\n")
    run_id = "strict-configured"
    run_root = tmp_path / "runs"
    run = run_root / run_id
    run.mkdir(parents=True)
    (run / "request.json").write_text(json.dumps({"repo": repo}))
    core = SimpleNamespace(run_root=run_root,
                           settings=SimpleNamespace(knowledge_dir=custom),
                           knowledge_maintenance=c.cfg)

    pin = RunService._pin_knowledge(core, run_id)
    receipt = pin["knowledge_usage"]
    assert pin["snapshot"] == receipt["snapshot"] == "unverified"
    assert pin["knowledge_dir"] == str(custom.resolve())
    assert any(row["page"] == page and row["block_id"] == "CUSTOM-1a"
               for row in receipt["scope_units"])
    stored = json.loads((Path(c.cfg["state_dir"]) / "usage" /
                         f"{receipt['receipt_id']}.json").read_text())
    assert stored["knowledge_root"] == str(custom.resolve())
    assert knowledge_availability_check(receipt, config=c.cfg)["allowed"]

    c.rt.registry[repo] = SimpleNamespace(enabled=True, auto_merge=True)
    unit = next(row for row in page_units(page, text, repo, "unverified")
                if row["block_id"] == "CUSTOM-1a")
    record_hold(c.rt, unit, finding(), enforce=True)
    install(c)
    denied = knowledge_availability_check(receipt, config=c.cfg)
    assert not denied["allowed"] and denied["reassessment_required"]
    # The original reservation receipt remains fixed across retries.
    assert RunService._pin_knowledge(core, run_id) == pin
