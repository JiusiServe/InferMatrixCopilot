"""Dynamic test-manifest builder — port of the parent's `test_manifest.py`.

Each run builds the manifest fresh from: the CI provider's YAML files
(authoritative job definitions), the live test tree (existence + rename-aware
path correction), `git diff origin/main` (change classification), and the
module test map. Drives phase-2 prompt injection and phase-3 execution.

Repo specifics arrive as `ManifestSpec` (adapter data): queue→GPU map, label
skip patterns, pipeline filenames, rename-suffix families, file-ref prefixes,
the module test map, and the change→module path rules. NOTE the parent kept a
THIRD inline copy of the module test map here; this port reads the
MANIFEST's operational map instead — recorded in DRIFT_TRIAGE (the prompt
flavor is a separate, deliberate dataset).
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
    # ordered [substring, module] rules classifying CHANGE paths
    change_path_rules: Sequence[Sequence[str]] = ()
    default_queue: str = ""
    priority_source: str = "ready"                 # slug-collision winner

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
            change_path_rules=tuple(tuple(r) for r in
                                    (tm.get("change_path_rules") or ())),
            default_queue=tm.get("default_queue", ""),
            priority_source=tm.get("priority_source", "ready"),
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

    def for_module(self, module: str) -> ModuleTestPlan:
        return self.module_plans.get(module, ModuleTestPlan(module=module))

    def to_dict(self) -> dict:
        return {
            "jobs": [{"slug": j.slug, "label": j.label, "source": j.source,
                      "command": j.command, "timeout_sec": j.timeout_sec,
                      "min_gpus": j.min_gpus, "hw": j.hw, "env": j.env,
                      "module": j.module} for j in self.jobs],
            "changes": [{"path": c.path, "type": c.change_type,
                         "new_path": c.new_path} for c in self.changes],
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


def _extract_steps(steps_list: list, source: str,
                   spec: ManifestSpec) -> list[ManifestJob]:
    jobs: list[ManifestJob] = []
    ref_rx = re.compile(
        r"(?:%s)/[\w/_.*-]+" % "|".join(re.escape(p)
                                        for p in spec.file_ref_prefixes))
    for step in steps_list:
        if not isinstance(step, dict):
            continue
        if "group" in step and "steps" in step:
            jobs.extend(_extract_steps(step["steps"], source, spec))
            continue
        label = step.get("label", "")
        if not label or _should_skip(label, spec.skip_patterns):
            continue
        cmds = step.get("commands", [])
        if isinstance(cmds, list):
            cmd = "\n".join(c for c in cmds
                            if isinstance(c, str) and c.strip())
        else:
            cmd = str(cmds or "")
        env_lines = [ln for ln in cmd.split("\n")
                     if ln.strip().startswith("export ")]
        cmd_clean = "\n".join(ln for ln in cmd.split("\n")
                              if not ln.strip().startswith("export "))
        timeout_min = step.get("timeout_in_minutes", 30)
        agents = step.get("agents", {}) or {}
        queue = agents.get("queue", spec.default_queue)
        min_gpus, hw = spec.queue_map.get(queue, (1, "any"))
        min_gpus = _parse_k8s_gpu_count(step, min_gpus)
        env_vars = " ".join(ln.replace("export ", "").strip()
                            for ln in env_lines)

        cmd_normalized = cmd_clean
        m = re.match(r"^timeout\s+\d+m\s+bash\s+-c\s*['\"](.*)['\"]\s*$",
                     cmd_clean.strip(), re.DOTALL)
        if m:
            inner = re.sub(r"^\s*set\s+[+-]?\w+(?:\s+[+-]?\w+)*\s*;?\s*\n",
                           "", m.group(1).strip()).strip()
            if inner:
                cmd_normalized = inner

        refs = []
        for ref in ref_rx.finditer(cmd_normalized):
            rp = ref.group(0).rstrip("'\"\\; ")
            if "*" not in rp:
                refs.append(rp)
        jobs.append(ManifestJob(
            slug=_label_to_slug(label), label=label, source=source,
            command=cmd_normalized, timeout_sec=timeout_min * 60,
            min_gpus=min_gpus, hw=hw, env=env_vars, file_refs=refs))
    return jobs


def _parse_ci_yaml(repo: Path, spec: ManifestSpec) -> list[ManifestJob]:
    all_jobs: dict[str, ManifestJob] = {}
    yaml_dir = repo / spec.yaml_dir
    for yaml_file, source in spec.pipelines.items():
        path = yaml_dir / yaml_file
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not data or "steps" not in data:
            continue
        for job in _extract_steps(data["steps"], source, spec):
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
    for job in jobs:
        best_module, best_score = "", 0
        for module, patterns in spec.module_test_paths.items():
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
    jobs = _parse_ci_yaml(repo, spec)
    changes = _classify_test_changes(repo)
    rename_map = {c.path: c.new_path for c in changes
                  if c.change_type == "renamed" and c.new_path}
    _validate_file_paths(jobs, repo, spec, rename_map)
    _assign_modules(jobs, spec)
    plans = _build_module_plans(jobs, changes, spec)
    return BuiltManifest(jobs=jobs, changes=changes, module_plans=plans)
