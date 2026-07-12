"""`run_agent_step_ensemble` — a robustness wrapper over `run_agent_step`.

A single agent-step run has high variance (each run samples one corner of its
checklist). The ensemble runs the same step once per perspective lens, unions
the list-valued `merge_key` items, and reduces them with one verify-and-merge
call: cross-lens consensus is kept, single-lens items must survive verification
against the evidence, misreads are dropped, kept items are rewritten to be
self-contained. Generalizes to any agent step whose extension output is a list.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from ...llm import parse_json_reply
from ...scopes import ToolScope
from ..step import FailureKind, StepContext, StepResult
from .runner import run_agent_step
from .utils import _build_evidence, _to_step_result


async def run_agent_step_ensemble(
    ctx: StepContext,
    *,
    step_name: str,
    purpose: str,
    evidence: dict[str, str],
    lenses: list[dict],
    merge_key: str,
    guidance: str = "",
    expected: str = "",
    output_extension: dict[str, str] | None = None,
    scope: ToolScope | None = None,
    extra_tools: dict[str, Any] | None = None,
    max_iters: int | None = None,
    merge_guidance: str = "",
) -> tuple[StepResult, dict]:
    """Robustness wrapper over `run_agent_step`: perspective-diverse fan-out,
    then a verify-and-merge reduction.

    A single agent-step run has high variance — each run samples one corner of
    its checklist (eval/ANALYSIS.md: RQS 0.11-0.38 across identical configs,
    while the UNION of samples covered 5/8 ground-truth issues). The ensemble
    runs the same step once per lens (a depth priority, not a restriction),
    unions the list-valued `merge_key` items, and reduces them with one
    verify-and-merge call: cross-lens consensus is kept, single-lens items must
    survive verification against the evidence, misreads are dropped, and every
    kept item is rewritten to be self-contained and evidence-grounded.

    Generalizes to any agent step whose extension output is a list — review
    comments, triage rows, debug hypotheses — lenses and merge_guidance are the
    only step-specific inputs.
    """
    if ctx.llm is None or not ctx.llm.available:
        return (StepResult(False, FailureKind.BLOCKED,
                           "LLM not configured — cannot run agent step"), {})

    budget = max_iters or ctx.settings.ensemble_lens_max_iters
    k = max(1, int(ctx.settings.ensemble_samples_per_lens))

    async def _one_lens(lens: dict, j: int, idx: int = 0) -> tuple[str, StepResult, dict]:
        """Run `run_agent_step` once for a single lens (sample `j`), instructing
        the agent to go DEEP on that lens as its depth priority while peers cover
        the rest. `idx` staggers concurrent starts: lenses share a byte-identical
        prompt prefix (tools+system+dispatch render), so giving the first lens a
        head start lets the provider cache the prefix before the siblings send
        it — simultaneous identical prefixes all miss. Returns the lens name,
        the StepResult, and the output dict."""
        if idx and ctx.settings.ensemble_stagger_seconds > 0:
            await asyncio.sleep(idx * ctx.settings.ensemble_stagger_seconds)
        suffix = f"/{j}" if k > 1 else ""
        lens_guidance = (
            f"{guidance}\n\n## Your assigned lens: {lens['name']}\n"
            f"{lens['focus']}\nGo DEEP on this lens — it is your depth "
            "priority; report other issues only if they surface on the way. "
            "Peer agents cover the other lenses.")
        result, output = await run_agent_step(
            ctx, step_name=f"{step_name}#{lens['name']}{suffix}",
            purpose=purpose,
            evidence=evidence, guidance=lens_guidance, expected=expected,
            output_extension=output_extension, scope=scope,
            extra_tools=extra_tools, max_iters=budget)
        if (ctx.settings.ensemble_zero_yield_retry and output and not (output.get(merge_key) or [])):
            # zero-yield lens: one cheap single-lens re-ask beats the full
            # 8-lens ensemble retry it used to trigger (T3 forensics #6)
            ctx.trace.record("lens_zero_yield_retry", lens=str(lens["name"]))
            result, output = await run_agent_step(
                ctx, step_name=f"{step_name}#{lens['name']}{suffix}/retry",
                purpose=purpose, evidence=evidence,
                guidance=lens_guidance + "\n\nYour first pass yielded zero "
                "candidates. Re-check your two highest-risk hunks; emit every "
                "plausible candidate (do not self-censor) or a [validated] "
                "finding for each checklist item you cleared.",
                expected=expected, output_extension=output_extension,
                scope=scope, extra_tools=extra_tools, max_iters=budget)
        return str(lens["name"]), result, output

    # lenses (and repeat samples of each lens — a single sample's item list is
    # the highest-variance link, so the union over samples is the recall
    # floor) are independent by construction — run them concurrently; the
    # sequential ensemble's wall-clock was its whole efficiency penalty
    jobs = [(lens, j) for lens in lenses for j in range(1, k + 1)]
    if ctx.settings.ensemble_parallel and len(jobs) > 1:
        runs = await asyncio.gather(
            *(_one_lens(lens, j, idx) for idx, (lens, j) in enumerate(jobs)))
    else:
        runs = [await _one_lens(lens, j) for lens, j in jobs]
    samples = [(name, output) for name, _, output in runs if output]
    last_result = runs[-1][1] if runs else None
    if not samples:
        return (last_result or StepResult(
            False, FailureKind.RETRYABLE,
            f"{step_name}: all ensemble samples failed"), {})

    # collapse EXACT duplicates before numbering — identical items from repeat
    # samples carry consensus, not new information
    candidates: list[dict] = []
    by_sig: dict[str, dict] = {}
    for name, output in samples:
        for item in output.get(merge_key) or []:
            base = dict(item) if isinstance(item, dict) else {"item": item}
            sig = json.dumps(base, ensure_ascii=False, sort_keys=True)
            if sig in by_sig:
                tagged = by_sig[sig]
                tagged["consensus"] += 1
                if name not in tagged["lenses"]:
                    tagged["lenses"].append(name)
            else:
                tagged = {**base, "lenses": [name], "consensus": 1}
                by_sig[sig] = tagged
                candidates.append(tagged)

    def _dedup_union(key: str) -> list:
        """Union the list-valued `key` across all samples, dropping exact
        duplicates (dict/list items compared by canonical JSON, scalars by str),
        preserving first-seen order. Used to merge the deterministic base fields
        that the reducer does not judge."""
        out, seen = [], set()
        for _, o in samples:
            for v in o.get(key) or []:
                sig = json.dumps(v, ensure_ascii=False, sort_keys=True) \
                    if isinstance(v, (dict, list)) else str(v)
                if sig not in seen:
                    seen.add(sig)
                    out.append(v)
        return out

    # base fields are merged DETERMINISTICALLY — the reducer only judges the
    # merge_key items (asking it to re-emit the whole contract truncated the
    # items behind verbose scalar fields in live runs)
    merged: dict = dict(samples[0][1])
    for key in ("findings", "files_read", "files_modified", "tests_requested",
                "tests_run", "assumptions", "blockers"):
        merged[key] = _dedup_union(key)
    # the reducer judges ITEMS, not the step: models conflate the step's status
    # with the reviewed artifact's verdict, so status comes from the samples
    if any(o.get("status") == "success" for _, o in samples):
        merged["status"] = "success"

    if len(candidates) <= 2 and all(c.get("consensus", 1) >= 2
                                    for c in candidates):
        # fast path: a small union whose every item was independently
        # replicated across samples needs no arbitration — skip the
        # reducer's latency. A single-lens singleton does NOT qualify: an
        # unreplicated claim must still face verification (a hallucinated
        # blocker once sailed through here and became the entire review)
        merged[merge_key] = [
            {k: v for k, v in c.items() if k not in ("lenses", "consensus")}
            for c in candidates]
        ctx.trace.record("agent_ensemble", step=step_name,
                         lenses=[name for name, _ in samples],
                         candidates=len(candidates), merged=len(candidates),
                         dropped=0, verified=False)
        return _to_step_result(merged, f"[ensemble x{len(samples)}] "), merged

    # the reducer never re-emits the merged list (free-form regeneration is
    # where findings silently died in live runs): it returns one verdict PER
    # NUMBERED CANDIDATE and code assembles the result deterministically —
    # any candidate it fails to mention is KEPT (fail-open per item)
    reduce_contract = {
        "verdicts": ('list of {"i": candidate index, "action": '
                     '"keep"|"drop"|"dup", "of": null | index this '
                     'duplicates, "severity": optional corrected severity, '
                     '"comment": optional self-contained rewrite, '
                     '"why": one line}'),
        "summary": "one-paragraph merged outcome",
    }
    # the reducer verifies against the evidence, so it needs far more of it
    # than the per-lens dispatch cap (the lenses had tools; the reducer has none)
    capped, _ = _build_evidence(ctx, evidence,
                                cap=ctx.settings.ensemble_merge_evidence_chars)
    ev_text = "\n\n".join(f"### {k}\n{v}" for k, v in capped.items())
    merge_system = (
        "You are the verify-and-merge reducer for an ensemble of independent "
        "agent samples of the same step. You receive their NUMBERED candidate "
        "items (tagged with the lens(es) that produced each and a consensus "
        "count) plus the evidence. Emit one verdict per candidate index:\n"
        "1. VERIFY each candidate, then action=drop the ones that fail: "
        "misreads of the evidence, claims the evidence already handles, "
        "vague items, cited evidence that contradicts the diff (e.g. a "
        "quoted stacktrace or file content inconsistent with the shown "
        "change), and pure stylistic alternatives to correct behavior — "
        "give the why. IMPORTANT: the candidates come from agents that had "
        "repo tools; you hold only this evidence pack. A claim grounded in "
        "cited repo evidence (a named file/grep and what it showed) is "
        "judged on coherence and specificity — NEVER drop it merely because "
        "the cited file is outside your evidence. A candidate with "
        "consensus >= 2 needs a concrete refutation to drop. A verified "
        "item is never dropped just for low severity.\n"
        "2. action=dup with of=<index> when two candidates report the same "
        "underlying issue — rewrite the surviving index with the most "
        "precise phrasing and the highest severity of the pair.\n"
        "3. action=keep otherwise; use 'comment' to rewrite the item so it "
        "is self-contained and verifiable: FIRST the concrete fact from the "
        "evidence it is grounded in, THEN the directive (what to change, "
        "where, why). Fix line numbers to lines actually visible in the "
        "evidence. Unmentioned candidates are kept unchanged.\n"
        + (f"4. {merge_guidance}\n" if merge_guidance else "")
        + "\nYour FINAL message must be a single JSON object with exactly "
        "these fields:\n" + json.dumps(reduce_contract, ensure_ascii=False))
    numbered = [{"i": i, **c} for i, c in enumerate(candidates)]
    # single untooled reduction call: a tool-looped reducer measurably
    # over-dropped (reviews shrank to 1-2 comments, starving recall and
    # flipping verdicts) and added 1-2 min of latency; repo-cited claims are
    # judged on coherence, not re-derived
    merge_prompt = (
        f"## CANDIDATE ITEMS ({merge_key}, from {len(samples)} samples)\n"
        + json.dumps(numbered, ensure_ascii=False, indent=1)
        + f"\n\n## EVIDENCE\n{ev_text}")
    reply = await asyncio.to_thread(
        ctx.llm.create, system=merge_system,
        messages=[{"role": "user", "content": merge_prompt}],
        max_tokens=max(6000, ctx.settings.llm_max_tokens))
    reply_text = reply.text
    reduce_in = (reply.usage or {}).get("input_tokens", 0)
    reduce_out = (reply.usage or {}).get("output_tokens", 0)
    try:  # archive the reduction exchange — reducer failures are hard to debug
        ctx.run_dir.mkdir(parents=True, exist_ok=True)
        (ctx.run_dir / f"ensemble_{step_name.replace('/', '_')}.json").write_text(
            json.dumps({"candidates": numbered, "reply": reply_text},
                       ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    reduced = parse_json_reply(reply_text or "")
    if not (isinstance(reduced, dict) and isinstance(reduced.get("verdicts"), list)):
        reduced = None
        if (reply_text or "").strip():  # one repair round (never on empty text)
            fix = ctx.llm.create(
                system=("Convert the draft into a single JSON object matching "
                        "this contract exactly (keep all substance):\n"
                        + json.dumps(reduce_contract, ensure_ascii=False)),
                messages=[{"role": "user", "content": str(reply_text)[:20_000]}],
                max_tokens=max(6000, ctx.settings.llm_max_tokens))
            reduce_in += (fix.usage or {}).get("input_tokens", 0)
            reduce_out += (fix.usage or {}).get("output_tokens", 0)
            obj = parse_json_reply(fix.text)
            if isinstance(obj, dict) and isinstance(obj.get("verdicts"), list):
                reduced = obj
    verified = reduced is not None
    kept: dict[int, dict] = {i: dict(c) for i, c in enumerate(candidates)}
    dropped: list[str] = []
    if reduced is not None:
        by_i: dict[int, dict] = {}
        for v in reduced.get("verdicts") or []:
            if isinstance(v, dict) and isinstance(v.get("i"), int) \
                    and 0 <= v["i"] < len(candidates):
                by_i[v["i"]] = v
        for i, v in by_i.items():  # drops first
            if str(v.get("action", "")).lower() == "drop":
                kept.pop(i, None)
                dropped.append(f"[{i}] {v.get('why', '')}")
        for i, v in by_i.items():  # then dups (a dup of a dropped item stays)
            of = v.get("of")
            if str(v.get("action", "")).lower() == "dup" \
                    and isinstance(of, int) and of != i and of in kept \
                    and i in kept:
                kept[of]["consensus"] = kept[of].get("consensus", 1) + 1
                kept.pop(i)
        for i, v in by_i.items():  # then rewrites
            if i in kept:
                if isinstance(v.get("comment"), str) and v["comment"].strip() \
                        and "comment" in kept[i]:
                    kept[i]["comment"] = v["comment"]
                if v.get("severity") and "severity" in kept[i]:
                    kept[i]["severity"] = str(v["severity"])
        merged["summary"] = str(reduced.get("summary")
                                or merged.get("summary") or "")
    else:
        merged["summary"] = (f"ensemble of {len(samples)} samples "
                             "(merge reduction failed; unverified union)")
    merged[merge_key] = [
        {k: v for k, v in kept[i].items() if k not in ("lenses", "consensus")}
        for i in sorted(kept)]
    ctx.trace.record(
        "agent_ensemble", step=step_name,
        lenses=[name for name, _ in samples],
        candidates=len(candidates),
        merged=len(merged.get(merge_key) or []),
        dropped=len(dropped),
        verified=verified,
        # reducer-call usage (lens usage is on each lens's agent_output event)
        input_tokens=reduce_in, output_tokens=reduce_out)
    prefix = f"[ensemble x{len(samples)}] "
    return _to_step_result(merged, prefix), merged
