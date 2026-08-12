#!/usr/bin/env python3
"""Build wave 2 of the PR-review dataset: 10 recent PRs as a pure frozen holdout.

Wave 1 (20 items, merged 2026-07-01..07-10) is left byte-identical, so the 3-arm
gpt-5.6 campaign already run against it stays a valid, citable measurement. Wave 2 is
a separate block with its own splits — all `holdout`, no train, no val.

**Why all holdout.** Wave 1 already carries 10 train items for adaptation but only 5
frozen test items, and that thin frozen set is what caps how confidently any result can
be stated. Never-seen recent PRs are the best possible holdout material, and spending
them on adaptation would burn the exact property that makes them valuable.

**Selection is fixed before anything runs, and is reproducible.** Eligibility is a
stated predicate, the draw is a seeded stratified sample over size bands proportional to
the eligible pool, and both the full pool and the draw are recorded in the provenance
file. Nobody — including me — gets to look at candidate reviews and then pick.

**Two honest caveats recorded in the YAML:**

* Wave 2 skews larger than wave 1 (pool median 8 changed files vs wave 1's 3) and has
  richer ground truth (median 6 human inline comments vs 2). So arm-vs-arm comparisons
  *within* wave 2 are clean, but a wave-1-vs-wave-2 difference is confounded by size and
  must not be read as a staleness effect.
* No GOLD latent-gap items. Those require repo history proving what human review missed
  and a later PR that fixed it; recent PRs have not had time to accumulate that.

**Ground truth is human-only here, unlike wave 1.** `chatgpt-codex-connector` authors
14% of wave 1's GT comments and is the single most frequent author in it — four wave-1
PRs have *no* human GT at all. Wave 2 filters AI reviewers out of the GT and records the
filter, so at least the new block measures recall against people.

Usage: build_wave2.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
GT = HERE / "gt"
HEADS = HERE / "goal-eval" / "expected_pr_heads.json"
PROV = HERE / "goal-eval" / "provenance_wave2.json"
REPO = "vllm-project/vllm-omni"
REPO_PATH = Path("/data/zhoutaichang/copilot/vllm-omni")

MERGED_SINCE = "2026-07-11"        # the day after wave 1 was constructed
MIN_HUMAN_COMMENTS = 2             # a PR with <2 human inline comments has near-empty GT
SEED = "vllm-omni-wave2-2026-08-12"
N_TARGET = 10
BANDS = (("1-3", 1, 3), ("4-9", 4, 9), ("10-24", 10, 24), ("25+", 25, 10**6))

_AI = ("bot", "codex", "copilot-pull-request")


def is_ai(login: str) -> bool:
    return any(b in (login or "").lower() for b in _AI)


def gh_json(*args: str):
    p = subprocess.run(["gh", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    if p.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {p.stderr.strip()[:200]}")
    return json.loads(p.stdout or "[]")


def gh_text(*args: str) -> str:
    p = subprocess.run(["gh", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    if p.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {p.stderr.strip()[:200]}")
    return p.stdout


def band_of(files: int) -> str:
    for name, lo, hi in BANDS:
        if lo <= files <= hi:
            return name
    return "25+"


def eligible_pool(exclude: set[int]) -> list[dict]:
    """Every merged PR since MERGED_SINCE with real human review, minus wave 1.

    Our own `vllm-omni-review-bot` reviews are an exclusion criterion, not just a note:
    scoring the copilot against ground truth that contains the copilot's own output
    would be circular. (Measured: zero of the eligible set is affected — the bot posts
    owner-assignment comments on open PRs, not reviews on merged ones — but the
    predicate has to be in the code, not in the luck.)
    """
    prs = gh_json("pr", "list", "--repo", REPO, "--state", "merged", "--limit", "150",
                  "--search", f"merged:>={MERGED_SINCE}",
                  "--json", "number,title,mergedAt,changedFiles,additions,deletions,author")
    out = []
    for p in prs:
        n = p["number"]
        if n in exclude:
            continue
        cs = gh_json("api", f"repos/{REPO}/pulls/{n}/comments", "--paginate")
        human = [c for c in cs if not is_ai(c.get("user", {}).get("login"))]
        if any(c.get("user", {}).get("login") == "vllm-omni-review-bot" for c in cs):
            continue
        if len(human) < MIN_HUMAN_COMMENTS:
            continue
        head = gh_text("api", f"repos/{REPO}/pulls/{n}", "--jq", ".head.sha").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            continue
        out.append({
            "pr": n, "head": head, "title": p["title"], "merged": p["mergedAt"][:10],
            "author": (p.get("author") or {}).get("login", "?"),
            "files": p["changedFiles"], "add": p["additions"], "del": p["deletions"],
            "human_inline": len(human), "ai_inline": len(cs) - len(human),
            "band": band_of(p["changedFiles"]),
        })
    return sorted(out, key=lambda d: d["pr"])


def range_gate_ok(pr: int, head: str, declared: int) -> tuple[bool, int]:
    """Does `merge-base(head, origin/main)..head` isolate exactly this PR's files?

    The arms enforce this (`run_ocr_arm._prepare_worktree`) and refuse the item when it
    fails, so an item that fails it is not a dataset item at all — it is an item that
    every arm will skip. Measured on the first draw: PR 5790 reports 10 changed files to
    the API but yields 109 over the range, because the branch trails main far enough
    that the merge-base predates a pile of unrelated commits.

    This is a mechanical runnability property, independent of anything about review
    quality, so filtering on it introduces no selection bias — unlike filtering on
    anything the reviews say.
    """
    def g(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=str(REPO_PATH), capture_output=True,
                              text=True, timeout=300).stdout.strip()
    if subprocess.run(["git", "cat-file", "-e", f"{head}^{{commit}}"],
                      cwd=str(REPO_PATH), capture_output=True).returncode != 0:
        subprocess.run(["git", "fetch", "--quiet", "origin", f"pull/{pr}/head"],
                       cwd=str(REPO_PATH), capture_output=True, timeout=600)
    base = g("merge-base", head, "origin/main")
    if not base:
        return False, -1
    n = len([x for x in g("diff", "--name-only", base, head).splitlines() if x])
    return n == declared, n


def stratified_draw(pool: list[dict], n: int) -> tuple[list[dict], dict]:
    """Proportional allocation across size bands, seeded, largest-remainder rounding."""
    by_band: dict[str, list[dict]] = {b[0]: [] for b in BANDS}
    for item in pool:
        by_band[item["band"]].append(item)
    total = len(pool)
    exact = {b: len(v) * n / total for b, v in by_band.items()}
    quota = {b: int(v) for b, v in exact.items()}
    # largest remainder, ties broken by band order so the result is deterministic
    while sum(quota.values()) < n:
        b = max(by_band, key=lambda k: (exact[k] - quota[k], -len(by_band[k]) == 0, k))
        if quota[b] >= len(by_band[b]):
            exact[b] = -1
            continue
        quota[b] += 1
    # Seeded permutation per stratum, then walk it taking items that pass the range
    # gate until the quota is met — rejection sampling, not re-rolling. Deterministic:
    # the permutation depends only on SEED and the sorted candidate list, so a rejected
    # item never changes which item follows it.
    picked, rejected = [], []
    for b, _lo, _hi in BANDS:
        cands = sorted(by_band[b], key=lambda d: d["pr"])
        order = random.Random(f"{SEED}:{b}").sample(cands, len(cands))
        taken = 0
        for c in order:
            if taken >= quota[b]:
                break
            ok, got = range_gate_ok(c["pr"], c["head"], c["files"])
            if not ok:
                c = {**c, "range_files": got}
                rejected.append(c)
                print(f"    reject #{c['pr']} ({b}): declares {c['files']} files, "
                      f"range yields {got} — every arm would refuse it")
                continue
            picked.append(c)
            taken += 1
        if taken < quota[b]:
            raise RuntimeError(f"band {b}: only {taken} of {quota[b]} candidates pass "
                               "the range gate — widen the pool")
    return sorted(picked, key=lambda d: d["pr"]), {"quota": quota, "rejected": rejected}


def fetch_gt(pr: int) -> dict:
    """diff + human-only inline comments + human-only thread/review bodies."""
    diff = gh_text("pr", "diff", str(pr), "--repo", REPO)
    inline_raw = gh_json("api", f"repos/{REPO}/pulls/{pr}/comments", "--paginate")
    inline = [{"author": c["user"]["login"], "body": c.get("body") or "",
               "line": c.get("line") if c.get("line") is not None else c.get("original_line"),
               "path": c.get("path")}
              for c in inline_raw if not is_ai(c.get("user", {}).get("login"))]
    conv_raw = gh_json("api", f"repos/{REPO}/issues/{pr}/comments", "--paginate")
    comments = [{"author": c["user"]["login"], "body": c.get("body") or ""}
                for c in conv_raw if not is_ai(c.get("user", {}).get("login"))]
    rev_raw = gh_json("api", f"repos/{REPO}/pulls/{pr}/reviews", "--paginate")
    reviews = [{"author": r["user"]["login"], "body": r.get("body") or "",
                "state": r.get("state")}
               for r in rev_raw
               if (r.get("body") or "").strip()
               and not is_ai(r.get("user", {}).get("login"))]
    # --jq emits a bare unquoted string, which is not JSON — read it as text
    head = gh_text("api", f"repos/{REPO}/pulls/{pr}", "--jq", ".head.sha").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError(f"pr{pr}: head sha did not resolve to a full SHA: {head!r}")
    return {"diff": diff, "inline": inline,
            "reviews": {"comments": comments, "reviews": reviews},
            "head": head}


def modules_of(diff: str) -> list[str]:
    """Coarse module tags from the touched paths — same vocabulary wave 1 uses."""
    paths = re.findall(r"^\+\+\+ b/(.+)$", diff, re.M)
    mods = set()
    for p in paths:
        parts = p.split("/")
        if p.startswith("docs/"):
            mods.add("docs")
        elif p.startswith("tests/"):
            mods.add("tests")
        elif p.startswith(".buildkite") or p.startswith(".github"):
            mods.add("ci")
        elif p.startswith("benchmarks/"):
            mods.add("benchmarks")
        elif len(parts) > 2 and parts[0] == "vllm_omni":
            mods.add(parts[1])
    return sorted(mods)[:4]


def class_of(title: str) -> str:
    t = title.lower()
    for pat, name in (("bugfix", "bugfix"), ("fix", "bugfix"), ("perf", "perf"),
                      ("feature", "feature"), ("doc", "docs"), ("ci", "ci"),
                      ("misc", "misc"), ("refactor", "refactor"), ("model", "model"),
                      ("rebase", "rebase"), ("quant", "quantization")):
        if pat in t:
            return name
    return "other"


def y(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    dry = "--dry-run" in sys.argv
    import yaml
    ds = yaml.safe_load((HERE / "vllm_omni_dataset.yaml").read_text(encoding="utf-8"))
    wave1 = {int(i["pr"]) for i in ds["pr_review"]}

    print(f"[wave2] building pool: merged >= {MERGED_SINCE}, "
          f">= {MIN_HUMAN_COMMENTS} human inline comments, no self-review, not in wave 1")
    pool = eligible_pool(wave1)
    print(f"[wave2] eligible: {len(pool)}")
    picked, draw_meta = stratified_draw(pool, N_TARGET)
    quota = draw_meta["quota"]
    print(f"[wave2] band quotas: {quota}; range-gate rejections: {[r[chr(39)+'pr'+chr(39)] if False else r['pr'] for r in draw_meta['rejected']]}")
    for p in picked:
        print(f"    #{p['pr']} {p['merged']} {p['band']:>5} files={p['files']:<3} "
              f"human={p['human_inline']:<3} {p['title'][:46]}")
    if dry:
        print("\n[wave2] --dry-run: nothing written")
        return 0

    GT.mkdir(exist_ok=True)
    # idempotent rebuild: strip a previous wave-2 block and its pins so a re-run
    # replaces the block instead of stacking a second one under the same key
    ypath = HERE / "vllm_omni_dataset.yaml"
    text = ypath.read_text(encoding="utf-8")
    marker = "\n# ============================================================\n# wave 2"
    if marker in text:
        prev = yaml.safe_load(text).get("pr_review_wave2") or []
        ypath.write_text(text[:text.index(marker)] + "\n", encoding="utf-8")
        stale = {str(i["pr"]) for i in prev}
        print(f"[wave2] replacing previous block ({len(stale)} items)")
    else:
        stale = set()
    heads = json.loads(HEADS.read_text(encoding="utf-8"))
    for k in stale:
        heads.pop(k, None)
    rows, gt_stats = [], []
    for p in picked:
        n = p["pr"]
        g = fetch_gt(n)
        (GT / f"pr{n}.diff").write_text(g["diff"], encoding="utf-8")
        (GT / f"pr{n}.inline.json").write_text(
            json.dumps(g["inline"], indent=2, ensure_ascii=False), encoding="utf-8")
        (GT / f"pr{n}.reviews.json").write_text(
            json.dumps(g["reviews"], indent=2, ensure_ascii=False), encoding="utf-8")
        heads[str(n)] = g["head"]
        gt_stats.append({"pr": n, "inline": len(g["inline"]),
                         "thread": len(g["reviews"]["comments"]),
                         "review_bodies": len(g["reviews"]["reviews"]),
                         "diff_bytes": len(g["diff"]), "head": g["head"]})
        rows.append((p, g))
        print(f"    gt pr{n}: inline={len(g['inline'])} "
              f"thread={len(g['reviews']['comments'])} diff={len(g['diff'])}B "
              f"head={g['head'][:12]}")

    HEADS.write_text(json.dumps(heads, indent=2) + "\n", encoding="utf-8")

    lines = [
        "",
        "# ============================================================",
        "# wave 2 — 10 recent PRs, ALL frozen holdout (added 2026-08-12)",
        "#",
        "# Wave 1 above is untouched: the 3-arm gpt-5.6 campaign run against it stays a",
        "# valid measurement. These items are a pure holdout — no train, no val — because",
        "# wave 1 already supplies 10 train items while only 5 frozen test items, and the",
        "# frozen set is the half that limits what can be claimed.",
        "#",
        "# Selection (reproducible; see goal-eval/provenance_wave2.json):",
        f"#   eligible = merged >= {MERGED_SINCE}, >= {MIN_HUMAN_COMMENTS} human inline",
        "#              comments, never reviewed by our own vllm-omni-review-bot,",
        "#              not already in wave 1",
        f"#   draw     = seeded stratified sample over changed-file bands, seed",
        f"#              {SEED!r}, proportional to the eligible pool",
        "#",
        "# READ BEFORE COMPARING WAVES:",
        "#   * Wave 2 skews larger and better-reviewed than wave 1 (pool median 8 changed",
        "#     files vs 3; median 6 human inline comments vs 2). Arm-vs-arm WITHIN wave 2",
        "#     is clean; a wave-1-vs-wave-2 delta is confounded by size and is NOT a",
        "#     staleness measurement.",
        "#   * No GOLD latent-gap items: those need history proving human review missed",
        "#     something plus a later PR that fixed it, which recent PRs lack.",
        "#   * Ground truth here is HUMAN-ONLY. Wave 1's GT includes AI reviewers"
        " (chatgpt-codex-",
        "#     connector authors 14% of it and is its most frequent single author; four",
        "#     wave-1 PRs have no human GT at all). Wave 2 filters them out.",
        "pr_review_wave2:",
    ]
    for p, g in rows:
        mods = modules_of(g["diff"])
        lines += [
            f"  - {{pr: {p['pr']}, split: holdout, wave: \"2026-08\", title: {y(p['title'])},",
            f"     author: {p['author']}, merged: {y(p['merged'])}, "
            f"modules: [{', '.join(mods) if mods else 'misc'}],",
            f"     size: {{files: {p['files']}, add: {p['add']}, del: {p['del']}}}, "
            f"review_comments: {len(g['inline'])},",
            f"     class: {class_of(p['title'])}}}",
        ]
    with (HERE / "vllm_omni_dataset.yaml").open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    PROV.write_text(json.dumps({
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "purpose": "wave-2 frozen holdout; wave 1 untouched and still comparable",
        "eligibility": {"merged_since": MERGED_SINCE,
                        "min_human_inline_comments": MIN_HUMAN_COMMENTS,
                        "excludes_self_reviewed": "vllm-omni-review-bot",
                        "range_gate": "merge-base(head,origin/main)..head must yield "
                                      "exactly the declared changed-file count",
                        "excludes_wave1": sorted(wave1)},
        "seed": SEED, "n_target": N_TARGET, "band_quotas": quota,
        "range_gate_rejected": [{"pr": r["pr"], "declared_files": r["files"],
                                 "range_files": r.get("range_files")}
                                for r in draw_meta["rejected"]],
        "eligible_pool_size": len(pool),
        "eligible_pool": pool,
        "selected": [p["pr"] for p, _ in rows],
        "gt": gt_stats,
        "gt_policy": "human-only: chatgpt-codex-connector / copilot-pull-request-reviewer "
                     "/ any *[bot] excluded from inline, thread and review bodies",
        "caveats": [
            "wave 2 skews larger than wave 1; cross-wave deltas are confounded by size",
            "no GOLD latent-gap items (insufficient repo history for recent PRs)",
            "no arm has been run against these items yet",
        ],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n[wave2] wrote {len(rows)} items, {len(rows)*3} gt artifacts, "
          f"{len(rows)} head pins")
    print(f"[wave2] provenance -> {PROV.relative_to(HERE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
