#!/usr/bin/env python3
"""Run the OCR arm (alibaba/open-code-review) over the dataset's PR items.

Produces the same artifact shape as `run_copilot_arm.py` so the existing blind judge
can score it in the ARM_A slot against the same `baselines/claudecode_opus48`:

  eval/dataset/arms/<ARM_OUT>/pr<N>.md         (the judged artifact)
  eval/dataset/arms/<ARM_OUT>/pr<N>.cost.json  (cost + coverage + run identity)
  eval/dataset/arms/<ARM_OUT>/manifest.json

`ocr review`, not `ocr delegate`: delegate emits a review SPEC for a host agent to
execute, which is scaffolding rather than a review, and judging it against a written
review would compare different kinds of object.

Fairness is bought three ways: the same model endpoint the copilot uses (OCR's own
benchmark methodology is "same underlying model"), the copilot's own PR-time worktrees
so both systems see a byte-identical tree, and a pinned evaluation range validated
against the dataset's declared file counts.

Usage: run_ocr_arm.py [splits] [only_stem]
  splits    comma list, default "train,val,test" — the 20-PR comparison set that
            copilot_v4_pr20_r{1,2,3} and the baseline already cover
  only_stem e.g. pr4977 to run a single item

Env:
  ARM_OUT   arm directory name (default ocr_v1810_r1)
  OCR_BIN   path to the ocr binary (default: `ocr` on PATH)
  OCR_JOBS  concurrent reviews (default 3)

Concurrency is deliberately modest. `ocr review` is ALREADY internally parallel — it
dispatches files to sub-agents 8-wide (`configured_concurrency: 8` in its manifest), so
N concurrent reviews put up to 8N requests on the same endpoint. Three matches the
judge's own pool size and keeps the ceiling near what a single copilot arm run already
produces. Worktree preparation stays serial regardless: `git worktree add` takes a
repository-level lock, so concurrent creation would fail on contention rather than go
faster.

Nothing touches the live repo: worktrees are read-only to this script, and OCR has no
posting path.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
EXPECTED_HEADS = HERE / "goal-eval" / "expected_pr_heads.json"
ARM = HERE / "arms" / os.environ.get("ARM_OUT", "ocr_v1810_r1")
REPO = Path("/data/zhoutaichang/copilot/vllm-omni")
WORKTREES = Path.home() / ".infermatrix-copilot" / "worktrees"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# judge_val.py caps each candidate at this many chars; anything longer is silently
# truncated before scoring, which would judge a partial review
JUDGE_CAP = 24_000
PER_PR_TIMEOUT = 1800


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None,
         timeout: int = 120) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def _git(repo: Path, *args: str) -> str:
    rc, out, err = _run(["git", *args], cwd=repo)
    if rc != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {err.strip()[:300]}")
    return out.strip()


def _write_atomic(path: Path, text: str) -> None:
    """tmp + replace: a killed run must never leave a half-written artifact that the
    resume check would then accept as finished."""
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _ocr_credential() -> tuple[str, str, str]:
    """(api_key, base_url, model) from the copilot's own .env — same endpoint, so the
    comparison is same-model as OCR's own benchmark methodology requires."""
    vals: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"')
    key = vals.get("ANTHROPIC_API_KEY", "")
    url = vals.get("ANTHROPIC_BASE_URL", "")
    model = vals.get("AGENT_MODEL", "")
    if not (key and url and model):
        sys.exit(f"missing ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL / AGENT_MODEL in {ENV_FILE}")
    return key, url, model


