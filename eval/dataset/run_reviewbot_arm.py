#!/usr/bin/env python3
"""Reviewbot arm: generate omni-reviewbot Direct reviews over dataset PRs.

The bot is a loop+model combination (harness arm, like the cursor arm):
its results live in results/reviewbot/ and are never merged into the
generator ablation tables. Scope is the dataset's train+val pr_review
items only — test stays frozen.

Measurement contract enforced per invocation, all fail-closed:
  - POST_MODE=shadow hard-set and `status: shadow` asserted in CLI output
    (a review that reached a publish path aborts the campaign);
  - REVIEW_CONTEXT_MODE=no_discussion hard-set and the CLI's
    `review_context: no_discussion (0 threads)` line asserted — on these
    PRs the historical review threads ARE the ground truth;
  - reviewed head (from the artifact name pr-<n>-<head>.md) must equal
    goal-eval/expected_pr_heads.json[<n>];
  - the CLI's `changed_files: N` must match the frozen GT diff's file
    count (gt/pr<N>.diff);
  - the sanitized artifact must fit judge_val.py's 24k candidate cap.

Replication has ONE owner: this runner. ARM_TAG=<tag> creates
arms/<tag>_r1..rN (GEN_REPLICATES, default 3); replicates of one item run
sequentially (the bot's artifact name repeats per head, and each artifact
is moved out immediately), items run with small parallelism (ARM_JOBS).

Env: ARM_TAG (required) · GEN_REPLICATES=3 · ONLY_ITEMS=4893,4810 ·
ARM_JOBS=2 · REVIEWBOT_DIR (default: sibling omni-reviewbot checkout) ·
REVIEWBOT_PYTHON (default <dir>/.venv/bin/python, else python3) ·
REVIEWBOT_ENV_FILE (default <dir>/.env; loaded first, hard overrides win) ·
REVIEWBOT_TIMEOUT_S=1800 · REVIEWBOT_EVAL_ROOT (tests only)
Flags: --dry-run (print the plan, touch nothing) · --preflight (doctor only)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

HERE = Path(os.environ.get("REVIEWBOT_EVAL_ROOT") or Path(__file__).parent)
DATASET = HERE / "vllm_omni_dataset.yaml"
EXPECTED_HEADS = HERE / "goal-eval" / "expected_pr_heads.json"
GT = HERE / "gt"
ARMS = HERE / "arms"
STATE_DIR = HERE.parent / "raw" / "reviewbot_state"
JUDGE_CAP = 24_000  # judge_val.py silently truncates candidates here

_MARKER = re.compile(r"<!--.*?-->", re.DOTALL)
_CONTEXT_LINE = re.compile(r"^review_context: (\S+) \((\d+) threads\)$", re.M)
_CHANGED_LINE = re.compile(r"^changed_files: (\d+)$", re.M)
_STATUS_LINE = re.compile(r"^status: (\S+)$", re.M)


def sanitize(body: str) -> str:
    """Blind judging: explicit arm labels must not reach the judge."""
    body = _MARKER.sub("", body)
    body = body.replace("## Omni ReviewBot review", "## Review", 1)
    return body.strip() + "\n"


def gt_changed_files(pr: int) -> int:
    text = (GT / f"pr{pr}.diff").read_text(encoding="utf-8", errors="replace")
    return sum(
        1 for line in text.splitlines() if line.startswith("diff --git ")
    )


def dataset_items() -> list[int]:
    data = yaml.safe_load(DATASET.read_text())
    items = [
        int(entry["pr"])
        for entry in data["pr_review"]
        if entry.get("split") in {"train", "val"}
    ]
    only = os.environ.get("ONLY_ITEMS", "").strip()
    if only:
        keep = {int(x) for x in only.split(",") if x.strip()}
        items = [n for n in items if n in keep]
    return sorted(items)


# Child-env keys that change what the Direct review actually does; they are
# part of the arm's identity (secrets are deliberately NOT in this list and
# never reach a manifest).
_BEHAVIOR_KEYS = (
    "AGENT_PROVIDER", "REVIEW_MODEL", "CURSOR_MODEL", "CODEX_COMMAND",
    "CODEX_TIMEOUT_SECONDS", "CURSOR_TIMEOUT_SECONDS",
    "GITHUB_REPOSITORY", "INFERMATRIX_PATH",
)


def git_state(path: Path) -> tuple[str, bool]:
    """(sha, dirty) for a checkout; ("unknown", True) when not a repo."""
    try:
        sha = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout.strip())
        return sha, dirty
    except Exception:
        return "unknown", True


def build_config(child_env: dict[str, str], bot_dir: Path) -> dict:
    """The arm's identity: bot revision, InferMatrix revision (its knowledge
    tree feeds the Direct routes), and the behavior-affecting env. A dirty
    or unknown source state is refused — a resumed campaign must never mix
    outputs from different implementations behind one manifest."""
    bot_sha, bot_dirty = git_state(bot_dir)
    im_path = child_env.get("INFERMATRIX_PATH", "")
    im_sha, im_dirty = (
        git_state(Path(im_path)) if im_path else ("unset", True)
    )
    if (bot_dirty or bot_sha == "unknown" or im_dirty) and not os.environ.get(
        "REVIEWBOT_EVAL_ALLOW_DIRTY"
    ):
        raise SystemExit(
            f"source state is not clean/pinned (bot {bot_sha[:12]} "
            f"dirty={bot_dirty}, infermatrix {im_sha[:12]} "
            f"dirty={im_dirty}) — commit or stash first, or set "
            "REVIEWBOT_EVAL_ALLOW_DIRTY=1 for a throwaway run"
        )
    return {
        "bot_sha": bot_sha,
        "bot_dirty": bot_dirty,
        "infermatrix_sha": im_sha,
        "infermatrix_dirty": im_dirty,
        "review_context_mode": "no_discussion",
        "post_mode": "shadow",
        "env": {key: child_env.get(key, "") for key in _BEHAVIOR_KEYS},
    }


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


class Runner:
    def __init__(self) -> None:
        self.tag = os.environ.get("ARM_TAG", "").strip()
        if not self.tag:
            sys.exit("ARM_TAG is required (e.g. ARM_TAG=reviewbot_2026-09)")
        self.gen_reps = int(os.environ.get("GEN_REPLICATES", "3"))
        self.jobs = int(os.environ.get("ARM_JOBS", "2"))
        self.timeout = int(os.environ.get("REVIEWBOT_TIMEOUT_S", "1800"))
        self.bot_dir = Path(
            os.environ.get("REVIEWBOT_DIR")
            or HERE.parent.parent.parent / "omni-reviewbot"
        ).resolve()
        venv_python = self.bot_dir / ".venv" / "bin" / "python"
        self.python = os.environ.get("REVIEWBOT_PYTHON") or (
            str(venv_python) if venv_python.exists() else "python3"
        )
        env_file = Path(
            os.environ.get("REVIEWBOT_ENV_FILE") or self.bot_dir / ".env"
        )
        # The bot's .env first, hard overrides LAST — the measurement
        # contract must win over whatever the operator's file says.
        child = dict(os.environ)
        child.update(_parse_env_file(env_file))
        child.update(
            {
                "POST_MODE": "shadow",
                "REVIEW_CONTEXT_MODE": "no_discussion",
                "REVIEWBOT_STATE_DIR": str(STATE_DIR),
                "PYTHONPATH": str(self.bot_dir / "src"),
            }
        )
        self.child_env = child
        self.expected = {
            int(k): v for k, v in json.loads(EXPECTED_HEADS.read_text()).items()
        }
        self.items = dataset_items()
        self.failures: list[str] = []
        self._lock = threading.Lock()
        self.config: dict | None = None

    def ensure_config(self) -> dict:
        if self.config is None:
            self.config = build_config(self.child_env, self.bot_dir)
        return self.config

    # --- manifests ---

    def _arm_dir(self, rep: int) -> Path:
        return ARMS / f"{self.tag}_r{rep}"

    def _manifest_path(self, rep: int) -> Path:
        return self._arm_dir(rep) / "manifest.json"

    def _init_manifest(self, rep: int) -> None:
        path = self._manifest_path(rep)
        config = self.ensure_config()
        if path.exists():
            stored = json.loads(path.read_text())
            if stored.get("config") != config:
                sys.exit(
                    f"{path}: existing manifest was generated under a "
                    f"different configuration — refusing to mix.\n"
                    f"stored:  {stored.get('config')}\n"
                    f"current: {config}"
                )
            if stored.get("stems") != [f"pr{n}" for n in self.items]:
                sys.exit(
                    f"{path}: existing manifest targets different items — "
                    "refusing to mix (delete the arm dir to restart)."
                )
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "arm_tag": self.tag,
                    "replicate": rep,
                    "stems": [f"pr{n}" for n in self.items],
                    "config": config,
                    "judge_cap": JUDGE_CAP,
                    "reviewed_heads": {},
                    "started_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    ),
                },
                indent=2,
            )
        )

    def _record_head(self, rep: int, stem: str, head: str) -> None:
        with self._lock:
            path = self._manifest_path(rep)
            manifest = json.loads(path.read_text())
            manifest["reviewed_heads"][stem] = head
            path.write_text(json.dumps(manifest, indent=2))

    # --- invocation ---

    def preflight(self) -> None:
        config = self.ensure_config()
        if config["env"]["AGENT_PROVIDER"] == "cursor" and not os.environ.get(
            "REVIEWBOT_EVAL_ALLOW_CURSOR"
        ):
            sys.exit(
                "AGENT_PROVIDER=cursor: cursor-family models have read the "
                "imreview methodology skills from $HOME before (contamination "
                "ledger). Vault the skill copies first, then set "
                "REVIEWBOT_EVAL_ALLOW_CURSOR=1."
            )
        for n in self.items:
            if n not in self.expected:
                sys.exit(f"pr{n} missing from {EXPECTED_HEADS}")
            if not (GT / f"pr{n}.diff").is_file():
                sys.exit(f"gt/pr{n}.diff missing — cannot validate diff range")
        doctor = subprocess.run(
            [self.python, "-m", "omni_reviewbot", "doctor"],
            cwd=self.bot_dir, env=self.child_env,
            capture_output=True, text=True, timeout=300,
        )
        if doctor.returncode != 0:
            sys.exit(
                "omni-reviewbot doctor failed:\n"
                + (doctor.stdout or "") + (doctor.stderr or "")
            )

    def _invoke(self, pr: int, rep: int) -> None:
        stem = f"pr{pr}"
        out_md = self._arm_dir(rep) / f"{stem}.md"
        if out_md.exists() and out_md.stat().st_size > 0:
            return
        completed = subprocess.run(
            [self.python, "-m", "omni_reviewbot", "review", "--pr", str(pr)],
            cwd=self.bot_dir, env=self.child_env,
            capture_output=True, text=True, timeout=self.timeout,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        if completed.returncode != 0:
            raise RuntimeError(f"exit {completed.returncode}: {output[-800:]}")
        status = _STATUS_LINE.search(completed.stdout or "")
        if not status or status.group(1) != "shadow":
            raise RuntimeError(
                f"outcome was not `status: shadow` — refusing "
                f"(got {status.group(1) if status else 'no status line'})"
            )
        context = _CONTEXT_LINE.search(completed.stdout or "")
        if not context or context.group(1) != "no_discussion" or (
            context.group(2) != "0"
        ):
            raise RuntimeError(
                "no `review_context: no_discussion (0 threads)` evidence — "
                "the run may have seen the ground-truth threads"
            )
        changed = _CHANGED_LINE.search(completed.stdout or "")
        expected_files = gt_changed_files(pr)
        if not changed or int(changed.group(1)) != expected_files:
            raise RuntimeError(
                f"changed_files {changed.group(1) if changed else '?'} != "
                f"frozen GT diff's {expected_files} — diff range drifted"
            )
        artifacts = sorted(
            (STATE_DIR / "artifacts").glob(f"pr-{pr}-*.md"),
            key=lambda p: p.stat().st_mtime,
        )
        if not artifacts:
            raise RuntimeError("no artifact produced")
        artifact = artifacts[-1]
        head = artifact.name[len(f"pr-{pr}-"):-len(".md")]
        if head != self.expected[pr]:
            raise RuntimeError(
                f"reviewed head {head[:12]} != pinned {self.expected[pr][:12]}"
            )
        body = sanitize(artifact.read_text())
        if len(body) > JUDGE_CAP:
            raise RuntimeError(
                f"sanitized review is {len(body)} chars — over the judge's "
                f"{JUDGE_CAP} cap; it would be silently truncated"
            )
        out_md.write_text(body)
        # Move (not copy): the next replicate reuses the same artifact name.
        artifact.unlink()
        self._record_head(rep, stem, head)

    def _run_item(self, pr: int) -> str:
        for rep in range(1, self.gen_reps + 1):
            try:
                self._invoke(pr, rep)
            except Exception as exc:  # noqa: BLE001 — every failure is a verdict
                with self._lock:
                    self.failures.append(f"pr{pr} r{rep}: {exc}")
                return f"pr{pr}: INVALID at r{rep}"
        return f"pr{pr}: ok x{self.gen_reps}"

    def run(self, *, dry_run: bool) -> int:
        plan = [
            f"  pr{n} x{self.gen_reps} -> " + ", ".join(
                str(self._arm_dir(r) / f"pr{n}.md")
                for r in range(1, self.gen_reps + 1)
            )
            for n in self.items
        ]
        print(
            f"[arm] tag={self.tag} items={len(self.items)} "
            f"reps={self.gen_reps} bot={self.bot_dir} "
            f"provider={self.child_env.get('AGENT_PROVIDER', 'codex')}"
        )
        print("\n".join(plan))
        if dry_run:
            print("[arm] dry run — nothing invoked")
            return 0
        self.preflight()
        (STATE_DIR / "artifacts").mkdir(parents=True, exist_ok=True)
        for rep in range(1, self.gen_reps + 1):
            self._init_manifest(rep)
        with ThreadPoolExecutor(max_workers=self.jobs) as pool:
            futures = {pool.submit(self._run_item, n): n for n in self.items}
            for future in as_completed(futures):
                print(f"[arm] {future.result()}", flush=True)
        if self.failures:
            print(
                f"[arm] {len(self.failures)} INVALID item(s) — the campaign "
                "must not be judged:", flush=True,
            )
            for failure in self.failures:
                print(f"  {failure}")
            return 1
        print("[arm] complete")
        return 0


def main() -> int:
    runner = Runner()
    if "--preflight" in sys.argv:
        runner.preflight()
        print("[arm] preflight ok")
        return 0
    return runner.run(dry_run="--dry-run" in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
