"""Knowledge snapshot activation: what reviews read, switched atomically.

Every merged knowledge change (from the service or from people) becomes an
immutable snapshot ``snapshots/<merge sha>/`` holding ``knowledge/`` and a
``MANIFEST.json``. Before ``active`` is switched to it, the snapshot must load
as a verified ``KnowledgeView``, have no tree-level issues, and every
repository's ``_routes.yaml`` must load. The switch is an atomic symlink
replace; rollback points ``active`` back at an earlier snapshot. The latest
``KEEP`` snapshots are kept, and so is anything ``active`` points at.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..knowledge_service.l1 import check_tree
from ..knowledge_view import KnowledgeView, _load_view, build_manifest
from .outbox import atomic_write_json

KEEP = 10


class ActivationError(RuntimeError):
    """A snapshot failed its checks; ``active`` was not switched."""


@contextmanager
def activation_lock(state_dir: Path) -> Iterator[None]:
    """Serialises activation, rollback and the scheduler's "read the rollback
    pin, then maybe activate" decision across processes, so the symlink, the
    activation record and the pin never disagree and a tick cannot undo a
    rollback that finished while it was deciding."""
    state_dir.mkdir(parents=True, exist_ok=True)
    fd = os.open(state_dir / ".activation.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def snapshots_dir(state_dir: Path) -> Path:
    return state_dir / "snapshots"


def active_link(state_dir: Path) -> Path:
    return state_dir / "active"


def build_snapshot(state_dir: Path, sha: str, files: dict[str, str], *, extra: dict[str, str]) -> Path:
    """Write the snapshot directory (idempotent: an existing one is reused).
    ``files`` are the governed knowledge texts; ``extra`` any other files the
    tree needs to be served (e.g. AGENTS.md, README.md)."""
    target = snapshots_dir(state_dir) / sha
    if (target / "MANIFEST.json").is_file():
        return target
    staging = Path(tempfile.mkdtemp(prefix=f".{sha}.", dir=snapshots_dir(state_dir).mkdir(
        parents=True, exist_ok=True) or snapshots_dir(state_dir)))
    try:
        root = staging / "knowledge"
        for rel, text in {**extra, **files}.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        atomic_write_json(staging / "MANIFEST.json", build_manifest(root, sha))
        os.replace(staging, target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def verify_snapshot(snapshot: Path) -> KnowledgeView:
    from ..knowledge_view import KnowledgeViewError

    _load_view.cache_clear()
    try:
        view = _load_view(str(snapshot.resolve()))
    except KnowledgeViewError as exc:
        raise ActivationError(f"snapshot does not load: {exc}") from exc
    # _load_view checks names and structure; hash EVERY file now, since not
    # every consumer reads through KnowledgeView.path
    for rel in view.files or {}:
        try:
            view.path(rel)
        except (KnowledgeViewError, FileNotFoundError, ValueError) as exc:
            raise ActivationError(f"snapshot content does not match its manifest: {exc}") from exc
    files = {p.relative_to(view.root).as_posix(): p.read_text(encoding="utf-8")
             for p in view.root.rglob("*") if p.is_file() and p.suffix in (".md", ".yaml")}
    issues = check_tree({k: v for k, v in files.items() if k.startswith(("repos/", "general/"))})
    if issues:
        raise ActivationError(f"snapshot has tree issues: {[i.to_dict() for i in issues[:5]]}")
    from ..direct_routing import _load_routes

    for repo_dir in sorted((view.root / "repos").iterdir()):
        if (repo_dir / "_routes.yaml").is_file():
            try:
                _load_routes(view, repo_dir.name)
            except Exception as exc:
                raise ActivationError(f"{repo_dir.name}/_routes.yaml does not load: {exc}") from exc
    return view


def switch_active(state_dir: Path, snapshot: Path) -> None:
    link = active_link(state_dir)
    tmp = link.with_name(f".active.{os.getpid()}")
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    tmp.symlink_to(snapshot.resolve())
    os.replace(tmp, link)


def activate(rt, sha: str, *, locked: bool = False) -> Path:
    """Build, verify and switch to the snapshot of knowledge at ``sha``."""
    if not locked:
        with activation_lock(rt.state_dir):
            return activate(rt, sha, locked=True)
    files = rt.knowledge.knowledge_files(sha)
    extra = rt.knowledge.top_level_knowledge(sha)
    snapshot = build_snapshot(rt.state_dir, sha, files, extra=extra)
    verify_snapshot(snapshot)
    switch_active(rt.state_dir, snapshot)
    rt.ledger.record_activation(sha, {"files": len(files)})
    rt.ledger.set_cursor("*", "rollback_pin", "")
    prune(rt.state_dir)
    return snapshot


def rollback(rt, sha: str) -> Path:
    """Point ``active`` at an earlier snapshot and pin it: the scheduler will not
    re-activate the main it was rolled back from, only a LATER main."""
    with activation_lock(rt.state_dir):
        snapshot = snapshots_dir(rt.state_dir) / sha
        if not (snapshot / "MANIFEST.json").is_file():
            raise ActivationError(f"no snapshot for {sha}")
        verify_snapshot(snapshot)
        switch_active(rt.state_dir, snapshot)
        rt.ledger.record_activation(sha, {"rollback": True})
        rt.ledger.set_cursor("*", "rollback_pin",
                             json.dumps({"snapshot": sha, "main": rt.knowledge.main_sha()}))
        return snapshot


def prune(state_dir: Path, keep: int = KEEP) -> None:
    root = snapshots_dir(state_dir)
    link = active_link(state_dir)
    active = link.resolve() if link.is_symlink() else None
    snapshots = sorted((p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    for old in snapshots[keep:]:
        if active is not None and old.resolve() == active:
            continue
        shutil.rmtree(old, ignore_errors=True)