def _provision_home(ocr_bin: str) -> tuple[Path, dict, str, str]:
    """A private HOME with OCR configured in it.

    Isolation is not optional: OCR's config lives in ~/.opencodereview, concurrent runs
    would race on it, and `ocr review` leaks a zero-byte session file per invocation
    (measured) which over 60 runs would accumulate in the user's real home. But
    isolating also HIDES the config, so it has to be provisioned here rather than
    inherited.
    """
    home = Path(tempfile.mkdtemp(prefix="ocr-arm-home-"))
    home.chmod(0o700)
    env = {**os.environ, "HOME": str(home)}
    key, url, model = _ocr_credential()
    for args in (["config", "set", "provider", "ds-anthropic"],
                 ["config", "set", "custom_providers.ds-anthropic.url", url],
                 ["config", "set", "custom_providers.ds-anthropic.protocol", "anthropic"],
                 ["config", "set", "custom_providers.ds-anthropic.api_key", key],
                 ["config", "set", "model", model]):
        rc, _out, err = _run([ocr_bin, *args], env=env)
        if rc != 0:
            shutil.rmtree(home, ignore_errors=True)
            sys.exit(f"ocr config failed: {err.strip()[:200]}")
    return home, env, url, model


def _prepare_worktree(pr: str, expected_head: str, declared_files: int) -> tuple[Path, str]:
    """Return (worktree, base) after three gates that all fail loudly.

    Deriving a base from live origin/main unconditionally is unsafe: for a merged PR
    whose head is an ancestor of main, merge-base returns the head itself, the range is
    empty, and OCR would 'review' nothing while the run still looked successful. The
    file-count check is the gate that catches that regardless of cause.
    """
    wt = WORKTREES / f"vllm-omni-pr{pr}"
    if not wt.is_dir():
        _run(["git", "fetch", "origin", f"pull/{pr}/head"], cwd=REPO, timeout=600)
        rc, _o, err = _run(["git", "worktree", "add", "--detach", str(wt), expected_head],
                           cwd=REPO, timeout=600)
        if rc != 0:
            raise RuntimeError(f"pr{pr}: worktree create failed: {err.strip()[:200]}")

    head = _git(wt, "rev-parse", "HEAD")
    if head != expected_head:
        raise RuntimeError(f"pr{pr}: head {head[:12]} != pinned {expected_head[:12]}")
    if _git(wt, "status", "--porcelain"):
        raise RuntimeError(f"pr{pr}: worktree is dirty — refusing to evaluate it")

    base = _git(wt, "merge-base", "HEAD", "origin/main")
    changed = [f for f in _git(wt, "diff", "--name-only", base, "HEAD").splitlines() if f]
    if len(changed) != declared_files:
        raise RuntimeError(
            f"pr{pr}: range {base[:12]}..{head[:12]} yields {len(changed)} changed files, "
            f"dataset declares {declared_files} — refusing to evaluate a wrong range")
    return wt, base


def _render(pr: str, title: str, data: dict, base: str, head: str) -> str:
    """Render OCR's JSON review as the judged markdown artifact.

    Faithful to OCR's own output rather than imitating either the copilot's run report
    or the Opus baseline's prose — format heterogeneity is already the norm in this
    harness, and mimicry would measure the renderer instead of the reviewer.
    """
    s = data.get("summary") or {}
    m = data.get("manifest") or {}
    cov = m.get("coverage") or {}
    state = m.get("terminal_state", "?")
    out = [
        f"# OCR review: PR #{pr} — {title}",
        "",
        f"- engine: open-code-review {m.get('execution', {}).get('ocr_version', '?')} "
        f"(`ocr review`), model `{(data.get('llm') or {}).get('model', '?')}`",
        f"- range: `{base[:12]}..{head[:12]}`",
        f"- terminal state: **{state}** — "
        f"{len(cov.get('completed', []))} of {len(cov.get('selected', []))} selected "
        f"item(s) reviewed, {len(cov.get('failed', []))} failed",
        "",
    ]
    if state == "skipped":
        out += [
            "## No files reviewed",
            "",
            "OCR selected no reviewable files for this PR: every changed file was "
            "filtered out before dispatch (its supported-extension list excludes "
            "Markdown and other documentation formats). This is a capability boundary "
            "of the tool, not a judgement that the change is correct.",
            "",
        ]
    comments = data.get("comments") or []
    if comments:
        out.append(f"## Findings ({len(comments)})")
        out.append("")
        for c in comments:
            loc = f"{c.get('path', '?')}:{c.get('start_line', '?')}"
            if c.get("end_line") and c.get("end_line") != c.get("start_line"):
                loc += f"-{c['end_line']}"
            out.append(f"### `{loc}` — {c.get('severity', '?')} / {c.get('category', '?')}")
            out.append("")
            out.append(str(c.get("content", "")).strip())
            if c.get("existing_code"):
                out += ["", "Anchored to:", "", "```",
                        str(c["existing_code"]).rstrip(), "```"]
            if c.get("suggestion_code"):
                out += ["", "Suggested:", "", "```",
                        str(c["suggestion_code"]).rstrip(), "```"]
            out.append("")
    elif state != "skipped":
        out += ["## Findings (0)", "",
                "OCR reviewed the selected files and reported no issues.", ""]
    for item in cov.get("failed", []):
        out.append(f"> Unreviewed: `{item.get('path')}` — "
                   f"{item.get('classification')}: {item.get('reason')}")
    return "\n".join(out).rstrip() + "\n"


