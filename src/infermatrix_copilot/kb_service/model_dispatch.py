"""Host/shared-filesystem dispatch slots for portable initialization.

Every participating generator and judge uses the same lock directory. This
limits active calls across threads, processes, repositories and batch state
directories. Separate lock directories are independent deployments; this is
not a distributed coordinator. Kernel file locks release on process exit.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)
MAX_CONCURRENCY = 13


class DispatchConfigError(ValueError):
    pass


@dataclass(frozen=True)
class DispatchTicket:
    slot: int
    wait_seconds: float
    limit: int
    directory: Path


class SharedModelDispatch:
    def __init__(self, directory: str | Path | None = None, *, limit: int | None = None,
                 environ=None):
        env = os.environ if environ is None else environ
        raw = env.get("KB_INIT_GLOBAL_CONCURRENCY", "13") if limit is None else limit
        if isinstance(raw, bool) or not str(raw).isdigit() or not 1 <= int(raw) <= MAX_CONCURRENCY:
            raise DispatchConfigError("KB_INIT_GLOBAL_CONCURRENCY must be an integer from 1 to 13")
        self.limit = int(raw)
        cache = Path(env.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        self.directory = Path(directory or env.get("KB_INIT_DISPATCH_DIR") or
                              cache / "infermatrix-copilot" / "kb-init-dispatch").expanduser().resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        # One namespace has one declared cap. Conflicting caps cannot silently
        # produce distinct pools on a shared host; choose an explicit namespace
        # when configuring an independent deployment.
        with (self.directory / "configuration.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            path = self.directory / "configuration.json"
            expected = {"schema_version": 1, "limit": self.limit}
            if path.exists():
                try:
                    actual = json.loads(path.read_text())
                except (ValueError, OSError) as exc:
                    raise DispatchConfigError("shared model dispatch configuration is unreadable") from exc
                if actual != expected:
                    raise DispatchConfigError("shared model dispatch cap conflicts with this namespace")
            else:
                with path.open("x") as stream:
                    json.dump(expected, stream, sort_keys=True)

    @contextmanager
    def slot(self):
        started = time.monotonic()
        last_notice = started
        while True:
            for index in range(self.limit):
                stream = (self.directory / f"slot-{index:02d}.lock").open("a+b")
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    stream.close()
                    continue
                try:
                    yield DispatchTicket(index, time.monotonic() - started, self.limit, self.directory)
                finally:
                    fcntl.flock(stream, fcntl.LOCK_UN)
                    stream.close()
                return
            now = time.monotonic()
            if now - last_notice >= 30:
                logger.info("Waiting for shared portable model dispatch slot (cap %s, %.1fs)",
                            self.limit, now - started)
                last_notice = now
            time.sleep(0.1)
