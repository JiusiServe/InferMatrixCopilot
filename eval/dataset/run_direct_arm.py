#!/usr/bin/env python3
"""The Direct-mode arm: the same Opus 5 host agent as the pinned baseline, plus our MCP.

Direct makes **zero LLM calls** — the host agent does the reviewing, and the copilot
supplies knowledge routing, an execution budget and a completion gate. So the arm is a
host agent driven by our MCP, and the baseline harness already *is* a headless host
agent. That makes the contrast nearly free and unusually clean:

  baseline = Opus 5 Claude Code, PR-time tree, read-only tools, **no MCP**
  direct   = Opus 5 Claude Code, PR-time tree, read-only tools, **+ our MCP**

Same model, same trees, same frozen snapshot, same tool surface, same isolation.

**What the delta is not.** It is not "the knowledge layer alone". Direct differs from
the baseline by two things at once — the MCP server and the inlined imreview protocol —
so this measures the Direct integration *as a whole*, which is the thing we actually
ship. Attributing the result to routing would need a further arm holding the protocol
constant, which is not built here; the claim is narrowed instead.

Skills are disabled on **both** arms and the protocol is inlined as prompt text rather
than loaded as a skill — see `skill_protocol()` for why the plan's "stage only
imreview" turned out to be unachievable and would have confounded the measurement.

**Fail closed on completion.** An arm that silently fell back to plain Claude Code
would produce a perfectly plausible review and be indistinguishable from a null result
for Direct — it would look like "Direct adds nothing" when in fact Direct never ran.
So each item must show exactly one successful `review(mode="direct")` and a successful
`validate_direct_review`, read out of the retained event stream; anything else fails the
item loudly rather than being scored as a Direct result.

The MCP server is pinned to **this checkout's** venv, not the shipped `git+…@main`
config: a moving reference would mean the arm tests code that was never reviewed, and
reproducibility is the entire point of an eval arm.

Usage: run_direct_arm.py [splits] [only_stem]
Env: ARM_OUT (default direct_opus5_r1), ARM_JOBS (default 3), ARM_MODEL
Outputs: eval/dataset/arms/<ARM_OUT>/pr<N>.{md,cost.json,events.jsonl}
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

import cc_arm_common as cc
import trace_pack
from run_ocr_arm import _prepare_worktree, _write_atomic, EXPECTED_HEADS, JUDGE_CAP

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
ARM_DIR = HERE / "arms" / os.environ.get("ARM_OUT", "direct_opus5_r1")
CHECKOUT = Path(__file__).resolve().parents[2]
MCP_BIN = CHECKOUT / ".venv" / "bin" / "infermatrix-copilot-mcp"
SERVER = "infermatrix-copilot"

ARM = "direct_opus5"
SKILL_MD = Path.home() / ".claude" / "skills" / "imreview" / "SKILL.md"
MCP_TOOLS = [f"mcp__{SERVER}__{t}" for t in
             ("review", "validate_direct_review", "get_review_status",
              "get_review_result", "doc_read", "doc_search")]
TOOLS = cc.BASE_TOOLS + cc.VALIDATION_TOOLS + MCP_TOOLS

REVIEW_TOOL = f"mcp__{SERVER}__review"
VALIDATE_TOOL = f"mcp__{SERVER}__validate_direct_review"


def mcp_config(home: Path, worktree: Path) -> Path:
    """One config per item: the server is told which checkout this review is about, and
    the path is the PR-time worktree rather than the shared repo."""
    cfg = home / f"mcp-{worktree.name}.json"
    cfg.write_text(json.dumps({"mcpServers": {SERVER: {
        "command": str(MCP_BIN), "args": [],
        "env": {"PATH": os.environ.get("PATH", ""),
                "HOME": str(home),
                "REPO_PATHS": json.dumps({cc.REPO: str(worktree)}),
                # the eval-leakage policy the copilot arms also ran under
                "PR_CONTEXT_MODE": "no_discussion"}}}}, indent=2) + "\n")
    return cfg


def skill_protocol() -> tuple[str, str]:
    """(protocol text, sha256) — the shipped imreview instructions, inlined.

    The plan called for staging `imreview` into the isolated HOME and running with
    skills enabled. Measured: that does not do what it says. `--setting-sources ""`
    excludes user-level skills, so the staged copy was never loaded, and enabling
    skills at all brings in **16 bundled skills — including a built-in `code-review`**
    that the baseline (running `--disable-slash-commands`) does not have. That is not a
    neutral difference: it would hand Direct a general code-review capability the
    reference lacks and fold it into the very delta this arm exists to measure.

    So both arms run with skills disabled and identical `skills: []`, and Direct
    receives the protocol as prompt text instead. Same content, no confound, and the
    instructions are visible in the retained events rather than resolved out of band.
    The file is read at run time (not copied) so this cannot drift from what ships, and
    its hash goes in the manifest.
    """
    raw = SKILL_MD.read_text(encoding="utf-8")
    body = raw.split("---", 2)[2].strip() if raw.startswith("---") else raw.strip()
    import hashlib
    return body, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def prompt(pr: int, snap: str, base: str, head: str, protocol: str) -> str:
    return (
        f"Review pull request #{pr} of {cc.REPO} with InferMatrixCopilot in "
        f"**direct** mode, following this protocol exactly:\n\n"
        f"<imreview-protocol>\n{protocol}\n</imreview-protocol>\n\n"
        f"Your working directory IS a read-only checkout of the repository at this "
        f"PR's exact head commit ({head[:12]}) — the merge-base with main is "
        f"{base[:12]}, so `git diff {base} HEAD` is precisely this PR's change.\n\n"
        f"The PR snapshot is already frozen for you (there is no PR discussion "
        f"available, deliberately, and no `gh pr view` in your tool allowlist — use "
        f"exactly this):\n\n{snap}\n\n"
        f"Follow the Direct protocol: report the frozen snapshot state, then call "
        f"`review` once with mode=\"direct\", honour the returned execution budget and "
        f"knowledge routes as given, read every source file you cite as evidence at "
        f"{head[:12]}, and call `validate_direct_review` before treating the review as "
        f"complete.\n\n"
        f"Budget: you have {cc.MAX_TURNS} turns in total. Honour the copilot's returned "
        f"execution budget as a hard ceiling, and leave yourself room to WRITE THE "
        f"REVIEW — an unwritten review scores as silence no matter how good the "
        f"investigation behind it was.\n\n"
        f"IMPORTANT: do not post anything to GitHub (never pass post=true). Output the "
        f"complete consolidated review as your final message — an overall verdict, "
        f"then specific comments with file:line references and what to change."
    )


def _tool_results(events: list[dict]) -> dict[str, dict]:
    """tool_use_id -> {is_error, text} from the tool_result blocks."""
    out: dict[str, dict] = {}
    for e in events:
        msg = e.get("message") or {}
        for block in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                content = block.get("content")
                if isinstance(content, list):
                    text = " ".join(str(c.get("text", "")) for c in content
                                    if isinstance(c, dict))
                else:
                    text = str(content or "")
                out[str(block.get("tool_use_id"))] = {
                    "is_error": bool(block.get("is_error")), "text": text[:4000]}
    return out


def completion_gate(events: list[dict]) -> tuple[bool, dict]:
    """Did Direct actually run, end to end?

    Checks the calls AND their results: a `review` call that errored, or a validation
    gate that never reaches `complete`, is not a completed Direct review even though
    the tool name appears in the transcript.

    What counts as completion is the **last** validation verdict, not the absence of a
    partial one. Measured on the first Direct item: validate returned `partial_review`
    with a specific `missing` list, the agent repaired those items, and the second call
    returned `status: complete, publish_ready: true`. That loop IS the protocol; an
    earlier draft of this gate failed the item for the intermediate state and would
    have rejected correctly-completed Direct reviews as null results — the precise
    confusion this gate exists to prevent, pointed the wrong way.
    """
    results = _tool_results(events)
    ids_by_name: dict[str, list[str]] = {}
    for e in events:
        msg = e.get("message") or {}
        for b in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                ids_by_name.setdefault(str(b.get("name")), []).append(str(b.get("id")))

    review_ids = ids_by_name.get(REVIEW_TOOL, [])
    validate_ids = ids_by_name.get(VALIDATE_TOOL, [])
    ok_reviews = [i for i in review_ids
                  if results.get(i) and not results[i].get("is_error")]
    ok_validates = [i for i in validate_ids
                    if results.get(i) and not results[i].get("is_error")]

    statuses = []
    for i in ok_validates:
        text = results[i].get("text", "")
        try:
            start, end = text.find("{"), text.rfind("}")
            statuses.append(str(json.loads(text[start:end + 1]).get("status")))
        except Exception:  # noqa: BLE001 — an unparseable gate is not a passed gate
            statuses.append("unparseable")

    final_status = statuses[-1] if statuses else None
    detail = {
        "mcp_review_calls": len(review_ids),
        "mcp_review_calls_ok": len(ok_reviews),
        "mcp_validate_calls": len(validate_ids),
        "mcp_validate_calls_ok": len(ok_validates),
        "validate_status_sequence": statuses,
        "validate_final_status": final_status,
    }
    ok = len(ok_reviews) == 1 and final_status == "complete"
    if not ok:
        detail["why"] = (
            "expected exactly one successful review(mode=direct) and a final "
            f"validate_direct_review status of 'complete'; got {detail}")
    return ok, detail


def main() -> int:
    if not MCP_BIN.is_file():
        sys.exit(f"MCP entrypoint not found: {MCP_BIN} — build the venv first")
    splits = set((sys.argv[1] if len(sys.argv) > 1 else "train,val,test").split(","))
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    ds = yaml.safe_load(DATASET.read_text(encoding="utf-8"))
    heads = json.loads(EXPECTED_HEADS.read_text(encoding="utf-8"))
    items = [i for i in ds["pr_review"] if i.get("split") in splits]
    if only:
        items = [i for i in items if f"pr{i['pr']}" == only]
    ARM_DIR.mkdir(parents=True, exist_ok=True)

    protocol, skill_sha = skill_protocol()
    home = cc.provision_home()
    failures: list[str] = []
    oversize: list[tuple[str, int]] = []
    resolved_models: set[str] = set()
    done = 0
    lock = threading.Lock()

    pending = []
    for item in items:
        pr = int(item["pr"])
        stem = f"pr{pr}"
        expected_head = heads.get(str(pr))
        if not expected_head:
            failures.append(f"{stem}: no pinned head in expected_pr_heads.json")
            continue
        if cc.already_done(ARM_DIR, stem, expected_head):
            print(f"  {stem}: already done, skipping")
            done += 1
            continue
        try:
            wt, base = _prepare_worktree(str(pr), expected_head,
                                         int(item["size"]["files"]))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{stem}: {exc}")
            print(f"  {stem}: GATE FAILED — {exc}")
            continue
        pending.append((item, wt, base, expected_head))

    def _review(job) -> None:
        nonlocal done
        item, wt, base, expected_head = job
        pr = int(item["pr"])
        stem = f"pr{pr}"
        snap, snap_sha = cc.snapshot(pr)
        t0 = time.time()
        run = cc.run_cc(prompt(pr, snap, base, expected_head, protocol), TOOLS,
                        home, wt, mcp_config(home, wt), disable_skills=True)
        events = run["events"]
        wall = round(time.time() - t0, 1)
        try:
            model = cc.assert_init(events, expect_skills=[],
                                   expect_mcp=[SERVER], arm=ARM)
        except Exception as exc:  # noqa: BLE001
            with lock:
                failures.append(f"{stem}: {exc}")
                print(f"  {stem}: CONFIG ASSERTION FAILED — {exc}")
            return
        body = cc.final_text(events)
        cost = cc.cost_from(events)
        violations, blocked = cc.audit_events(events, wt,
                                              extra_read_roots=(CHECKOUT / "knowledge",))
        gate_ok, gate = completion_gate(events)
        cost = cc.stamp(cost, item=item, head=expected_head, base=base, model=model,
                        snap_sha=snap_sha, worktree=wt, events=events)
        cost.update({"arm": ARM, "wall_s": wall, "audit_ok": not violations,
                     "audit_violations": violations,
                     "audit_blocked_attempts": blocked,
                     "artifact_chars": len(body),
                     "completion_gate_ok": gate_ok, **gate})
        cc.write_run(ARM_DIR, stem, body or "(no output)", cost, events)
        with lock:
            resolved_models.add(model)
            if len(body) > JUDGE_CAP:
                oversize.append((stem, len(body)))
            if violations:
                failures.append(f"{stem}: audit violations {violations[:3]}")
                print(f"  {stem}: AUDIT FAILED — {violations[:2]}")
                return
            if not gate_ok:
                failures.append(f"{stem}: Direct did not complete — {gate.get('why')}")
                print(f"  {stem}: COMPLETION GATE FAILED — "
                      f"review_ok={gate['mcp_review_calls_ok']} "
                      f"validate_ok={gate['mcp_validate_calls_ok']} "
                      f"partial={gate['validate_reported_partial']}")
                return
            if not body:
                failures.append(f"{stem}: empty review "
                                f"({cost.get('terminal_reason')}, {cost['calls']} turns)")
                print(f"  {stem}: EMPTY REVIEW — {cost.get('terminal_reason')}")
                return
            if cost.get("is_error"):
                failures.append(f"{stem}: run errored ({cost.get('terminal_reason')})")
                print(f"  {stem}: RUN ERROR — {cost.get('terminal_reason')}")
                return
            done += 1
            print(f"  {stem}: wall={wall}s turns={cost['calls']} "
                  f"usd={cost.get('cost_usd')} chars={len(body)} "
                  f"mcp_review={gate['mcp_review_calls_ok']} "
                  f"bash={len(cost['validation_commands'])} "
                  f"validated={cost['ran_validation']}")

    jobs = max(1, int(os.environ.get("ARM_JOBS", "3")))
    try:
        if pending:
            print(f"  reviewing {len(pending)} item(s), {jobs} at a time")
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_review, j) for j in pending]
            for f in as_completed(futs):
                if f.exception():
                    with lock:
                        failures.append(f"worker crashed: {f.exception()}")
        _write_atomic(ARM_DIR / "manifest.json", json.dumps({
            "arm": ARM_DIR.name,
            "mode": "direct — the host agent reviews; the copilot makes zero LLM calls",
            "measures": "the Direct integration as a whole (MCP + imreview skill + "
                        "protocol prompt), NOT knowledge routing in isolation",
            "model_requested": cc.MODEL,
            "resolved_models": sorted(resolved_models),
            "mcp_server": str(MCP_BIN),
            "mcp_pinned_to": "this checkout's venv, not plugins/.mcp.json (git+@main)",
            "harness": "claude -p --output-format stream-json --verbose",
            "isolation": {"setting_sources": "", "skills": "disabled on BOTH arms "
                          "(--disable-slash-commands); enabling them would have added "
                          "16 bundled skills incl. a built-in code-review that the "
                          "baseline lacks", "mcp": SERVER,
                          "home": "isolated, credentials only"},
            "imreview_protocol": "inlined into the prompt from the shipped "
                                 "SKILL.md (read at run time, not copied)",
            "imreview_skill_sha256": skill_sha,
            "allowed_tools": TOOLS,
            "pr_context": "frozen snapshot (no_discussion), byte-identical to the "
                          "pinned baseline's",
            "completion_gate": "exactly one successful review(mode=direct) + a "
                               "successful validate_direct_review, read from events",
            "dataset": DATASET.name, "splits": sorted(splits), "n_items": done,
            "concurrency": jobs,
        }, indent=2) + "\n")
    finally:
        shutil.rmtree(home, ignore_errors=True)

    print(f"\n{done}/{len(items)} items written to {ARM_DIR}")
    # Trace gate: an arm that cannot be explained later is not a finished arm. Checked
    # here rather than trusted, because the wave-1 Strict loss was silent — nothing
    # ever asserted the traces existed until someone needed them, months too late.
    trace_problems, checked = trace_pack.verify_arm(ARM_DIR)
    print(f"trace gate: {checked} packed trace(s) verified")
    failures += [f"trace: {p}" for p in trace_problems]
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