def _already_done(md: Path, cj: Path, expected_head: str) -> bool:
    """Resume only when everything agrees. A non-empty .md alone would permanently
    accept a timeout or partial artifact."""
    if not (md.is_file() and md.stat().st_size and cj.is_file()):
        return False
    try:
        c = json.loads(cj.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (c.get("terminal_state") in {"complete", "partial", "skipped"}
            and c.get("head") == expected_head)


def main() -> int:
    splits = set((sys.argv[1] if len(sys.argv) > 1 else "train,val,test").split(","))
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    ocr_bin = os.environ.get("OCR_BIN") or shutil.which("ocr") or ""
    if not ocr_bin:
        sys.exit("ocr binary not found — set OCR_BIN, or "
                 "`npm install -g @alibaba-group/open-code-review`")

    ds = yaml.safe_load(DATASET.read_text(encoding="utf-8"))
    heads = json.loads(EXPECTED_HEADS.read_text(encoding="utf-8"))
    items = [i for i in ds["pr_review"] if i.get("split") in splits]
    if only:
        items = [i for i in items if f"pr{i['pr']}" == only]
    ARM.mkdir(parents=True, exist_ok=True)

    home, env, url, model = _provision_home(ocr_bin)
    oversize, failures = [], []
    done = 0
    lock = threading.Lock()

    # PHASE 1 — serial. Every gate, and every git write, happens before any review
    # starts: `git worktree add` takes a repository-level lock, so doing this inside
    # the pool would contend rather than parallelise.
    pending: list[tuple[dict, Path, str, str]] = []
    for item in items:
        pr = str(item["pr"])
        stem = f"pr{pr}"
        md, cj = ARM / f"{stem}.md", ARM / f"{stem}.cost.json"
        expected_head = heads.get(pr)
        if not expected_head:
            failures.append(f"{stem}: no pinned head in expected_pr_heads.json")
            continue
        if _already_done(md, cj, expected_head):
            print(f"  {stem}: already done, skipping")
            done += 1
            continue
        try:
            wt, base = _prepare_worktree(pr, expected_head, int(item["size"]["files"]))
        except Exception as exc:
            failures.append(f"{stem}: {exc}")
            print(f"  {stem}: GATE FAILED — {exc}")
            continue
        pending.append((item, wt, base, expected_head))

    # PHASE 2 — parallel reviews over the prepared, gated set.
    def _review(job: tuple[dict, Path, str, str]) -> None:
        nonlocal done
        item, wt, base, expected_head = job
        pr = str(item["pr"])
        stem = f"pr{pr}"
        md, cj = ARM / f"{stem}.md", ARM / f"{stem}.cost.json"
        t0 = time.time()
        rc, out, err = _run([ocr_bin, "review", "--from", base, "--to", "HEAD",
                             "--format", "json", "--audience", "agent"],
                            cwd=wt, env=env, timeout=PER_PR_TIMEOUT)
        wall = round(time.time() - t0, 1)
        try:
            data = json.loads(out)
        except Exception:
            with lock:
                failures.append(
                    f"{stem}: unparseable OCR output (rc={rc}) {err[:200]}")
                print(f"  {stem}: UNPARSEABLE (rc={rc})")
            return

        s = data.get("summary") or {}
        m = data.get("manifest") or {}
        cov = m.get("coverage") or {}
        state = m.get("terminal_state", "?")
        inp, outp = s.get("input_tokens") or 0, s.get("output_tokens") or 0
        cached = s.get("cache_read_tokens") or 0
        body = _render(pr, str(item.get("title", "")), data, base, expected_head)
        if len(body) > JUDGE_CAP:
            with lock:
                oversize.append((stem, len(body)))

        cost = {
            # fields aggregate_costs.py reads
            "wall_s": wall, "split": item["split"], "rc": rc,
            "input_tokens": inp, "output_tokens": outp,
            "attempt_usd_total": round(
                ((inp - cached) * 0.28 + cached * 0.028 + outp * 0.42) / 1e6, 6),
            # OCR-specific detail
            "engine": "ocr", "terminal_state": state,
            "head": expected_head, "base": base,
            "cached_input_tokens": cached, "fresh_input_tokens": inp - cached,
            "raw_total_tokens": inp + outp,   # cache-inclusive; never quote bare
            "coverage": {k: len(cov.get(k, [])) for k in
                         ("selected", "completed", "reused", "failed", "waived")},
            "findings": len(data.get("comments") or []),
            "tool_calls": (data.get("tool_calls") or {}).get("total", 0),
            # OCR reviewed nothing because every file was filtered out: a
            # capability boundary, NOT a completed review of zero findings
            "structural_skip": state == "skipped",
            "artifact_chars": len(body),
            "identity": {
                "repository": (m.get("repository") or {}).get("identity_sha256"),
                "source_artifact": (m.get("input") or {}).get("source_artifact_sha256"),
                "rule_config": (m.get("execution") or {}).get("rule_config_sha256"),
                "runtime_config": (m.get("execution") or {}).get("runtime_config_sha256"),
            },
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        _write_atomic(md, body)
        _write_atomic(cj, json.dumps(cost, indent=2) + "\n")
        with lock:
            done += 1
            print(f"  {stem}: {state} wall={wall}s findings={cost['findings']} "
                  f"usd={cost['attempt_usd_total']:.4f} chars={len(body)}")

    jobs = max(1, int(os.environ.get("OCR_JOBS", "3")))
    try:
        if pending:
            print(f"  reviewing {len(pending)} item(s), {jobs} at a time")
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futures = [ex.submit(_review, j) for j in pending]
            for f in as_completed(futures):
                exc = f.exception()
                if exc:
                    with lock:
                        failures.append(f"worker crashed: {exc}")

        _write_atomic(ARM / "manifest.json", json.dumps({
            "arm": ARM.name,
            "engine": f"open-code-review ({ocr_bin}) — `ocr review`, agent audience",
            "llm": f"{model} @ {url} (same endpoint as the copilot arms)",
            "dataset": "vllm_omni_dataset.yaml",
            "splits": sorted(splits),
            "n_items": done,
            "concurrency": jobs,
            "notes": "PR-time worktrees shared with the copilot arms; head pinned to "
                     "expected_pr_heads.json; range validated against declared file "
                     "counts. structural_skip marks PRs OCR filtered out entirely.",
        }, indent=2) + "\n")
    finally:
        shutil.rmtree(home, ignore_errors=True)

    print(f"\n{done}/{len(items)} items written to {ARM}")
    if oversize:
        print("OVER JUDGE CAP (would be silently truncated before scoring):")
        for stem, n in oversize:
            print(f"  {stem}: {n} chars > {JUDGE_CAP}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
