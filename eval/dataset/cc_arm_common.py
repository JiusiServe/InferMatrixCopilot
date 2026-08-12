#!/usr/bin/env python3
"""Shared harness for the two Opus 5 arms: `run_baseline_pinned.py` (no MCP) and
`run_direct_arm.py` (our MCP + the imreview skill).

The two arms exist to be compared to each other, so everything except the variable
under test is defined here once — same model, same trees, same frozen PR snapshot,
same tool surface, same isolation, same audit. If a control lives in only one of the
two runners it is not a control.

Three properties this module is responsible for:

**Configuration isolation, asserted rather than assumed.** `--strict-mcp-config`
isolates MCP and nothing else; skills, user/project settings, hooks and agents each
need their own switch. All four are set here, and — the part that makes it checkable —
the CLI's `system/init` event reports `skills`, `mcp_servers`, `slash_commands` and the
resolved model, so `assert_init` compares the run's real configuration against what the
arm declared before any item is paid for. This matters concretely: `imreview` is
installed at user level, so an inherited-skill baseline could have invoked our own
skill and put our contribution on both sides of the contrast the baseline exists to
provide.

**Events, not just the final result.** `--output-format json` exposes only the last
message, which cannot answer "was the MCP `review` tool actually called", "what paths
were read" or "what did the agent execute". Every run is captured as a stream and
retained per item as `<stem>.events.jsonl`; every audit downstream reads that file.

**A bounded validation surface, given to both arms equally.** `imreview` requires an
import preflight, targeted pytest and static checks (SKILL.md:27-32), so an arm holding
read-only tools plus MCP could not follow its own protocol. Withholding execution from
Direct while the copilot Strict arm has `run_shell` would invent an asymmetry, so both
arms get the same short allowlist. `python3 -c` is genuinely arbitrary execution, which
tool-level path denial cannot contain — so containment here is *detection*: every
command string is recorded and `audit_events` fails the item if one reaches the ground
truth, another arm's outputs, or the network.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Import by location, not by ambient sys.path: this module is also loaded by tests via
# importlib, where the dataset directory is not necessarily importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import trace_pack  # noqa: E402

REAL_HOME = Path.home()
HERE = Path(__file__).parent
SNAPSHOTS = HERE / "snapshots"
REPO = "vllm-project/vllm-omni"

# Exact id, never the `opus` alias: an alias is a moving target and this arm exists to
# be reproducible. The resolved id from the init event is what actually gets recorded.
MODEL = os.environ.get("ARM_MODEL", "claude-opus-5")
# 60 was inherited from the Opus 4.8 baseline and measured too low: the first smoke
# item spent all 61 turns investigating, hit the cap mid-flight and returned an EMPTY
# final message — $3.50 for no artifact. The cap is raised, and the prompts now spend
# the budget deliberately, because a review that never gets written scores as silence.
MAX_TURNS = int(os.environ.get("ARM_MAX_TURNS", "120"))
PER_ITEM_TIMEOUT = 3600

# Read-only investigation, shared by both arms. `gh pr view` and `gh pr checks` are
# absent on purpose: prefix matching cannot stop `gh pr view --comments`, and a live
# `gh pr checks` would give each arm a different CI snapshot than the frozen one.
BASE_TOOLS = [
    "Read", "Grep", "Glob", "LS", "TodoWrite", "Task",
    "Bash(gh pr diff:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
]
# The validation surface imreview's protocol requires — given to BOTH arms. Both
# `python` and `python3` spellings are listed because the smoke run reached for
# `python -c` and was denied, which would have silently deprived the arm of the
# preflight the protocol asks for while looking like the arm chose not to run one.
VALIDATION_TOOLS = [
    "Bash(python -c:*)", "Bash(python3 -c:*)",
    "Bash(python -m pytest:*)", "Bash(python3 -m pytest:*)",
    "Bash(python -m ruff:*)", "Bash(python3 -m ruff:*)",
    "Bash(python -m compileall:*)", "Bash(python3 -m compileall:*)",
    "Bash(ruff:*)", "Bash(rg:*)",
]

# Anything an arm must never reach. `gt/` is the answer key; the arm/baseline dirs are
# other candidates' outputs; the rest are the discussion endpoints the snapshot exists
# to replace.
FORBIDDEN_SUBSTRINGS = (
    "eval/dataset/gt", "dataset/gt/", "/gt/pr",
    "eval/dataset/arms", "eval/dataset/baselines",
    "gh pr view", "gh pr checks", "gh api", "pulls/", "/comments",
    "gh issue view", "gh search",
)

# Installed dependencies, readable by BOTH arms. vllm-omni extends vllm, so reviewing
# an integration means reading the upstream API the change binds to — three baseline
# items and one Direct item did exactly that, and confining reads to the worktree
# flagged all four. Library source carries no PR ground truth, and granting it to only
# one arm would be the asymmetry worth worrying about. The forbidden list above is
# checked first and independently, so this widens dependency reading and nothing else.
def _dep_roots() -> tuple[Path, ...]:
    import site
    roots = set(site.getsitepackages())
    try:
        roots.add(site.getusersitepackages())
    except Exception:  # noqa: BLE001 — absent in some layouts
        pass
    return tuple(Path(p) for p in sorted(roots) if Path(p).is_dir())


DEP_READ_ROOTS = _dep_roots()


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def provision_home(skills: tuple[str, ...] = ()) -> Path:
    """A private HOME carrying credentials and the named skills — nothing else.

    Isolating is what removes inherited settings, hooks, agents and the user's whole
    skill library; but isolating also removes authentication (measured: a bare HOME
    fails with `Not logged in`), so the credential file is copied back in explicitly.
    Skills are staged rather than inherited so that `skills: ["imreview"]` in the init
    event means the one we put there, not whatever happens to be installed.
    """
    home = Path(tempfile.mkdtemp(prefix="cc-arm-home-"))
    home.chmod(0o700)
    (home / ".claude").mkdir()
    shutil.copy2(REAL_HOME / ".claude" / ".credentials.json", home / ".claude")
    if skills:
        (home / ".claude" / "skills").mkdir()
        for name in skills:
            src = REAL_HOME / ".claude" / "skills" / name
            if not src.is_dir():
                shutil.rmtree(home, ignore_errors=True)
                raise RuntimeError(f"skill {name!r} not found at {src}")
            shutil.copytree(src, home / ".claude" / "skills" / name)
    (home / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
    return home


def snapshot(pr: int) -> tuple[str, str]:
    """(text, sha256) of the frozen PR context — the same bytes for both arms."""
    d = json.loads((SNAPSHOTS / f"pr{pr}.json").read_text(encoding="utf-8"))
    return d["text"], d["sha256"]


def run_cc(prompt: str, allowed: list[str], home: Path, cwd: Path,
           mcp_config: Path, disable_skills: bool,
           timeout: int = PER_ITEM_TIMEOUT) -> dict:
    """One headless Claude Code run, captured as events.

    `env -i`-style: the environment is rebuilt from scratch rather than filtered, so no
    ANTHROPIC*/CLAUDE_CODE* routing can survive by having a name we did not predict.
    """
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(home), "TERM": "dumb",
           "LANG": os.environ.get("LANG", "C.UTF-8")}
    cmd = ["claude", "-p", prompt,
           "--output-format", "stream-json", "--verbose",
           "--max-turns", str(MAX_TURNS),
           "--model", MODEL,
           "--setting-sources", "",
           "--strict-mcp-config", "--mcp-config", str(mcp_config),
           "--allowedTools", ",".join(allowed)]
    if disable_skills:
        cmd.append("--disable-slash-commands")
    p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    events = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"events": events, "rc": p.returncode, "stderr": p.stderr[-2000:]}


def init_event(events: list[dict]) -> dict:
    for e in events:
        if e.get("type") == "system" and e.get("subtype") == "init":
            return e
    return {}


def result_event(events: list[dict]) -> dict:
    for e in reversed(events):
        if e.get("type") == "result":
            return e
    return {}


def tool_uses(events: list[dict]) -> list[dict]:
    """Every tool call the model actually made, as {name, input}."""
    out = []
    for e in events:
        msg = e.get("message") or {}
        for block in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                out.append({"name": block.get("name", "?"),
                            "input": block.get("input") or {}})
    return out


def assert_init(events: list[dict], *, expect_skills: list[str],
                expect_mcp: list[str], arm: str) -> str:
    """Fail before spending if the run is not configured the way the arm claims.

    Returns the resolved model id. The alternative — discovering after 20 Opus runs
    that a skill or MCP server leaked in — costs the whole arm, not one item.
    """
    init = init_event(events)
    if not init:
        raise RuntimeError(f"{arm}: no init event — cannot verify configuration")
    got_skills = sorted(init.get("skills") or [])
    got_mcp = sorted(s.get("name", s) if isinstance(s, dict) else s
                     for s in (init.get("mcp_servers") or []))
    problems = []
    if got_skills != sorted(expect_skills):
        problems.append(f"skills {got_skills} != {sorted(expect_skills)}")
    if got_mcp != sorted(expect_mcp):
        problems.append(f"mcp_servers {got_mcp} != {sorted(expect_mcp)}")
    model = str(init.get("model") or "")
    if not model or model == "opus":
        problems.append(f"model did not resolve to an exact id (got {model!r})")
    if problems:
        raise RuntimeError(f"{arm}: configuration assertion failed — "
                           + "; ".join(problems))
    return model


def denied_ids(events: list[dict]) -> set[str]:
    """tool_use_ids the permission layer refused. These are containment WORKING."""
    return {str(d.get("tool_use_id")) for d
            in (result_event(events).get("permission_denials") or [])}


def audit_events(events: list[dict], worktree: Path,
                 extra_read_roots: tuple[Path, ...] = ()) -> tuple[list[str], list[str]]:
    """(violations, blocked_attempts) from what the run actually did.

    Output text that happens to lack reviewer usernames proves nothing about what the
    model read, so this reads the recorded tool calls. Bash is checked as a raw string
    because `python -c` reaches places a path-based check would never look at.

    The distinction the first smoke run forced: an *attempt* that the permission layer
    refused is the sandbox doing its job, not a leak. Counting denials as violations
    failed a clean item and would have failed all 40. Only a forbidden target that
    actually returned data is a violation; refused attempts are reported separately so
    they stay visible without being fatal.

    `extra_read_roots` exists for the Direct arm, whose whole purpose is to follow the
    knowledge routes the copilot returns — those live in the copilot checkout, outside
    the worktree. Reading them is the behaviour under test, not a leak. The forbidden
    list is checked first and independently, so `gt/`, `arms/` and `baselines/` stay
    unreachable even though they sit inside the same checkout.
    """
    violations: list[str] = []
    blocked: list[str] = []
    refused = denied_ids(events)
    wt = str(worktree.resolve())
    allowed_roots = ([wt] + [str(p.resolve()) for p in extra_read_roots]
                     + [str(p) for p in DEP_READ_ROOTS])
    for e in events:
        msg = e.get("message") or {}
        for b in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name, inp = str(b.get("name")), b.get("input") or {}
            blob = json.dumps(inp, ensure_ascii=False)
            hit = next((bad for bad in FORBIDDEN_SUBSTRINGS if bad in blob), None)
            fp = str(inp.get("file_path") or "")
            outside = (name in ("Read", "Edit", "Write", "NotebookEdit")
                       and fp.startswith("/")
                       and not any(fp.startswith(r) for r in allowed_roots))
            if not hit and not outside:
                continue
            why = (f"forbidden target {hit!r}" if hit
                   else f"path outside the worktree: {fp}")
            entry = f"{name}: {why} in {blob[:160]}"
            (blocked if str(b.get("id")) in refused else violations).append(entry)
    return violations, blocked


def cost_from(events: list[dict]) -> dict:
    r = result_event(events)
    usage = r.get("usage") or {}
    return {
        "calls": r.get("num_turns", 0),
        "input_tokens": (usage.get("input_tokens", 0)
                         + usage.get("cache_read_input_tokens", 0)
                         + usage.get("cache_creation_input_tokens", 0)),
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": r.get("total_cost_usd"),
        "is_error": bool(r.get("is_error")),
        "terminal_reason": r.get("terminal_reason"),
    }


def final_text(events: list[dict]) -> str:
    return str(result_event(events).get("result") or "").strip()


def validation_commands(events: list[dict]) -> list[str]:
    """What each arm actually executed — so the report can state how often the
    validation capability was used rather than assuming it was."""
    return [str(c["input"].get("command", ""))[:300]
            for c in tool_uses(events) if c["name"] == "Bash"]


def ran_validation(events: list[dict]) -> bool:
    """Did the arm actually exercise the execution surface both arms were given?

    Reading files is investigation; running the preflight/tests/static checks is the
    thing `imreview` requires and the baseline merely may do. Whether each side used it
    is a finding, so it is measured rather than assumed either way.
    """
    refused = denied_ids(events)
    marks = ("python -c", "python3 -c", "pytest", "ruff", "compileall")
    for e in events:
        msg = e.get("message") or {}
        for b in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if (isinstance(b, dict) and b.get("type") == "tool_use"
                    and b.get("name") == "Bash"
                    and str(b.get("id")) not in refused
                    and any(m in str((b.get("input") or {}).get("command", ""))
                            for m in marks)):
                return True
    return False


def claude_md_fingerprint(worktree: Path) -> dict:
    """The one ambient input `--setting-sources` does not govern.

    CLAUDE.md discovery walks up from cwd, and the pinned worktrees live under
    /data/zhoutaichang, so a policy file up there is in scope for both arms. It is not
    excludable, so it is recorded: both arms run from the same parents, so this must be
    identical between them, and the comparison checks that it is.
    """
    import hashlib
    found = {}
    p = worktree.resolve()
    for d in [p, *p.parents]:
        f = d / "CLAUDE.md"
        if f.is_file():
            found[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
        if str(d) == "/":
            break
    return found


def write_run(arm_dir: Path, stem: str, body: str, cost: dict,
              events: list[dict]) -> None:
    """Emit every artifact for one item, with `.cost.json` written LAST.

    `.cost.json` is what `already_done` keys on, so writing it last makes the whole
    group effectively transactional against resume: a crash midway leaves the item
    looking unfinished and it re-runs cleanly, rather than being permanently accepted
    with a missing trace.

    The committed `.trace.json.gz` is produced here rather than by a later step because
    a trace emitted by a separate pass is a trace that can be skipped — which is exactly
    how the wave-1 Strict arm ended up unexplainable. `.events.jsonl` stays on disk as
    the unscrubbed original and is gitignored.
    """
    _write_atomic(arm_dir / f"{stem}.md", body)
    _write_atomic(arm_dir / f"{stem}.events.jsonl",
                  "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n")
    trace_pack.pack_claude_code(arm_dir, stem, events, {
        "arm": arm_dir.name, "stem": stem,
        "head": cost.get("head"), "base": cost.get("base"),
        "resolved_model": cost.get("resolved_model"),
        "snapshot_sha256": cost.get("snapshot_sha256"),
        "recorded_at": cost.get("recorded_at"), "backfilled": False,
    })
    _write_atomic(arm_dir / f"{stem}.cost.json", json.dumps(cost, indent=2) + "\n")


def already_done(arm_dir: Path, stem: str, expected_head: str) -> bool:
    """Resume only when every artifact agrees. A non-empty .md alone would permanently
    accept a timed-out or audit-failed item as finished."""
    md, cj = arm_dir / f"{stem}.md", arm_dir / f"{stem}.cost.json"
    if not (md.is_file() and md.stat().st_size > 50 and cj.is_file()):
        return False
    try:
        c = json.loads(cj.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (c.get("head") == expected_head and c.get("audit_ok") is True
            and not c.get("is_error"))


def stamp(cost: dict, *, item: dict, head: str, base: str, model: str,
          snap_sha: str, worktree: Path, events: list[dict]) -> dict:
    cost.update({
        "split": item["split"], "head": head, "base": base,
        "resolved_model": model, "snapshot_sha256": snap_sha,
        "validation_commands": validation_commands(events),
        "ran_validation": ran_validation(events),
        "claude_md_seen": claude_md_fingerprint(worktree),
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    return cost
