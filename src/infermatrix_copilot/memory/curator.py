"""Debug-memory curator — repo-neutral port of the parent rebase agent's
`agent/curator.py` (design D5; Rev 8 §5).

Same rule-based passes as the parent — merge/near-dup consolidation (greedy
single-link clustering per module, Jaccard over key+symptom+root_cause
tokens), staleness by upstream commit distance, dormancy, and pattern
extraction into skill CANDIDATES (never auto-written skills) — with the
recorded divergences:

* **Retire, never delete.** The parent hard-deleted merged-away rows; here
  they become `status='retired'` with `derived_from` = the survivor's id.
  Retired rows are excluded from every curator input AND from search, so a
  second curation over an already-curated store is a strict no-op.
* **Repo-scoped.** The copilot store is shared across repos; every read and
  mutation filters `repo == <target>` — foreign rows are untouched.
* **Dormancy maps to `stale`** (the copilot has no 'inactive' status);
  like the parent, dormancy is judged against a recent-run window and only
  when a window is supplied.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

from .debug_memory import DebugMemory
from .skills import SkillStore

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on",
    "for", "and", "or", "not", "no", "it", "this", "that", "with", "from",
    "by", "at", "error", "fix", "fixed", "failure", "failed", "test",
    "tests", "module",
}
_TOKEN_RE = re.compile(r"[a-z0-9_]+")

# parent-verbatim non-actionable filters: "module needed no changes" rows
# dominate the store and make useless skill candidates
_NON_ACTIONABLE_PATTERNS = [
    r"already\s+compatible",
    r"no\s+(code\s+)?changes?\s+(needed|required|made)",
    r"no\s+change\s+(needed|required)",
    r"no\s+fix\s+(needed|required)",
    r"noop",
    r"fully\s+compatible",
    r"nothing\s+to\s+(rebase|change|fix)",
    r"known\s+upstream\s+bug",
    r"pre-existing\s+(upstream\s+)?(bug|failure|defect)",
    r"not\s+a\s+rebase\s+regression",
    r"known/expected\s+baseline\s+failure",
    r"verification[-\s]?only",
]
_NON_ACTIONABLE_TAGS = {
    "already-compatible", "clean", "clean-rebase", "compatible",
    "known-upstream-bug", "no-change", "no-change-needed", "no-changes",
    "no-code-changes", "no-fix-needed", "noop", "pre-existing-failures",
    "rebase-success", "verification-only",
}
_EXISTING_SKILL_COVERAGE_THRESHOLD = 0.45


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall((text or "").lower())
            if len(t) > 2 and t not in _STOPWORDS}


def _signature(entry: dict) -> set[str]:
    return _tokens(f"{entry.get('key', '')} {entry.get('symptom', '')} "
                   f"{entry.get('root_cause', '')}")


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def _tags_of(entry: dict) -> list[str]:
    raw = entry.get("tags") or ""
    return [t.strip() for t in str(raw).split(",") if t.strip()]


def _non_actionable(entry: dict) -> bool:
    if set(t.lower() for t in _tags_of(entry)) & _NON_ACTIONABLE_TAGS:
        return True
    combined = " ".join(str(entry.get(f, "")).lower() for f in (
        "key", "symptom", "root_cause", "fix_summary", "watch_outs",
        "tags"))
    return any(re.search(p, combined) for p in _NON_ACTIONABLE_PATTERNS)


@dataclass
class SkillCandidate:
    module: str
    key: str
    occurrences: int
    trigger: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class CuratorReport:
    merged: int = 0
    stale: int = 0
    dormant: int = 0
    candidates: list[SkillCandidate] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"merged": self.merged, "stale": self.stale,
                "dormant": self.dormant,
                "candidates": [c.__dict__ for c in self.candidates],
                "actions": self.actions}


class DebugMemoryCurator:
    """One curation pass over the copilot store, repo-scoped."""

    def __init__(self, dm: DebugMemory, *, repo: str,
                 sim_threshold: float = 0.82,
                 pattern_threshold: float = 0.6,
                 min_pattern_occurrences: int = 2,
                 dormant_window: int = 12,
                 stale_commit_distance: int = 5000,
                 upstream_path: str = "",
                 current_upstream_commit: str = "",
                 skill_layers: tuple = (),
                 propose_to: SkillStore | None = None,
                 survivor_key=None):
        if not dm.schema_v2:
            raise RuntimeError(
                "curation requires the v2 schema — run ensure_schema_v2() "
                "first (sanctioned maintenance entry points only)")
        self.dm = dm
        self.repo = repo
        self.sim_threshold = sim_threshold
        self.pattern_threshold = pattern_threshold
        self.min_pattern_occurrences = min_pattern_occurrences
        self.dormant_window = dormant_window
        self.stale_commit_distance = stale_commit_distance
        self.upstream_path = upstream_path
        self.current_upstream_commit = current_upstream_commit
        self.skill_layers = tuple(skill_layers)
        self.propose_to = propose_to
        # merge-survivor order: default = newest id (parent parity);
        # migration passes a source-precedence rank so a newly imported
        # lower-priority parent/adapter row can never retire
        # higher-priority runtime knowledge (PR-boundary F11). The
        # callable maps an entry dict to a sort key; LOWEST wins.
        self.survivor_key = survivor_key or \
            (lambda e: (-int(e["id"]),))

    # ── entry point ─────────────────────────────────────────────────────
    def curate(self, recent_runs: list[str] | None = None) -> CuratorReport:
        report = CuratorReport()
        updates: dict[int, dict] = {}
        self._merge_duplicates(report, updates)
        self._detect_stale(report, updates)
        self._detect_dormant(report, updates, recent_runs or [])
        self.dm.apply_curation(updates)
        report.candidates = self._extract_patterns(report)
        return report

    def _entries(self) -> list[dict]:
        return self.dm.entries(repo=self.repo)

    # ── 1. merge (retire-never-delete) ──────────────────────────────────
    def _merge_duplicates(self, report: CuratorReport,
                          updates: dict[int, dict]) -> None:
        for group in self._cluster(self._entries(), self.sim_threshold):
            if len(group) < 2:
                continue
            group.sort(key=self.survivor_key)
            rep, others = group[0], group[1:]
            tags = _tags_of(rep)
            files = list(rep.get("files") or [])
            run_count = int(rep.get("run_count") or 1)
            last_seen = str(rep.get("last_seen_run") or "")
            for e in others:
                for t in _tags_of(e):
                    if t not in tags:
                        tags.append(t)
                for f in e.get("files") or []:
                    if f not in files:
                        files.append(f)
                run_count += int(e.get("run_count") or 1)
                if str(e.get("last_seen_run") or "") > last_seen:
                    last_seen = str(e.get("last_seen_run") or "")
                # retire with lineage — derived_from is immutable once set
                updates[e["id"]] = {"status": "retired",
                                    "derived_from": str(rep["id"])}
            updates[rep["id"]] = {"tags": ",".join(tags), "files": files,
                                  "run_count": run_count,
                                  "last_seen_run": last_seen}
            report.merged += len(others)
            report.actions.append(
                f"MERGED: {len(group)} entries -> '{rep.get('key', '')}' "
                f"(module={rep.get('module', '')}, run_count={run_count})")

    def _cluster(self, entries: list[dict],
                 threshold: float) -> list[list[dict]]:
        """Greedy single-link clustering per module (parent-verbatim
        mechanics; deterministic — entries arrive ordered by id)."""
        clusters: list[list[dict]] = []
        sigs: list[set[str]] = []
        for e in entries:
            sig = _signature(e)
            placed = False
            for idx, cluster in enumerate(clusters):
                if cluster[0].get("module") != e.get("module"):
                    continue
                if _jaccard(sig, sigs[idx]) >= threshold:
                    cluster.append(e)
                    sigs[idx] |= sig
                    placed = True
                    break
            if not placed:
                clusters.append([e])
                sigs.append(set(sig))
        return clusters

    # ── 2. stale (upstream moved on) ────────────────────────────────────
    def _detect_stale(self, report: CuratorReport,
                      updates: dict[int, dict]) -> None:
        if not (self.upstream_path and self.current_upstream_commit):
            return
        for e in self._entries():
            if e["id"] in updates and updates[e["id"]].get("status"):
                continue
            commit = str(e.get("upstream_commit") or "")
            if not commit:
                continue
            distance = self._commit_distance(commit,
                                             self.current_upstream_commit)
            if distance is not None and distance > self.stale_commit_distance:
                updates.setdefault(e["id"], {})["status"] = "stale"
                report.stale += 1
                report.actions.append(
                    f"STALE: '{e.get('key', '')}' (module="
                    f"{e.get('module', '')}, {distance} commits behind)")

    def _commit_distance(self, old: str, new: str) -> int | None:
        try:
            anc = subprocess.run(
                ["git", "merge-base", "--is-ancestor", old, new],
                cwd=self.upstream_path, capture_output=True, timeout=10)
            if anc.returncode != 0:
                return None  # diverged/unknown -> never tag (parent parity)
            out = subprocess.run(
                ["git", "rev-list", "--count", f"{old}..{new}"],
                cwd=self.upstream_path, capture_output=True, text=True,
                timeout=10)
            return int(out.stdout.strip()) \
                if out.returncode == 0 and out.stdout.strip() else None
        except (subprocess.SubprocessError, ValueError, OSError):
            return None

    # ── 3. dormancy -> stale ────────────────────────────────────────────
    def _detect_dormant(self, report: CuratorReport,
                        updates: dict[int, dict],
                        recent_runs: list[str]) -> None:
        if not recent_runs:
            return
        window = set(recent_runs[-self.dormant_window:])
        for e in self._entries():
            if str(e.get("status")) != "active":
                continue
            if e["id"] in updates and updates[e["id"]].get("status"):
                continue
            # MIGRATED rows carry run ids from a FOREIGN id space (the
            # parent's), which can never appear in the copilot's run
            # window — dormancy would mark every freshly migrated fact
            # stale on the first curate (PR-boundary F12). Source-aware
            # rule: migrated rows are exempt from the dormancy clock
            # (staleness still applies via upstream-commit distance,
            # which IS meaningful for them).
            source_tag = str(e.get("source") or "").split("#", 1)[0]
            if source_tag in ("parent-db", "copilot-global",
                              "adapter-tree"):
                continue
            seen = str(e.get("last_seen_run") or e.get("run_id") or "")
            if seen and seen not in window:
                updates.setdefault(e["id"], {})["status"] = "stale"
                report.dormant += 1
                report.actions.append(
                    f"DORMANT->stale: '{e.get('key', '')}' (module="
                    f"{e.get('module', '')}, last_seen={seen})")

    # ── 4. pattern extraction -> skill candidates ───────────────────────
    def _extract_patterns(self, report: CuratorReport) -> list[SkillCandidate]:
        entries = [e for e in self._entries()
                   if str(e.get("status")) == "active"
                   and not _non_actionable(e)]
        existing = self._existing_skill_signatures()
        candidates: list[SkillCandidate] = []
        for cluster in self._cluster(entries, self.pattern_threshold):
            occurrences = sum(int(e.get("run_count") or 1) for e in cluster)
            if occurrences < self.min_pattern_occurrences:
                continue
            cluster.sort(key=lambda e: e["id"], reverse=True)
            rep = cluster[0]
            if self._covered(rep, existing):
                continue
            trigger_lines = (str(rep.get("symptom") or
                                 rep.get("root_cause") or "")
                             .strip().splitlines()[0:1])
            cand = SkillCandidate(
                module=str(rep.get("module", "")),
                key=str(rep.get("key", "")),
                occurrences=occurrences,
                trigger=trigger_lines[0][:200] if trigger_lines else "",
                sources=sorted({str(e.get("key", "")) for e in cluster}))
            candidates.append(cand)
            report.actions.append(
                f"SKILL-CANDIDATE: '{cand.key}' (module={cand.module}, "
                f"{occurrences}x, {len(cluster)} entries)")
            if self.propose_to is not None:
                # identity (module+key) decides, never prose; the whole
                # check-allocate-write is ONE critical section inside the
                # store's candidates flock, so concurrent curators can
                # neither re-propose one identity nor overwrite each
                # other's colliding names
                identity = f"{cand.module}\0{cand.key}"
                base = re.sub(r"[^a-z0-9]+", "-",
                              f"{cand.module} {cand.key}".lower()
                              ).strip("-") or f"pattern-{rep['id']}"
                written = self.propose_to.propose_if_new_identity(
                    base_name=base, identity=identity,
                    description=cand.trigger or cand.key,
                    body=(f"## Pattern ({occurrences}x)\n\n"
                          f"Symptom: {rep.get('symptom', '')}\n\n"
                          f"Root cause: {rep.get('root_cause', '')}\n\n"
                          f"Fix: {rep.get('fix_summary', '')}\n\n"
                          f"Sources: {', '.join(cand.sources)}\n"),
                    modules=[cand.module] if cand.module else [])
                if written is None:
                    report.actions.append(
                        f"CANDIDATE-PENDING: identity '{cand.module}/"
                        f"{cand.key}' already proposed (or name refused) "
                        "— not re-proposed")
        return candidates

    def _existing_skill_signatures(self) -> list[tuple[set[str], set[str]]]:
        signatures = []
        for store in self.skill_layers:
            try:
                skills = store.load_all()
            except Exception:  # noqa: BLE001 — optional during curation
                continue
            for s in skills:
                signatures.append((
                    {str(m).strip() for m in s.modules if str(m).strip()},
                    _tokens(f"{s.name} {s.description} {s.trigger} "
                            f"{s.body}")))
        return signatures

    def _covered(self, entry: dict, existing) -> bool:
        sig = _tokens(f"{entry.get('key', '')} {entry.get('symptom', '')} "
                      f"{entry.get('root_cause', '')} "
                      f"{entry.get('tags', '')}")
        if not sig:
            return False
        for modules, skill_sig in existing:
            if modules and entry.get("module") not in modules:
                continue
            overlap = len(sig & skill_sig) / len(sig)
            if (_jaccard(sig, skill_sig) >= self.pattern_threshold
                    or overlap >= _EXISTING_SKILL_COVERAGE_THRESHOLD):
                return True
        return False
