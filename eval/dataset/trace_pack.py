#!/usr/bin/env python3
"""Durable, lossless trace packing for every review arm — baseline, Direct and Strict.

Why this exists. The wave-1 Strict arm (`copilot_v4_pr20_r1`) can never be explained,
because its run directories lived under `arms/*/runs/` — gitignored — on a machine that
no longer exists. Only `.md` and `.cost.json` survived, so "why does Strict lose recall"
is permanently unanswerable for that arm. The baseline and Direct arms were one
`git clean` from the same fate: their `<stem>.events.jsonl` files are untracked, not
committed, and exist on exactly one disk.

The fix is not more instrumentation — the runners already emit everything. It is
retention: one committed artifact per item that is complete enough to answer questions
nobody has thought of yet.

**Lossless by construction, not by schema design.** A hand-written "distilled" schema
can only preserve the fields its author anticipated; the Direct analysis that motivated
this needed `quick_map` character counts and `validate_direct_review`'s `missing[]`
array, neither of which any reasonable distillation would have kept. So this module does
not interpret the traces at all. It applies a generic content-addressed compaction: every
object or string at or above `INTERN_THRESHOLD` bytes is hoisted into `blobs` and
replaced by a `{"$blob": sha}` reference, bottom-up. `expand()` inverts it exactly, and
`selftest` proves round-trip equality on real fixtures.

**The compaction is free because the bulk is repetition, not information.** A Strict
`events.jsonl` is 99% the `payload` field — the entire message history re-serialized on
every LLM call. One measured run: 1,986K of file holding 23 distinct messages. Interning
bottom-up means each message hashes once no matter how many calls quote it, which is why
lossless costs ~18% of raw for Strict and ~43% for Direct, before gzip.

**Paths are scrubbed, and the scrub is verified.** Traces carry the operating user's
absolute paths (measured: 1,526 `/home/...` references in a single Strict item). No
committed file in this repo contains them today, and the repo is private only for now,
so the roots are replaced with `$WORKSPACE`/`$HOME`/`$USER` placeholders before hashing
and `verify()` fails if any survive. Only roots derived from the *local* machine are
substituted — a blanket `/data/<x>` regex would silently rewrite paths appearing inside
quoted vLLM-Omni source, corrupting the evidence to protect it.

`path_map` records placeholder -> sha256 prefix of the original root, never the root
itself: recording the literal mapping would reintroduce the path the scrub just removed,
once per file. Analysis never needs the original (placeholders are portable and the
worktree name is derivable from the item), and an operator can still confirm a mapping
locally by hashing their own root.

Usage:
  trace_pack.py backfill <arm_dir>...   pack existing raw into <stem>.trace.json.gz
  trace_pack.py verify   <arm_dir>...   parse, resolve refs, assert the scrub held
  trace_pack.py selftest                round-trip proof over real fixtures
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = 1
SUFFIX = ".trace.json.gz"

# Serialized-size floor for hoisting a node into `blobs`. Interning is bottom-up, so a
# low floor moves dedup down to individual messages (where the repetition actually is)
# rather than whole payload arrays (which differ on every call and so never dedup).
INTERN_THRESHOLD = int(os.environ.get("TRACE_PACK_THRESHOLD", "256"))

HERE = Path(__file__).resolve().parent            # eval/dataset
WORKSPACE = HERE.parents[2]                       # the workspace holding both checkouts

KIND_CLAUDE_CODE = "claude_code"                  # baseline + Direct (stream-json)
KIND_COPILOT_CLI = "copilot_cli"                  # Strict (copilot run directory)

# Files a copilot run directory may contain. Absent ones are skipped, not faked: an arm
# that produced no ensemble artifact must be distinguishable from one whose artifact was
# lost, which is the whole failure this module exists to prevent.
_COPILOT_JSONL = ("events.jsonl", "run_trace.jsonl", "trace.jsonl")
_COPILOT_JSON = ("metrics.json", "progress.json", "task.json")
_COPILOT_TEXT = ("RUN_REPORT.md", "DIAGNOSTICS.md", "ESCALATION.md", "console.log")


# --------------------------------------------------------------------------- scrubbing

def path_roots() -> list[tuple[str, str]]:
    """(absolute_root, placeholder) pairs, longest first.

    Longest-first matters: `$WORKSPACE` must win over `$HOME`/`/data/$USER` when the
    workspace sits inside one of them, or the longer path is left half-substituted.
    """
    home = Path.home().resolve()
    user = home.name
    roots = {str(WORKSPACE.resolve()): "$WORKSPACE", str(home): "$HOME"}
    for parent in ("/data", "/home", "/Users"):
        roots.setdefault(f"{parent}/{user}", f"{parent}/$USER")
    return sorted(roots.items(), key=lambda kv: -len(kv[0]))


def scrub_text(text: str, roots: list[tuple[str, str]]) -> str:
    for root, placeholder in roots:
        if root in text:
            text = text.replace(root, placeholder)
    return text


def scrub(node, roots: list[tuple[str, str]]):
    """Substitute machine roots throughout a decoded JSON tree, keys included."""
    if isinstance(node, str):
        return scrub_text(node, roots)
    if isinstance(node, dict):
        return {scrub(k, roots): scrub(v, roots) for k, v in node.items()}
    if isinstance(node, list):
        return [scrub(v, roots) for v in node]
    return node


def residual_paths(text: str, roots: list[tuple[str, str]]) -> list[str]:
    """Occurrences of *this machine's* identifying roots that the scrub missed.

    Deliberately not a general "no absolute paths" check: `/home/ubuntu/...` quoted
    inside reviewed source is evidence, not a leak, and failing on it would block packing
    for a privacy problem that does not exist.
    """
    return sorted({root for root, _ in roots if root in text})


# ------------------------------------------------------------------- content addressing

def _canon(node) -> str:
    return json.dumps(node, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _is_ref(node) -> bool:
    return isinstance(node, dict) and len(node) == 1 and "$blob" in node


def intern(node, blobs: dict):
    """Hoist large nodes into `blobs`, bottom-up, returning the compacted tree.

    Bottom-up is the load-bearing detail. Top-down would intern a whole `payload` array
    as one blob per LLM call; since each call's array differs by one message, nothing
    would ever dedup and the pack would be as large as the raw.
    """
    if isinstance(node, dict):
        node = {k: intern(v, blobs) for k, v in node.items()}
    elif isinstance(node, list):
        node = [intern(v, blobs) for v in node]
    if _is_ref(node):
        return node
    if not isinstance(node, (dict, list, str)):
        return node
    body = node if isinstance(node, str) else _canon(node)
    if len(body) < INTERN_THRESHOLD:
        return node
    digest = hashlib.sha256(
        (body if isinstance(node, str) else body).encode("utf-8")).hexdigest()
    blobs.setdefault(digest, node)
    return {"$blob": digest}


def expand(node, blobs: dict):
    """Exact inverse of `intern`."""
    if _is_ref(node):
        return expand(blobs[node["$blob"]], blobs)
    if isinstance(node, dict):
        return {k: expand(v, blobs) for k, v in node.items()}
    if isinstance(node, list):
        return [expand(v, blobs) for v in node]
    return node


# ------------------------------------------------------------------------ source readers

def _sha_bytes(path: Path) -> dict:
    raw = path.read_bytes()
    return {"name": path.name, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def _read_jsonl(path: Path) -> list:
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"_unparsed": line})
    return out


def read_claude_code(events_path: Path) -> tuple[dict, list[dict]]:
    return {"events": _read_jsonl(events_path)}, [_sha_bytes(events_path)]


def read_copilot_run(item_root: Path) -> tuple[dict, list[dict]]:
    """Every `run-*` directory under one item's private RUN_ROOT.

    All of them, not just the last: the Strict runner retries on intent-clarify and on
    rc=3, and a retried item's earlier attempts are exactly where a systematic failure
    would show.
    """
    runs, sources = [], []
    for run_dir in sorted(p for p in item_root.glob("run-*") if p.is_dir()):
        rec: dict = {"run": run_dir.name}
        for name in _COPILOT_JSONL:
            f = run_dir / name
            if f.is_file():
                rec[name[:-6]] = _read_jsonl(f)
                sources.append({**_sha_bytes(f), "name": f"{run_dir.name}/{name}"})
        for name in _COPILOT_JSON:
            f = run_dir / name
            if f.is_file():
                try:
                    rec[name[:-5]] = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                sources.append({**_sha_bytes(f), "name": f"{run_dir.name}/{name}"})
        for f in sorted(run_dir.glob("ensemble_*.json")):
            try:
                rec.setdefault("ensemble", {})[f.stem] = json.loads(
                    f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            sources.append({**_sha_bytes(f), "name": f"{run_dir.name}/{f.name}"})
        for name in _COPILOT_TEXT:
            f = run_dir / name
            if f.is_file():
                rec[name.split(".")[0].lower()] = f.read_text(
                    encoding="utf-8", errors="replace")
                sources.append({**_sha_bytes(f), "name": f"{run_dir.name}/{name}"})
        runs.append(rec)
    return {"runs": runs}, sources


# ------------------------------------------------------------------------------- index

def _index_claude_code(streams: dict) -> dict:
    calls, mcp, usage = [], [], {}
    for event in streams.get("events", []):
        if event.get("type") == "result":
            usage = {"num_turns": event.get("num_turns"),
                     "total_cost_usd": event.get("total_cost_usd"),
                     "usage": event.get("usage")}
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        for block in message.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = str(block.get("name") or "?")
            calls.append({"seq": len(calls) + 1, "name": name, "id": block.get("id")})
            if name.startswith("mcp__"):
                mcp.append({"seq": len(calls), "name": name})
    return {"tool_calls": calls, "mcp_calls": mcp, "result": usage}


def _index_copilot(streams: dict) -> dict:
    runs = []
    for rec in streams.get("runs", []):
        spans = rec.get("trace") or []
        kinds: dict[str, int] = {}
        for event in rec.get("events") or []:
            kinds[str(event.get("kind"))] = kinds.get(str(event.get("kind")), 0) + 1
        runs.append({
            "run": rec.get("run"),
            "event_kinds": kinds,
            "span_names": sorted({str(s.get("name")) for s in spans if s.get("name")}),
            "has_ensemble": bool(rec.get("ensemble")),
            "task": (rec.get("task") or {}).get("spec")
                    or next((r.get("spec") for r in (rec.get("run_trace") or [])
                             if isinstance(r, dict) and r.get("spec")), None),
        })
    return {"runs": runs}


# -------------------------------------------------------------------------- pack / io

def _gz_size(obj) -> int:
    return len(gzip.compress(
        json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8"), 6))


def pack(kind: str, streams: dict, sources: list[dict], meta: dict) -> dict:
    """Scrub, then store in whichever encoding is actually smaller for this trace.

    Interning is not universally a win, and assuming it was would have cost ~30% on two
    of the four arms. Measured per shape: a copilot run is 99% repeated message history,
    so interning beats plain compression 5.7x (533K vs 3,039K); a Claude Code stream has
    little duplication, so the sha256 keys and the loss of gzip locality make interning
    *lose* by 30% (139K vs 107K). Rather than hardcode that split — which would silently
    become wrong when either harness changes shape — both encodings are built and the
    smaller is kept, with the losing size recorded so the choice stays auditable.
    """
    roots = path_roots()
    scrubbed = scrub(streams, roots)
    blobs: dict = {}
    compacted = intern(scrubbed, blobs)
    inline_size = _gz_size({"streams": scrubbed, "blobs": {}})
    interned_size = _gz_size({"streams": compacted, "blobs": blobs})
    if inline_size <= interned_size:
        encoding, streams_out, blobs = "inline", scrubbed, {}
    else:
        encoding, streams_out = "interned", compacted
    index = (_index_claude_code(scrubbed) if kind == KIND_CLAUDE_CODE
             else _index_copilot(scrubbed))
    return {
        "schema": SCHEMA,
        "kind": kind,
        "meta": {
            **scrub(meta, roots),
            "sources": sources,
            "encoding": encoding,
            "encoding_sizes_gz": {"inline": inline_size, "interned": interned_size},
            "intern_threshold": INTERN_THRESHOLD,
            # placeholder -> sha256 prefix of the original root. Never the root itself;
            # see the module docstring.
            "path_map": {placeholder: hashlib.sha256(root.encode()).hexdigest()[:16]
                         for root, placeholder in roots},
        },
        "blobs": blobs,
        "streams": streams_out,
        "index": index,
    }


def write(arm_dir: Path, stem: str, packed: dict) -> Path:
    """Atomic, deterministic write. mtime=0 so identical content produces identical
    bytes — a repack that changed nothing must not show up as a diff."""
    out = arm_dir / f"{stem}{SUFFIX}"
    tmp = out.with_suffix(out.suffix + f".tmp{os.getpid()}")
    body = json.dumps(packed, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with gzip.GzipFile(filename="", mode="wb", fileobj=tmp.open("wb"), mtime=0) as fh:
        fh.write(body)
    tmp.replace(out)
    return out


def read(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def restore(packed: dict) -> dict:
    """The original (path-scrubbed) stream tree."""
    return expand(packed["streams"], packed.get("blobs") or {})


# ------------------------------------------------------------- write-time entry points

def pack_claude_code(arm_dir: Path, stem: str, events: list[dict], meta: dict) -> Path:
    """Called from `cc_arm_common.write_run` — baseline and Direct."""
    streams = {"events": events}
    body = "\n".join(json.dumps(e, ensure_ascii=False) for e in events).encode("utf-8")
    sources = [{"name": f"{stem}.events.jsonl", "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest()}]
    return write(arm_dir, stem, pack(KIND_CLAUDE_CODE, streams, sources, meta))


def pack_copilot_item(arm_dir: Path, stem: str, item_root: Path, meta: dict) -> Path:
    """Called from `run_copilot_arm.one` — Strict."""
    streams, sources = read_copilot_run(item_root)
    return write(arm_dir, stem, pack(KIND_COPILOT_CLI, streams, sources, meta))


# ------------------------------------------------------------------------------ verify

def verify_file(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        packed = read(path)
    except Exception as exc:  # noqa: BLE001 — any failure to read is the finding
        return [f"{path.name}: unreadable ({exc})"]
    if packed.get("schema") != SCHEMA:
        problems.append(f"{path.name}: schema {packed.get('schema')} != {SCHEMA}")
    if packed.get("kind") not in (KIND_CLAUDE_CODE, KIND_COPILOT_CLI):
        problems.append(f"{path.name}: unknown kind {packed.get('kind')!r}")
    blobs = packed.get("blobs") or {}
    try:
        restored = restore(packed)
    except KeyError as exc:
        return problems + [f"{path.name}: dangling blob ref {exc}"]
    except RecursionError:
        return problems + [f"{path.name}: cyclic blob refs"]
    for digest, node in blobs.items():
        body = node if isinstance(node, str) else _canon(node)
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != digest:
            problems.append(f"{path.name}: blob {digest[:12]} fails its own hash")
            break
    text = json.dumps(restored, ensure_ascii=False)
    leaked = residual_paths(text, path_roots())
    if leaked:
        problems.append(f"{path.name}: unscrubbed machine path(s) {leaked}")
    if packed["kind"] == KIND_CLAUDE_CODE and not restored.get("events"):
        problems.append(f"{path.name}: no events retained")
    if packed["kind"] == KIND_COPILOT_CLI and not restored.get("runs"):
        problems.append(f"{path.name}: no run directories retained")
    return problems


def expected_stems(arm_dir: Path) -> list[str]:
    """Items the arm claims to have produced — one `.md` per item."""
    return sorted(p.name[:-3] for p in arm_dir.glob("*.md")
                  if p.name not in ("README.md", "RESULTS_INDEX.md"))


def verify_arm(arm_dir: Path) -> tuple[list[str], int]:
    problems: list[str] = []
    stems = expected_stems(arm_dir)
    checked = 0
    for stem in stems:
        path = arm_dir / f"{stem}{SUFFIX}"
        if not path.is_file():
            problems.append(f"{arm_dir.name}/{stem}: MISSING trace")
            continue
        checked += 1
        problems.extend(f"{arm_dir.name}/" + p for p in verify_file(path))
    return problems, checked


# --------------------------------------------------------------------------- backfill

def backfill_arm(arm_dir: Path) -> tuple[int, list[str]]:
    """Pack whatever raw survives next to an already-completed arm.

    Read-only over the raw: packing never moves or deletes `events.jsonl` or `runs/`,
    so a bad pack costs a repack, not the evidence.
    """
    done, skipped = 0, []
    manifest = {}
    mf = arm_dir / "manifest.json"
    if mf.is_file():
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    for stem in expected_stems(arm_dir):
        cost = {}
        cj = arm_dir / f"{stem}.cost.json"
        if cj.is_file():
            try:
                cost = json.loads(cj.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cost = {}
        meta = {"arm": arm_dir.name, "stem": stem, "backfilled": True,
                "head": cost.get("head"), "base": cost.get("base"),
                "resolved_model": cost.get("resolved_model"),
                "arm_manifest": {k: manifest.get(k) for k in
                                 ("arm", "engine", "llm", "model_requested",
                                  "resolved_models", "mcp_server") if k in manifest}}
        events_file = arm_dir / f"{stem}.events.jsonl"
        item_root = arm_dir / "runs" / stem
        if events_file.is_file():
            streams, sources = read_claude_code(events_file)
            write(arm_dir, stem, pack(KIND_CLAUDE_CODE, streams, sources, meta))
            done += 1
        elif item_root.is_dir() and any(item_root.glob("run-*")):
            streams, sources = read_copilot_run(item_root)
            if not streams["runs"]:
                skipped.append(f"{stem}: run dir present but empty")
                continue
            write(arm_dir, stem, pack(KIND_COPILOT_CLI, streams, sources, meta))
            done += 1
        else:
            skipped.append(f"{stem}: no raw trace on disk (unrecoverable)")
    return done, skipped


# --------------------------------------------------------------------------- selftest

def _selftest() -> int:
    """Round-trip equality against real fixtures, not synthetic ones.

    Synthetic events would prove the code round-trips the shapes I imagined. The
    failure this module prevents was caused by real data having a shape nobody modelled.
    """
    roots = path_roots()
    fixtures = []
    cc = HERE / "arms" / "direct_opus5_r1"
    for p in sorted(cc.glob("pr*.events.jsonl"))[:2]:
        fixtures.append((KIND_CLAUDE_CODE, p))
    for arm in ("copilot_v5_flash_r1", "copilot_v6_pro_r1"):
        runs = HERE / "arms" / arm / "runs"
        for p in sorted(runs.glob("pr*"))[:1] if runs.is_dir() else []:
            fixtures.append((KIND_COPILOT_CLI, p))
    if not fixtures:
        print("selftest: no fixtures on disk — nothing to prove"); return 1
    failures = 0
    for kind, src in fixtures:
        if kind == KIND_CLAUDE_CODE:
            streams, sources = read_claude_code(src)
        else:
            streams, sources = read_copilot_run(src)
        packed = pack(kind, streams, sources, {"arm": "selftest", "stem": src.name})
        restored = restore(packed)
        want = scrub(streams, roots)
        raw = len(json.dumps(streams, ensure_ascii=False).encode())
        gz = len(gzip.compress(json.dumps(packed, ensure_ascii=False,
                                          sort_keys=True).encode()))
        ok = restored == want
        failures += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {kind:12s} {src.name:34s} "
              f"raw={raw/1024:8.0f}K  packed+gz={gz/1024:7.0f}K  "
              f"({100*gz/raw:.0f}%)  {packed['meta']['encoding']:8s} "
              f"blobs={len(packed['blobs'])}")
        if ok and residual_paths(json.dumps(restored, ensure_ascii=False), roots):
            print("        FAIL: machine path survived the scrub"); failures += 1
    print("selftest:", "OK" if not failures else f"{failures} FAILURE(S)")
    return 1 if failures else 0


# -------------------------------------------------------------------------------- cli

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-4]); return 2
    cmd, args = argv[1], [Path(a) for a in argv[2:]]
    if cmd == "selftest":
        return _selftest()
    if cmd == "backfill":
        total = 0
        for arm in args:
            done, skipped = backfill_arm(arm)
            total += done
            print(f"{arm.name}: packed {done}")
            for s in skipped:
                print(f"   skipped {s}")
        print(f"packed {total} item(s)")
        return 0
    if cmd == "verify":
        problems, checked = [], 0
        for arm in args:
            p, c = verify_arm(arm)
            problems += p
            checked += c
        print(f"verified {checked} trace(s) across {len(args)} arm(s)")
        for p in problems:
            print(f"  {p}")
        return 1 if problems else 0
    print(f"unknown command {cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
