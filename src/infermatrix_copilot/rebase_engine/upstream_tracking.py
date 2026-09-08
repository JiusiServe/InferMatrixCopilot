"""Manual rolling maintenance: published baselines and per-run wheel targets."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin

from .substate import Substate
from .wheel import WheelPickError, WheelSpec, make_arch_probe


UPSTREAM_TRAILER = "AFD-Upstream-Commit"
MAX_WHEEL_PROBES = 200


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise WheelPickError(result.stderr.strip()[-1000:]
                             or f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout.strip()


def published_baseline(repo: Path, published_ref: str) -> str:
    """Read only history fetched from the published result branch.

    Local commits from failed/disabled pushes must not advance this baseline.
    Commit trailers travel with the branch to a colleague's fresh checkout.
    """
    if not published_ref:
        return ""
    value = git(repo, "log", "--first-parent", "-1",
                f"--grep=^{UPSTREAM_TRAILER}: ",
                f"--format=%(trailers:key={UPSTREAM_TRAILER},valueonly)",
                published_ref)
    if value and not re.fullmatch(r"[0-9a-f]{40}", value):
        raise WheelPickError("published branch has an invalid upstream baseline trailer")
    return value


def select_target(repo: Path, canonical: Path, *, remote: str, branch: str,
                  baseline: str, spec: WheelSpec, sub: Substate) -> dict:
    """Freeze remote main before probing; retries keep the same selected SHA.

    The scratch's origin is the local canonical clone, so fetching its origin
    alone would silently track a stale local branch instead of upstream main.
    """
    saved = sub.get("upstream_tracking", {})
    if not saved:
        source = git(canonical, "remote", "get-url", remote)
        git(repo, "fetch", "--tags", source, f"refs/heads/{branch}")
        main_sha = git(repo, "rev-parse", "FETCH_HEAD^{commit}")
        baseline = git(repo, "rev-parse", f"{baseline}^{{commit}}")
        # A rewritten upstream history needs an operator decision, not an
        # automatic rewind of the last successfully published adaptation.
        try:
            git(repo, "merge-base", "--is-ancestor", baseline, main_sha)
        except WheelPickError as exc:
            raise WheelPickError(
                "published baseline is not an ancestor of upstream main; "
                "history needs reconciliation") from exc
        saved = {"main_sha": main_sha, "baseline_sha": baseline,
                 "branch": branch,
                 "wheel_index_template": spec.index_url_template,
                 "wheel_variant": spec.variant, "wheel_arch": spec.arch}
        sub.update({"upstream_tracking": saved})
    elif (saved["wheel_index_template"] != spec.index_url_template
          or saved["wheel_variant"] != spec.variant
          or saved["wheel_arch"] != spec.arch):
        raise WheelPickError("wheel configuration changed during this run; restore it to resume")

    selected = saved.get("selected_sha", "")
    probe = make_arch_probe(spec)
    if not selected:
        # Main's first-parent history avoids selecting an unmerged side-branch
        # build. The baseline is the lower bound, never an older fallback.
        candidates = git(repo, "rev-list", "--first-parent",
                         f"--max-count={MAX_WHEEL_PROBES + 1}",
                         f"{saved['baseline_sha']}..{saved['main_sha']}").splitlines()
        for candidate in candidates[:MAX_WHEEL_PROBES]:
            if probe(candidate):
                selected = candidate
                break
        if not selected:
            if len(candidates) > MAX_WHEEL_PROBES:
                raise WheelPickError(
                    f"no matching wheel within {MAX_WHEEL_PROBES} main commits; "
                    "baseline was not advanced")
            selected = saved["baseline_sha"]
            if not probe(selected):
                raise WheelPickError("no matching wheel at or after the published baseline")
        saved.update(selected_sha=selected)
        sub.update({"upstream_tracking": saved})
    git(repo, "checkout", "--detach", selected)
    return saved


def index_root(spec: WheelSpec, commit: str) -> str:
    return urljoin(spec.index_url_template.format(
        commit=commit, variant=spec.variant, package=spec.package), "../")


def runtime_contract(tracking: dict, dependency: dict) -> str:
    if not tracking.get("version"):
        return ""
    package, extra = dependency["package"], dependency["extra"]
    module, index_name = dependency["module"], dependency["index_name"]
    return (
        "\n## This run's rolling upstream target\n"
        f"Main snapshot: {tracking['main_sha']}\n"
        f"Selected commit: {tracking['selected_sha']}\n"
        f"Required runtime base version: {tracking['version']}\n"
        f"Commit-specific uv index: {tracking['index_url']}\n"
        f"The {module} module must update pyproject.toml's optional {extra} "
        f"dependency to {package}=={tracking['version']}, use an explicit tool.uv.index "
        f"named {index_name} with the URL above and tool.uv.sources.{package} = "
        f"{{index = '{index_name}'}}, then regenerate uv.lock. "
        f"The lock's {package} package must resolve from that commit-specific index. "
        "Do not keep the old release pin, disable lock checks, or change the "
        "selected upstream checkout. Other modules must preserve this pin.\n")
