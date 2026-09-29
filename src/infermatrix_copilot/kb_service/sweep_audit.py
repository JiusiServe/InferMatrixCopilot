"""The release audit inside each sweep, and the adapter-baseline companion PR.

A repository whose adapter configures ``release.auditor`` has its plugin run
(generated-baseline mode) for the sweep's upstream SHA pair:

* knowledge-document issues become per-page hints for the sweep's generator;
* reconciliation findings (the committed adapter baseline lags the audited
  upstream) do not block the sweep. Instead the service drafts the baseline
  update as a companion PR: the plugin names its baseline file
  (``baseline_file``, relative to the adapter) and the audit supplies the
  generated values. Only the ``upstream:`` and ``inventories:`` blocks are
  replaced, so everything else in the file (comments included) is kept.
  People review and merge it; the sweep never waits for it.

An audit that fails goes to people once per sweep; the sweep runs without hints.
"""

from __future__ import annotations

import tempfile

import yaml

from ..knowledge_service.release_audit import ReleaseAuditPluginError, run_release_audit

BLOCKS = ("upstream", "inventories")


def audit_sweep(rt, lifecycle, sweep: dict, upstream, base_sha: str) -> tuple[dict[str, list[dict]], object | None]:
    """(hints per knowledge-relative page, the audit result or None). The audit
    reads ``base_sha`` of the knowledge repository, materialized for it: the
    same revision the sweep then runs on (never a checkout or snapshot that
    may lag main)."""
    if not lifecycle.release.auditor or lifecycle.adapter_dir is None:
        return {}, None
    if not sweep.get("from_sha") or sweep.get("from_sha") == sweep.get("to_sha"):
        return {}, None  # nothing moved upstream (a fallback re-check)
    try:
        with tempfile.TemporaryDirectory(prefix="kb-audit-") as scratch:
            project = rt.knowledge.export(base_sha, scratch)
            result = run_release_audit(
                lifecycle.adapter_dir, lifecycle.release.auditor, upstream_repo=upstream.path,
                from_ref=sweep["from_sha"], to_ref=sweep["to_sha"], knowledge_root=project / "knowledge",
                project_root=project)
    except (ReleaseAuditPluginError, Exception) as exc:  # noqa: BLE001 - never blocks the sweep
        key = f"audit_failed:{sweep.get('tag')}:{sweep.get('to_sha')}"
        if not rt.ledger.get_cursor(lifecycle.repo, key):
            rt.ledger.set_cursor(lifecycle.repo, key, "1")
            rt.ledger.enqueue_human(lifecycle.repo, f"release audit for {sweep.get('tag')} failed: {exc}")
        return {}, None
    hints: dict[str, list[dict]] = {}
    for issue in result.issues:
        page = str(issue.get("document") or "").removeprefix("knowledge/")
        if page:
            hints.setdefault(page, []).append(issue)
    return hints, result


def _replace_block(text: str, key: str, value) -> str:
    """Replace one top-level YAML block. It runs to the next top-level key; a
    column-0 comment inside it belongs to it, but comments and blank lines
    right before the next key belong to that key and are kept."""
    dumped = yaml.safe_dump({key: value}, sort_keys=False, default_flow_style=False)
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith(f"{key}:")), None)
    if start is None:
        return text.rstrip("\n") + "\n\n" + dumped
    end = next((i for i in range(start + 1, len(lines))
                if lines[i][:1] not in (" ", "\t", "#", "\n", "\r", "")), len(lines))
    while end - 1 > start and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
        end -= 1
    tail = "".join(lines[end:])
    return "".join(lines[:start]) + dumped + ("\n" if tail and not tail.startswith("\n") else "") + tail


def baseline_text(committed: str, generated: dict) -> str:
    text = committed
    for key in BLOCKS:
        if key in generated:
            text = _replace_block(text, key, generated[key])
    return text


def stage_baseline_companion(rt, lifecycle, owner: str, sweep: dict, result, base_sha: str) -> str | None:
    """Draft the adapter-baseline update once per sweep; None when not needed."""
    from .companion import publish_companion

    if result is None or not result.reconciliation or lifecycle.adapter_dir is None:
        return None
    baseline_file = str(result.data.get("baseline_file") or "")
    if not baseline_file or ".." in baseline_file.split("/") or baseline_file.startswith("/"):
        return None
    key = f"baseline:{sweep.get('tag')}:{sweep.get('to_sha')}"
    for changeset in rt.ledger.changesets(lifecycle.repo, ("companion_staged", "pr_requested", "companion_open",
                                                           "merged", "closed", "shadow_recorded")):
        if changeset["kind"] == "companion" and changeset["detail"].get("baseline_for") == key:
            return None  # already drafted for this sweep
    path = f"adapters/{lifecycle.adapter_dir.name}/{baseline_file}"
    main = base_sha  # the revision the audit and the sweep use
    committed = rt.knowledge.show(main, path)
    if committed is None:
        return None
    updated = baseline_text(committed, result.generated_baseline)
    if updated == committed:
        return None
    companion_id = rt.ledger.new_changeset_id(lifecycle.repo, "companion")
    rt.save_changeset_files(companion_id, {"base_sha": main, "files": {path: updated}, "deleted": [],
                                           "evidence": []})
    rt.ledger.stage_intake(owner, lifecycle.repo, companion_id, kind="companion", status="companion_staged",
                           verdicts=[], drafted_events=[],
                           human_reason=f"review and merge the adapter baseline update for {sweep.get('tag')}",
                           detail={"for_changeset": "", "baseline_for": key, "base_sha": main,
                                   "reconciliation": list(result.reconciliation)[:50]})
    publish_companion(rt, lifecycle, companion_id)
    return companion_id
