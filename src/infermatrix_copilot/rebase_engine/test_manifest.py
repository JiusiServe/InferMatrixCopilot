"""Dynamic test-manifest builder — port of the parent's `test_manifest.py`.

Each run builds the manifest fresh from: the CI provider's YAML files
(authoritative job definitions), the live test tree (existence + rename-aware
path correction), `git diff origin/main` (change classification), and the
module test map. Drives phase-2 prompt injection and phase-3 execution.

Repo specifics arrive as `ManifestSpec` (adapter data): queue→GPU map, label
skip patterns, pipeline filenames, rename-suffix families, file-ref prefixes,
the module maps, and the change→module path rules. NOTE on map flavors
(DRIFT_TRIAGE #6): the parent kept its OWN inline module map here for
job→module ROUTING, distinct from the §11 operational test map — merging
them changes routing scores, so this port keeps both as separate adapter
data: `assignment_paths` (routing, parent inline flavor) and
`modules.*.test_paths` (§11, shell test selection). The prompt flavor is a
third, deliberate dataset (`prompt_data.yaml`).
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import yaml

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ManifestSpec:
    """Adapter data for manifest building (parent constants, externalized)."""

    yaml_dir: str                                  # e.g. ".buildkite"
    pipelines: Mapping[str, str]                   # filename -> source tag
    queue_map: Mapping[str, Sequence]              # queue -> (min_gpus, hw)
    skip_patterns: Sequence[str] = ()
    rename_suffixes: Sequence[str] = ()            # longest-first
    file_ref_prefixes: Sequence[str] = ("tests",)  # cmd path-ref roots
    file_tree_roots: Sequence[str] = ("tests",)    # path-correction scan roots
    module_test_paths: Mapping[str, Sequence[str]] = field(default_factory=dict)
    # job→module ROUTING patterns — the parent's test_manifest.py inline map,
    # a DISTINCT flavor from §11 MODULE_TEST_MAP (shell test selection):
    # scoring over a different pattern set produces different winners, so
    # assignment must use the parent's own map verbatim (DRIFT_TRIAGE #6).
    # Empty ⇒ fall back to module_test_paths (repo-neutral default).
    assignment_paths: Mapping[str, Sequence[str]] = field(default_factory=dict)
    # ordered [substring, module] rules classifying CHANGE paths
    change_path_rules: Sequence[Sequence[str]] = ()
    default_queue: str = ""
    priority_source: str = "ready"                 # slug-collision winner
    # slug -> setup command (parent CI_TEST_SETUP: pre-run model downloads;
    # feeds the runner's model-download notification hook)
    setup_map: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_manifest(cls, manifest: Mapping) -> "ManifestSpec":
        rb = (manifest.get("rebase") or {})
        tm = rb.get("test_manifest") or {}
        modules = manifest.get("modules") or {}
        return cls(
            yaml_dir=tm["yaml_dir"],
            pipelines=dict(tm["pipelines"]),
            queue_map={k: tuple(v) for k, v in (tm.get("queue_map") or {}).items()},
            skip_patterns=tuple(tm.get("skip_patterns") or ()),
            rename_suffixes=tuple(tm.get("rename_suffixes") or ()),
            file_ref_prefixes=tuple(tm.get("file_ref_prefixes") or ("tests",)),
            file_tree_roots=tuple(tm.get("file_tree_roots") or ("tests",)),
            module_test_paths={m: tuple((spec or {}).get("test_paths") or ())
                               for m, spec in modules.items()},
            assignment_paths={m: tuple(v or ())
                              for m, v in (tm.get("assignment_paths")
                                           or {}).items()},
            change_path_rules=tuple(tuple(r) for r in
                                    (tm.get("change_path_rules") or ())),
            default_queue=tm.get("default_queue", ""),
            priority_source=tm.get("priority_source", "ready"),
            setup_map=dict(tm.get("setup_map") or {}),
        )


@dataclass
class ManifestJob:
    slug: str
    label: str
    source: str
    command: str
    timeout_sec: int
    min_gpus: int
    hw: str
    env: str
    module: str = ""
    setup: str = ""                # parent CI_TEST_SETUP[slug], adapter data
    file_refs: list[str] = field(default_factory=list)


@dataclass
class TestChange:
    __test__ = False
    path: str
    change_type: str       # added | deleted | renamed | modified
    new_path: str = ""


@dataclass
class ModuleTestPlan:
    module: str
    ci_tests: list[ManifestJob] = field(default_factory=list)
    upstream_changes: list[TestChange] = field(default_factory=list)
    omni_specific_tests: list[str] = field(default_factory=list)


@dataclass
class BuiltManifest:
    jobs: list[ManifestJob]
    changes: list[TestChange]
    module_plans: dict[str, ModuleTestPlan]
    # labels of LABELED steps that carried no runnable command — surfaced,
    # never silent (the run side classifies each as a structural failure)
    dropped: list[str] = field(default_factory=list)

    def for_module(self, module: str) -> ModuleTestPlan:
        return self.module_plans.get(module, ModuleTestPlan(module=module))

    def to_dict(self) -> dict:
        return {
            "jobs": [{"slug": j.slug, "label": j.label, "source": j.source,
                      "command": j.command, "timeout_sec": j.timeout_sec,
                      "min_gpus": j.min_gpus, "hw": j.hw, "env": j.env,
                      "module": j.module, "setup": j.setup}
                     for j in self.jobs],
            "changes": [{"path": c.path, "type": c.change_type,
                         "new_path": c.new_path} for c in self.changes],
            "dropped": list(self.dropped),
            "module_plans": {
                m: {"ci_tests": [j.slug for j in p.ci_tests],
                    "upstream_changes": [
                        {"path": c.path, "type": c.change_type,
                         "new_path": c.new_path}
                        for c in p.upstream_changes],
                    "omni_specific": p.omni_specific_tests}
                for m, p in self.module_plans.items()},
        }


def _should_skip(label: str, patterns: Sequence[str]) -> bool:
    return any(re.search(p, label) for p in patterns)


def _label_to_slug(label: str) -> str:
    s = label.lower().strip()
    s = re.sub(r"[^a-z0-9\s_-]", "", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _parse_k8s_gpu_count(step: dict, fallback: int) -> int:
    """`nvidia.com/gpu` from a Kubernetes pod spec beats the queue map's
    rough guess (parent-documented)."""
    plugins = step.get("plugins", [])
    if not isinstance(plugins, list):
        return fallback
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        k8s = plugin.get("kubernetes", {})
        if not isinstance(k8s, dict):
            continue
        containers = (k8s.get("podSpec", {}) or {}).get("containers", [])
        if not isinstance(containers, list):
            continue
        for c in containers:
            if not isinstance(c, dict):
                continue
            gpu = (c.get("resources", {}) or {}).get("limits", {}) \
                .get("nvidia.com/gpu")
            if gpu is not None:
                try:
                    return max(fallback, int(gpu))
                except (ValueError, TypeError):
                    pass
    return fallback


# a PURE export line assigns env and nothing else — a compound line like
# `export X=1 && pytest ...` is a COMMAND and must never be stripped (or a
# job could silently lose its entire body to the env split). The grammar
# covers the valid setup-only forms bash accepts: multiple assignments per
# export (`export A=1 B=2`), chained exports (`export A=1; export B=2`), a
# trailing `;`, and a trailing comment (whitespace-separated — a glued
# `A=1#x` is a VALUE in bash, not a comment). Extraction shares the same
# grammar (`export\tA=1` yields the clean token `A=1`).
_ASSIGN = r"[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|[^\s;]*)"
_EXPORT_GROUP = rf"export\s+{_ASSIGN}(?:\s+{_ASSIGN})*"
_PURE_EXPORT_RX = re.compile(
    rf"^\s*{_EXPORT_GROUP}(?:\s*;\s*{_EXPORT_GROUP})*\s*;?(?:\s+#.*)?\s*$")
_ASSIGN_RX = re.compile(_ASSIGN)
_EXPORT_SKIP_RX = re.compile(r"\s+|;|export\b")
# a bare shell-option line (`set -e`, `set +o xtrace`, `set -euo pipefail`)
# configures the shell and runs nothing — setup-only, like a pure export.
# Tokens are flag/option WORDS only: `$`, quotes, and backticks are excluded
# so `set $(cmd)` (which executes cmd) can never be classified as a no-op.
# The FULL setup-line grammar chains export and set groups with `;`, allows
# a trailing `;`, and a whitespace-separated trailing comment — mirroring
# the export grammar, so `set -euo pipefail # strict`,
# `set -e; set -o pipefail`, and `set -e; export A=1` are all recognized
# as running no test.
_SET_TOKEN = r"[+-]?[A-Za-z_][A-Za-z0-9_-]*"
_SET_GROUP = rf"set\s+{_SET_TOKEN}(?:\s+{_SET_TOKEN})*"
_SETUP_GROUP = rf"(?:{_EXPORT_GROUP}|{_SET_GROUP})"
_PURE_SETUP_RX = re.compile(
    rf"^\s*{_SETUP_GROUP}(?:\s*;\s*{_SETUP_GROUP})*\s*;?(?:\s+#.*)?\s*$")


def _export_tokens(line: str) -> list[str]:
    """The K=V tokens of a line that matched `_PURE_EXPORT_RX`, scanned
    LEFT-TO-RIGHT with the same quote-aware grammar — a `#` inside a
    quoted value stays part of the value (`export NOTE='foo # bar'`),
    while a `#` at a token boundary starts the comment and nothing after
    it (e.g. `# B=2 note`) can masquerade as env."""
    tokens: list[str] = []
    pos = 0
    while pos < len(line):
        skip = _EXPORT_SKIP_RX.match(line, pos)
        if skip:
            pos = skip.end()
            continue
        if line[pos] == "#":
            break
        m = _ASSIGN_RX.match(line, pos)
        if not m:       # unreachable after a _PURE_EXPORT_RX match
            break
        tokens.append(m.group(0))
        pos = m.end()
    return tokens


def is_runnable_command(text: str) -> bool:
    """True when `text` contains at least one line that would actually DO
    something in bash. Blank lines, comment lines, pure-export lines, and
    bare `set` option lines are all rc=0 no-ops whose exit would read as a
    pass — the §10 false-pass class (`# pytest temporarily disabled`, a
    wrapper-unwrapped `export A=1`, or `set -e` must never count as a
    runnable job)."""
    for ln in (text or "").split("\n"):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if _PURE_SETUP_RX.match(ln):
            continue
        return True
    return False


def _format_env_pairs(env_map: Mapping) -> str:
    """A pipeline-level `env:` mapping as shell-safe "K=V" tokens (the same
    encoding job-level `export` lines produce) — values with spaces stay a
    single token for the downstream shlex parse."""
    import shlex as _shlex
    return " ".join(_shlex.quote(f"{k}={v}")
                    for k, v in env_map.items()
                    if isinstance(k, str) and k)


def _extract_steps(steps_list: list, source: str,
                   spec: ManifestSpec,
                   pipeline_env: str = "",
                   dropped: list | None = None) -> list[ManifestJob]:
    jobs: list[ManifestJob] = []
    ref_rx = re.compile(
        r"(?:%s)/[\w/_.*-]+" % "|".join(re.escape(p)
                                        for p in spec.file_ref_prefixes))
    for step in steps_list:
        if not isinstance(step, dict):
            continue
        if "group" in step and "steps" in step:
            jobs.extend(_extract_steps(step["steps"], source, spec,
                                       pipeline_env, dropped))
            continue
        label = step.get("label", "")
        if not label or _should_skip(label, spec.skip_patterns):
            continue
        # Buildkite accepts both `commands:` (list) and `command:`
        # (string or list) — the parent read only the plural form and
        # silently produced empty jobs for the singular one
        cmds = step.get("commands", step.get("command", []))
        if isinstance(cmds, list):
            cmd = "\n".join(c for c in cmds
                            if isinstance(c, str) and c.strip())
        else:
            cmd = str(cmds or "")
        export_matches = [_PURE_EXPORT_RX.match(ln)
                          for ln in cmd.split("\n")]
        env_tokens: list[str] = []
        for ln, m in zip(cmd.split("\n"), export_matches):
            if m:
                env_tokens.extend(_export_tokens(ln))
        cmd_clean = "\n".join(ln for ln, m in zip(cmd.split("\n"),
                                                  export_matches) if not m)

        cmd_normalized = cmd_clean
        m = re.match(r"^timeout\s+\d+m\s+bash\s+-c\s*['\"](.*)['\"]\s*$",
                     cmd_clean.strip(), re.DOTALL)
        if m:
            inner = re.sub(r"^\s*set\s+[+-]?\w+(?:\s+[+-]?\w+)*\s*;?\s*\n",
                           "", m.group(1).strip()).strip()
            # unconditional: an EMPTY body must not resurrect the wrapper
            # text as a "runnable" command (`timeout 20m bash -c ""` is a
            # no-op test — fix over the parent, which kept the wrapper)
            cmd_normalized = inner

        # runnability is judged on the NORMALIZED command — a wrapper like
        # `timeout 20m bash -c "# disabled"` reduces to a comment-only body
        # and must be dropped here (a GPU-ineligible job would be skipped
        # before the run-side guard could classify it structural)
        if not is_runnable_command(cmd_normalized):
            # a labeled step with no RUNNABLE command (empty, export-only,
            # or comment-only — bash treats comments as rc=0 no-ops) is NOT
            # a test job: emitting it would read as a pass (the parent's
            # §10 false-pass mechanism, DRIFT_TRIAGE #4). NEVER silent: the
            # drop is surfaced through BuiltManifest.dropped and classified
            # structural by the run side, so the push gate cannot pass over
            # an omitted test
            if dropped is not None:
                dropped.append(label)
            continue
        timeout_min = step.get("timeout_in_minutes", 30)
        agents = step.get("agents", {}) or {}
        queue = agents.get("queue", spec.default_queue)
        min_gpus, hw = spec.queue_map.get(queue, (1, "any"))
        min_gpus = _parse_k8s_gpu_count(step, min_gpus)
        env_vars = " ".join(env_tokens)
        if pipeline_env:
            # top-level pipeline env FIRST so a job's own export wins the
            # later last-key-wins parse — the live pipelines declare shared
            # runtime settings there, and dropping them would run local
            # jobs outside their authoritative CI environment
            env_vars = f"{pipeline_env} {env_vars}".strip()

        refs = []
        for ref in ref_rx.finditer(cmd_normalized):
            rp = ref.group(0).rstrip("'\"\\; ")
            if "*" not in rp:
                refs.append(rp)
        slug = _label_to_slug(label)
        jobs.append(ManifestJob(
            slug=slug, label=label, source=source,
            command=cmd_normalized, timeout_sec=timeout_min * 60,
            min_gpus=min_gpus, hw=hw, env=env_vars,
            setup=spec.setup_map.get(slug, ""), file_refs=refs))
    return jobs


def _parse_ci_yaml(repo: Path, spec: ManifestSpec,
                   dropped: list | None = None) -> list[ManifestJob]:
    all_jobs: dict[str, ManifestJob] = {}
    yaml_dir = repo / spec.yaml_dir
    for yaml_file, source in spec.pipelines.items():
        path = yaml_dir / yaml_file
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not data or "steps" not in data:
            continue
        top_env = data.get("env")
        pipeline_env = _format_env_pairs(top_env) \
            if isinstance(top_env, dict) else ""
        for job in _extract_steps(data["steps"], source, spec,
                                  pipeline_env, dropped):
            if job.slug not in all_jobs or source == spec.priority_source:
                all_jobs[job.slug] = job
    return list(all_jobs.values())


def _classify_test_changes(repo: Path) -> list[TestChange]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-status", "origin/main",
             "--", "tests/"], capture_output=True, text=True, timeout=30)
    except Exception:  # noqa: BLE001 - parent parity: best-effort
        return []
    changes: list[TestChange] = []
    for line in proc.stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("A"):
            changes.append(TestChange(path=parts[1], change_type="added"))
        elif status.startswith("D"):
            changes.append(TestChange(path=parts[1], change_type="deleted"))
        elif status.startswith("M"):
            changes.append(TestChange(path=parts[1], change_type="modified"))
        elif status.startswith("R"):
            changes.append(TestChange(
                path=parts[1], change_type="renamed",
                new_path=parts[2] if len(parts) > 2 else ""))
    return changes


def _canonical_stem(stem: str, suffixes: Sequence[str]) -> str:
    for suf in suffixes:
        if stem.endswith(suf) and len(stem) > len(suf):
            return stem[: -len(suf)]
    return stem


def _validate_file_paths(jobs: list[ManifestJob], repo: Path,
                         spec: ManifestSpec,
                         rename_map: Mapping[str, str]) -> None:
    """Auto-correct stale test paths, decreasing confidence: unique basename
    (a move), the authoritative git rename map, then canonical-stem family
    (a rename like test_x.py → test_x_expansion.py), same-directory first.
    Stale paths used to fail collection with pytest rc=4."""
    index: dict[str, list[str]] = {}
    all_files: list[str] = []
    for root in spec.file_tree_roots:
        base = repo / root
        if not base.is_dir():
            continue
        for dp, _, fnames in os.walk(str(base)):
            for fn in fnames:
                if fn.endswith(".py"):
                    rel = str((Path(dp) / fn).relative_to(repo))
                    index.setdefault(fn, []).append(rel)
                    all_files.append(rel)

    def resolve(ref: str) -> str | None:
        candidates = index.get(Path(ref).name, [])
        if len(candidates) == 1:
            return candidates[0]
        new = rename_map.get(ref)
        if new and (repo / new).exists():
            return new
        miss_canon = _canonical_stem(Path(ref).stem, spec.rename_suffixes)
        miss_dir = str(Path(ref).parent)
        fam = [f for f in all_files if f != ref and
               _canonical_stem(Path(f).stem, spec.rename_suffixes) == miss_canon]
        in_dir = [f for f in fam if str(Path(f).parent) == miss_dir]
        for pool in (in_dir, fam):
            uniq = sorted(set(pool))
            if len(uniq) == 1:
                return uniq[0]
        return None

    for job in jobs:
        for i, ref in enumerate(list(job.file_refs)):
            if (repo / ref).exists():
                continue
            fixed = resolve(ref)
            if fixed and fixed != ref:
                job.command = job.command.replace(ref, fixed)
                job.file_refs[i] = fixed
                log.info("  [%s] path corrected: %s -> %s",
                         job.slug, ref, fixed)


def _assign_modules(jobs: list[ManifestJob], spec: ManifestSpec) -> None:
    routing = spec.assignment_paths or spec.module_test_paths
    for job in jobs:
        best_module, best_score = "", 0
        for module, patterns in routing.items():
            score = 0
            for ref in job.file_refs:
                for pat in patterns:
                    if pat.endswith("/"):
                        if ref.startswith(pat):
                            score += 2
                    elif pat in ref or ref.startswith(pat):
                        score += 1
            if score > best_score:
                best_score, best_module = score, module
        job.module = best_module


def _build_module_plans(jobs: list[ManifestJob], changes: list[TestChange],
                        spec: ManifestSpec) -> dict[str, ModuleTestPlan]:
    plans: dict[str, ModuleTestPlan] = {}
    for job in jobs:
        mod = job.module or "unknown"
        plans.setdefault(mod, ModuleTestPlan(module=mod)).ci_tests.append(job)
    for change in changes:
        path = change.new_path or change.path
        mod = "unknown"
        for needle, module in spec.change_path_rules:
            if needle in path:
                mod = module
                break
        plans.setdefault(mod, ModuleTestPlan(module=mod)) \
            .upstream_changes.append(change)
    for m in spec.module_test_paths:
        plans.setdefault(m, ModuleTestPlan(module=m))
    return plans


def build_manifest(repo: Path, spec: ManifestSpec) -> BuiltManifest:
    """The parent's `TestManifest.build` sequence: parse CI YAML → classify
    changes → rename-aware path validation → module assignment → plans."""
    repo = Path(repo)
    dropped: list[str] = []
    jobs = _parse_ci_yaml(repo, spec, dropped)
    changes = _classify_test_changes(repo)
    rename_map = {c.path: c.new_path for c in changes
                  if c.change_type == "renamed" and c.new_path}
    _validate_file_paths(jobs, repo, spec, rename_map)
    _assign_modules(jobs, spec)
    plans = _build_module_plans(jobs, changes, spec)
    return BuiltManifest(jobs=jobs, changes=changes, module_plans=plans,
                         dropped=dropped)
