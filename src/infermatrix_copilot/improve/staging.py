"""Item staging for shadow experiments (design §8.2, "before isolation").

`stage_item` does, with network access and the engine's own read-only scope,
everything a shadow run must not: resolve the PR's base ref and head via gh,
fetch both into the source repository's pinned refs, compute the pinned
three-dot diff, assemble the PR context bundle (no discussion), take the
gate report and the CI checks, then build the independent shadow clone at
the head with the base tip published inside it. The result is a snapshot
dict the `pr_context_source=snapshot` steps consume verbatim; its bytes are
hashed so arm and incumbent can be proven to have seen the same input, and
it is recorded as a `decision` (`result.type="item_staged"`) with the
snapshot as a blob when a trace store is bound.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ..trace_store import current_store
from .shadow import make_shadow_clone

ITEM_RE = re.compile(r"^(?P<repo>[^#]+)#(?P<pr>\d+)(?:@(?P<head>[0-9a-f]{7,40}))?$")


class StagingError(RuntimeError):
    pass


def parse_item(item: str) -> tuple[str, int, str]:
    m = ITEM_RE.match(str(item or "").strip())
    if not m:
        raise StagingError(f"item must look like repo#pr@head_sha, got {item!r}")
    return m.group("repo"), int(m.group("pr")), (m.group("head") or "")


def snapshot_digest(snapshot: dict) -> str:
    """sha256 over the snapshot's INPUT fields (what a review sees), stable
    across the shadow dir and the timestamp."""
    payload = {k: snapshot.get(k) for k in ("repo", "pr", "base_ref", "base_sha", "head_sha", "diff",
                                             "context_text", "gate_report", "pr_state", "ci_checks")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
                          .encode("utf-8")).hexdigest()


def stage_item(ctx: Any, item: str, *, shadow_root: Path) -> dict:
    """Stage one item; returns the snapshot dict (also written to
    `<run_dir>/snapshots/<item>.json`). Raises StagingError on any failure —
    an item that cannot be staged faithfully is excluded, never approximated."""
    from ..engine.steps.pr.fetch import (_fetch_pinned, _pinned_diff, _pr_context_bundle,
                                         _resolve_pr_head, ci_checks_for, gate_report_for)

    repo_name, pr, pinned_head = parse_item(item)
    repo = ctx.settings.repo_path(repo_name)
    if repo is None or not Path(repo).is_dir():
        raise StagingError(f"unknown repository {repo_name!r} (REPO_PATHS)")
    repo = Path(repo)
    base_ref, head_sha, err = _resolve_pr_head(repo, pr)
    if err or not head_sha:
        raise StagingError(f"{item}: {err or 'head unresolvable'}")
    if pinned_head and not head_sha.startswith(pinned_head):
        raise StagingError(f"{item}: PR head is {head_sha[:12]}, not the pre-registered {pinned_head[:12]}")
    base_sha, err = _fetch_pinned(repo, pr, base_ref, head_sha, ctx.run_dir.name)
    if err:
        raise StagingError(f"{item}: {err}")
    diff, detail, err = _pinned_diff(repo, base_sha, head_sha)
    if err:
        raise StagingError(f"{item}: {err}")
    # the context bundle without discussion, whatever the run's own mode: a
    # shadow arm must never see the review threads (the eval leakage policy)
    bundle_ctx = _BundleCtx(ctx.settings.model_copy(update={"pr_context_mode": "no_discussion"}),
                            ctx.state, ctx.trace)
    context_text = _pr_context_bundle(bundle_ctx, str(repo), pr)
    gate_report, pr_state, available = gate_report_for(repo, pr)
    if not available:
        raise StagingError(f"{item}: gate report unavailable (gh pr view failed); refusing to stage without it")
    ci_checks = ci_checks_for(repo, pr)
    if ci_checks is None:
        raise StagingError(f"{item}: CI checks unavailable (gh pr checks failed); refusing to stage without them")
    shadow_dir = shadow_root / f"{repo_name}-{pr}-{head_sha[:12]}"
    ok, note = make_shadow_clone(repo, shadow_dir, head_sha=head_sha, base_tip=base_sha, base_ref_name=base_ref)
    if not ok:
        raise StagingError(f"{item}: {note}")
    snapshot = {
        "item": item, "repo": repo_name, "pr": pr, "base_ref": base_ref, "base_sha": base_sha,
        "head_sha": head_sha, "diff": diff, "diff_note": detail, "context_text": context_text,
        "gate_report": gate_report, "pr_state": pr_state, "ci_checks": ci_checks,
        "shadow_dir": str(shadow_dir), "clone_note": note,
    }
    snapshot["snapshot_sha256"] = snapshot_digest(snapshot)
    out_dir = Path(ctx.run_dir) / "snapshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", item)
    (out_dir / f"{safe}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    store = current_store()
    if store is not None:
        try:
            store.append("decision", inputs={"snapshot": json.dumps(snapshot, ensure_ascii=False, sort_keys=True)},
                         result={"type": "item_staged", "item": item, "repo": repo_name, "pr": pr,
                                 "head_sha": head_sha, "base_sha": base_sha, "base_ref": base_ref,
                                 "snapshot_sha256": snapshot["snapshot_sha256"], "shadow_dir": str(shadow_dir)},
                         context={"item": item})
        except Exception:  # noqa: BLE001 - recording never fails staging
            pass
    return snapshot


class _BundleCtx:
    """The subset of StepContext `_pr_context_bundle` reads."""

    def __init__(self, settings, state, trace):
        self.settings, self.state, self.trace = settings, state, trace
