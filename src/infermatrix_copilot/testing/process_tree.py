"""Process-tree termination — port of the rebase agent's kill_test_tree.sh.

Kills a test process and every descendant (pytest workers hold GPU memory if
the root dies alone): BFS descendant collection, self-ancestor exclusion,
SIGTERM → grace → SIGKILL, survivor report.
"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from typing import Callable


def _log(msg: str) -> None:
    print(f"[kill_test_tree] {msg}", flush=True)


def _pgrep(args: list[str]) -> list[int]:
    try:
        out = subprocess.run(["pgrep", *args], capture_output=True, text=True,
                             timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [int(x) for x in out.split() if x.isdigit()]


def collect_descendants(pid: int,
                        children_of: Callable[[int], list[int]] | None = None
                        ) -> list[int]:
    """BFS over the child tree rooted at `pid` (inclusive), deduplicated."""
    children_of = children_of or (lambda p: _pgrep(["-P", str(p)]))
    tree, queue = {pid}, [pid]
    while queue:
        for child in children_of(queue.pop(0)):
            if child not in tree:
                tree.add(child)
                queue.append(child)
    return sorted(tree)


def _is_ancestor_of_self(pid: int) -> bool:
    """Walk our own parent chain via /proc/<pid>/stat — killing an ancestor
    would take this process down with the target."""
    current = os.getpid()
    while current > 1:
        if current == pid:
            return True
        try:
            stat = open(f"/proc/{current}/stat").read()
            # field 4 is ppid; comm (field 2) may contain spaces but is
            # parenthesized, so split after the closing paren
            current = int(stat.rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return False
    return False


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _proc_stat_ids(pid: int) -> tuple[int, int] | None:
    """(ppid, starttime) from ONE /proc/<pid>/stat read — a (pid, starttime)
    pair identifies a process across PID reuse, and reading the ppid in the
    same read lets callers verify ancestry atomically with the identity
    capture. None when unreadable (process gone, or no procfs)."""
    try:
        stat = open(f"/proc/{pid}/stat", "rb").read().decode(errors="replace")
        # comm (field 2) may contain spaces/parens; split after the LAST ")".
        # Fields after it start at field 3; ppid is field 4 → index 1,
        # starttime is field 22 → index 19.
        after = stat.rsplit(")", 1)[1].split()
        return int(after[1]), int(after[19])
    except (OSError, ValueError, IndexError):
        return None


def _start_time(pid: int) -> int | None:
    ids = _proc_stat_ids(pid)
    return None if ids is None else ids[1]


def kill_tree(pids: list[int], *, term_grace: float = 2.0,
              kill_grace: float = 1.0,
              kill: Callable[[int, int], None] | None = None,
              sleep: Callable[[float], None] = time.sleep,
              identity: dict[int, int | None] | None = None) -> list[int]:
    """SIGTERM every pid and its descendants, wait `term_grace`, SIGKILL the
    survivors, wait `kill_grace`. Returns pids still alive (ideally empty).

    `identity` optionally maps pid → the /proc starttime recorded when the pid
    was *observed* (e.g. by the runner's descendant-snapshot thread). A pid
    whose current starttime no longer matches was reused by an unrelated
    process and is silently dropped — this is what makes accumulate-only
    snapshots safe to kill from."""
    kill = kill or (lambda p, s: os.kill(p, s))
    provided = dict(identity or {})
    # a reused ROOT must be rejected before walking: its children belong to
    # the unrelated new holder and carry no recorded identity of their own
    roots = []
    for p in dict.fromkeys(pids):
        recorded = provided.get(p)
        if recorded is not None:
            born_now = _start_time(p)
            if born_now is not None and born_now != recorded:
                continue
        roots.append(p)
    candidates = sorted({d for p in roots for d in collect_descendants(p)})

    # a root can pass the pre-walk check, exit, and be reused DURING the
    # walk — its stranger children would enter as identity-less candidates.
    # So walked-up candidates are accepted only on an ancestry chain anchored
    # at a root whose identity holds AFTER the walk (re-read here); pids with
    # their own recorded identity are exempt (the per-pid baseline below
    # drops reused ones). Legacy roots without recorded identity keep the
    # historical behavior. The residual window is the stat-read-to-signal
    # gap, irreducible without pidfds.
    info = {p: _proc_stat_ids(p) for p in candidates}
    # `chain` holds ancestry ANCHORS: legacy roots (no identity knowledge —
    # historical behavior) and pids whose recorded identity matches their
    # post-walk stat read. A merely-recorded pid is still a TARGET (the
    # per-pid baseline below drops it if reused) but must not anchor
    # children without this re-verification.
    chain: set[int] = {r for r in roots if provided.get(r) is None}
    for p in candidates:
        rec = provided.get(p)
        if rec is not None and info.get(p) is not None and info[p][1] == rec:
            chain.add(p)
    changed = True
    while changed:
        changed = False
        for p in candidates:
            if p in chain or p in provided:
                continue
            ids = info.get(p)
            if ids is not None and ids[0] in chain:
                chain.add(p)
                changed = True
    candidates = [p for p in candidates if p in chain or p in provided]
    # capture identity BEFORE signalling: after the grace sleep a target's pid
    # may have been reaped and reused, and escalating SIGKILL by bare pid would
    # then hit an unrelated process
    baseline: dict[int, int | None] = {}
    targets = []
    for p in candidates:
        born_now = _start_time(p)
        recorded = provided.get(p)
        if recorded is not None and born_now is not None and born_now != recorded:
            continue  # pid reused since it was recorded — not our process
        baseline[p] = recorded if recorded is not None else born_now
        targets.append(p)
    if not targets:
        return []

    def same_process(pid: int) -> bool:
        born = _start_time(pid)
        if born is None or baseline[pid] is None:
            return _alive(pid)  # identity unverifiable — legacy pid-only check
        return born == baseline[pid]

    _log(f"Killing {len(targets)} process(es): {' '.join(map(str, targets))}")
    for pid in targets:
        try:
            kill(pid, signal.SIGTERM)
        except OSError:
            pass
    sleep(term_grace)
    survivors = [p for p in targets if _alive(p) and same_process(p)]
    if survivors:
        _log(f"{len(survivors)} survivor(s) after SIGTERM, sending SIGKILL...")
        for pid in survivors:
            try:
                kill(pid, signal.SIGKILL)
            except OSError:
                pass
        sleep(kill_grace)
    still_alive = [p for p in targets if _alive(p) and same_process(p)]
    if still_alive:
        _log(f"WARNING: {len(still_alive)} process(es) still alive: "
             f"{' '.join(map(str, still_alive))}")
    else:
        _log("All processes terminated successfully.")
    return still_alive


def kill_by_pattern(pattern: str, **kw) -> list[int]:
    """`pgrep -f pattern`, excluding this process's own ancestor chain, then
    `kill_tree`. Returns survivors ([] also when nothing matched)."""
    matches = [p for p in _pgrep(["-f", pattern]) if not _is_ancestor_of_self(p)]
    if not matches:
        _log(f"No processes matching pattern: {pattern}")
        return []
    return kill_tree(matches, **kw)
