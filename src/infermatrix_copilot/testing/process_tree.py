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


def _start_time(pid: int) -> int | None:
    """Kernel start time (jiffies) from /proc/<pid>/stat — a (pid, starttime)
    pair identifies a process across PID reuse. None when unreadable (process
    gone, or no procfs)."""
    try:
        stat = open(f"/proc/{pid}/stat", "rb").read().decode(errors="replace")
        # comm (field 2) may contain spaces/parens; split after the LAST ")".
        # Fields after it start at field 3; starttime is field 22 → index 19.
        return int(stat.rsplit(")", 1)[1].split()[19])
    except (OSError, ValueError, IndexError):
        return None


def kill_tree(pids: list[int], *, term_grace: float = 2.0,
              kill_grace: float = 1.0,
              kill: Callable[[int, int], None] | None = None,
              sleep: Callable[[float], None] = time.sleep) -> list[int]:
    """SIGTERM every pid and its descendants, wait `term_grace`, SIGKILL the
    survivors, wait `kill_grace`. Returns pids still alive (ideally empty)."""
    kill = kill or (lambda p, s: os.kill(p, s))
    targets = sorted({d for p in pids for d in collect_descendants(p)})
    if not targets:
        return []
    # capture identity BEFORE signalling: after the grace sleep a target's pid
    # may have been reaped and reused, and escalating SIGKILL by bare pid would
    # then hit an unrelated process
    identity = {p: _start_time(p) for p in targets}

    def same_process(pid: int) -> bool:
        born = _start_time(pid)
        if born is None or identity[pid] is None:
            return _alive(pid)  # identity unverifiable — legacy pid-only check
        return born == identity[pid]

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
