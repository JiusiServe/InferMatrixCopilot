#!/usr/bin/env python3
"""Reviewbot arm: generate omni-reviewbot Direct reviews over dataset PRs.

The bot is a loop+model combination (harness arm, like the cursor arm):
its results live in results/reviewbot/ and are never merged into the
generator ablation tables. Scope is the dataset's train+val pr_review
items only — test stays frozen.

Measurement contract enforced per invocation, all fail-closed:
  - POST_MODE=shadow hard-set and `status: shadow` asserted in CLI output
    (a review that reached a publish path aborts the campaign);
  - REVIEW_CONTEXT_MODE=no_discussion hard-set and the CLI's
    `review_context: no_discussion (0 threads)` line asserted — on these
    PRs the historical review threads ARE the ground truth;
  - reviewed head (from the artifact name pr-<n>-<head>.md) must equal
    goal-eval/expected_pr_heads.json[<n>];
  - the CLI's `changed_files: N` must match the frozen GT diff's file
    count (gt/pr<N>.diff);
  - the sanitized artifact must fit judge_val.py's 24k candidate cap.

Replication has ONE owner: this runner. ARM_TAG=<tag> creates
arms/<tag>_r1..rN (GEN_REPLICATES, default 3); replicates of one item run
sequentially (the bot's artifact name repeats per head, and each artifact
is moved out immediately), items run with small parallelism (ARM_JOBS).

Env: ARM_TAG (required) · GEN_REPLICATES=3 · ONLY_ITEMS=4893,4810 ·
ARM_JOBS=2 · REVIEWBOT_PYTHON (required installed release venv Python) ·
REVIEWBOT_RELEASE_MANIFEST (optional only when safely discoverable beside that
venv) · REVIEWBOT_ENV_FILE (optional; loaded first, hard overrides win) ·
REVIEWBOT_TIMEOUT_S=1800 · REVIEWBOT_EVAL_ROOT (tests only) ·
REVIEWBOT_EVAL_ALLOW_UNPAIRED=1 (non-month throwaway runs only)
Flags: --dry-run (print the plan, touch nothing) · --preflight (doctor only)
"""
from __future__ import annotations

import email.parser
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any

import yaml

HERE = Path(os.environ.get("REVIEWBOT_EVAL_ROOT") or Path(__file__).parent)
DATASET = HERE / "vllm_omni_dataset.yaml"
EXPECTED_HEADS = HERE / "goal-eval" / "expected_pr_heads.json"
GT = HERE / "gt"
ARMS = HERE / "arms"
STATE_DIR = HERE.parent / "raw" / "reviewbot_state"
JUDGE_CAP = 24_000  # judge_val.py silently truncates candidates here

_MARKER = re.compile(r"<!--.*?-->", re.DOTALL)
_CONTEXT_LINE = re.compile(
    r"^review_context: (\S+) \((\d+) threads\)$", re.MULTILINE
)
_CHANGED_LINE = re.compile(r"^changed_files: (\d+)$", re.MULTILINE)
_STATUS_LINE = re.compile(r"^status: (\S+)$", re.MULTILINE)
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MONTH_TAG = re.compile(r"reviewbot_\d{4}-\d{2}\Z")
_MANIFEST_LIMIT = 2 * 1024 * 1024
_REQUIRED_CAPABILITIES = {
    "supports_expected_head",
    "supports_structured_result",
    "supports_post_false",
    "supports_file_locking",
    "supports_idempotent_strict_start",
    "supports_knowledge_curation",
}
_RUNTIME_PROBE = r"""
import inspect
import json
import sys
from importlib.metadata import version

import omni_reviewbot
import infermatrix_copilot.sdk.v1 as provider_sdk

print(json.dumps({
    "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    "prefix": sys.prefix,
    "reviewbot_module": inspect.getfile(omni_reviewbot),
    "provider_module": inspect.getfile(provider_sdk),
    "reviewbot_version": version("omni-reviewbot"),
    "provider_version": version("infermatrix-copilot"),
    "provider_capabilities": provider_sdk.get_capabilities().to_dict(),
}, sort_keys=True))
"""


def sanitize(body: str) -> str:
    """Blind judging: explicit arm labels must not reach the judge."""
    body = _MARKER.sub("", body)
    body = body.replace("## Omni ReviewBot review", "## Review", 1)
    return body.strip() + "\n"


def gt_changed_files(pr: int) -> int:
    text = (GT / f"pr{pr}.diff").read_text(encoding="utf-8", errors="replace")
    return sum(
        1 for line in text.splitlines() if line.startswith("diff --git ")
    )


def dataset_items() -> list[int]:
    data = yaml.safe_load(DATASET.read_text())
    items = [
        int(entry["pr"])
        for entry in data["pr_review"]
        if entry.get("split") in {"train", "val"}
    ]
    only = os.environ.get("ONLY_ITEMS", "").strip()
    if only:
        keep = {int(x) for x in only.split(",") if x.strip()}
        items = [n for n in items if n in keep]
    return sorted(items)


# Child-env keys that change what the Direct review actually does; they are
# part of the arm's identity (secrets are deliberately NOT in this list and
# never reach a manifest).
_BEHAVIOR_KEYS = (
    "AGENT_PROVIDER", "REVIEW_MODEL", "CURSOR_MODEL", "CODEX_COMMAND",
    "CODEX_TIMEOUT_SECONDS", "CURSOR_TIMEOUT_SECONDS",
    "GITHUB_REPOSITORY",
)


class ReleaseValidationError(RuntimeError):
    """The selected interpreter is not the manifest's paired artifact."""


def build_config(child_env: dict[str, str], release: dict[str, Any]) -> dict:
    """Stable arm identity from paired artifacts and behavior-only settings."""
    return {
        "release": release,
        "review_context_mode": "no_discussion",
        "post_mode": "shadow",
        "env": {key: child_env.get(key, "") for key in _BEHAVIOR_KEYS},
    }


def _canonical_distribution(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _wheel_metadata(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [
                name for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            ]
            if len(names) != 1:
                raise ReleaseValidationError(
                    f"{path.name}: expected one wheel METADATA file"
                )
            metadata = email.parser.BytesParser().parsebytes(
                archive.read(names[0])
            )
    except (OSError, zipfile.BadZipFile) as exc:
        raise ReleaseValidationError(f"invalid wheel: {path.name}") from exc
    name, version = metadata.get("Name"), metadata.get("Version")
    if not name or not version:
        raise ReleaseValidationError(f"{path.name}: incomplete wheel metadata")
    return name, version


def _release_python(value: str) -> Path:
    if not value:
        raise ReleaseValidationError("REVIEWBOT_PYTHON is required")
    path = Path(value).expanduser()
    if (
        not path.is_absolute()
        or ".." in path.parts
        or path.parent.name != "bin"
        or path.parent.parent.name != ".venv"
        or not path.name.startswith("python")
    ):
        raise ReleaseValidationError(
            "REVIEWBOT_PYTHON must be an absolute <release>/.venv/bin/python"
        )
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ReleaseValidationError("REVIEWBOT_PYTHON is not executable")
    return path


def _release_manifest_path(python: Path, configured: str) -> Path:
    app_root = python.parent.parent.parent
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute() or ".." in candidate.parts:
            raise ReleaseValidationError(
                "REVIEWBOT_RELEASE_MANIFEST must be an absolute path"
            )
    else:
        candidate = app_root / "manifest.json"
    if candidate.is_symlink() or not candidate.is_file():
        raise ReleaseValidationError("paired release manifest is missing")
    resolved = candidate.resolve()
    if resolved.parent != app_root.resolve():
        raise ReleaseValidationError(
            "paired release manifest is outside the release app root"
        )
    return resolved


def _runtime_identity(
    python: Path, child_env: dict[str, str]
) -> dict[str, Any]:
    completed = subprocess.run(
        [str(python), "-I", "-c", _RUNTIME_PROBE],
        cwd=python.parent.parent.parent,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-1000:]
        raise ReleaseValidationError(
            f"installed release identity probe failed: {detail}"
        )
    try:
        runtime = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ReleaseValidationError(
            "installed release identity probe returned invalid JSON"
        ) from exc
    if not isinstance(runtime, dict):
        raise ReleaseValidationError("installed release identity is not an object")
    expected_prefix = python.parent.parent.resolve()
    try:
        prefix = Path(runtime["prefix"]).resolve()
        modules = (
            Path(runtime["reviewbot_module"]).resolve(),
            Path(runtime["provider_module"]).resolve(),
        )
        for module in modules:
            module.relative_to(prefix)
    except (KeyError, OSError, ValueError, TypeError) as exc:
        raise ReleaseValidationError(
            "runtime modules are not installed inside the selected release venv"
        ) from exc
    if prefix != expected_prefix:
        raise ReleaseValidationError(
            "REVIEWBOT_PYTHON resolved a different runtime prefix"
        )
    return runtime


def _safe_wheel(root: Path, value: Any) -> Path:
    if not isinstance(value, str):
        raise ReleaseValidationError("manifest wheel path must be a string")
    pure = PurePosixPath(value)
    if (
        len(pure.parts) != 2
        or pure.parts[0] != "wheelhouse"
        or pure.is_absolute()
        or ".." in pure.parts
        or not pure.name.endswith(".whl")
    ):
        raise ReleaseValidationError(f"unsafe manifest wheel path: {value!r}")
    candidate = root.joinpath(*pure.parts)
    if candidate.is_symlink() or not candidate.is_file():
        raise ReleaseValidationError(f"manifest wheel is missing: {value}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ReleaseValidationError("manifest wheel escapes release root") from exc
    return resolved


def validate_paired_release(
    manifest_path: Path, runtime: dict[str, Any]
) -> dict[str, Any]:
    raw = manifest_path.read_bytes()
    if not raw or len(raw) > _MANIFEST_LIMIT:
        raise ReleaseValidationError("paired release manifest size is invalid")
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReleaseValidationError("paired release manifest is invalid JSON") from exc
    required_top = {
        "schema_version", "release_id", "created_at", "python", "reviewbot",
        "provider", "api_expectations", "provider_capabilities", "wheelhouse",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != required_top
        or manifest.get("schema_version") != 1
    ):
        raise ReleaseValidationError("unsupported paired release manifest")

    components: dict[str, dict[str, Any]] = {}
    for name, distribution in (
        ("reviewbot", "omni-reviewbot"),
        ("provider", "infermatrix-copilot"),
    ):
        component = manifest.get(name)
        fields = {"distribution", "version", "git_sha", "wheel", "sha256"}
        if not isinstance(component, dict) or set(component) != fields:
            raise ReleaseValidationError(f"malformed {name} component")
        if _canonical_distribution(str(component["distribution"])) != distribution:
            raise ReleaseValidationError(f"unexpected {name} distribution")
        if not _SHA.fullmatch(str(component["git_sha"])):
            raise ReleaseValidationError(f"invalid {name} git SHA")
        if not _DIGEST.fullmatch(str(component["sha256"])):
            raise ReleaseValidationError(f"invalid {name} wheel hash")
        components[name] = component
    release_id = (
        f"{components['reviewbot']['git_sha']}-"
        f"{components['provider']['git_sha']}"
    )
    if manifest["release_id"] != release_id:
        raise ReleaseValidationError("release ID does not bind both component SHAs")

    capabilities = runtime.get("provider_capabilities")
    if not isinstance(capabilities, dict):
        raise ReleaseValidationError("runtime has no public provider capabilities")
    if runtime.get("python") != manifest["python"]:
        raise ReleaseValidationError("runtime Python differs from manifest")
    if runtime.get("reviewbot_version") != components["reviewbot"]["version"]:
        raise ReleaseValidationError("installed ReviewBot version differs from manifest")
    if runtime.get("provider_version") != components["provider"]["version"]:
        raise ReleaseValidationError("installed provider version differs from manifest")
    if capabilities != manifest["provider_capabilities"]:
        raise ReleaseValidationError(
            "runtime public capabilities differ from paired manifest"
        )
    if capabilities.get("distribution_version") != runtime.get("provider_version"):
        raise ReleaseValidationError(
            "runtime provider version differs from public capabilities"
        )
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(
        capabilities.get("resource_revision", "")
    )):
        raise ReleaseValidationError("runtime resource revision is invalid")
    expectations = manifest.get("api_expectations")
    if not isinstance(expectations, dict):
        raise ReleaseValidationError("manifest has no API expectations")
    for kind in ("direct", "strict", "knowledge"):
        key = f"{kind}_api_version"
        if expectations.get(key) != capabilities.get(key):
            raise ReleaseValidationError(f"runtime {kind} API differs from manifest")
    required = expectations.get("required_capabilities")
    if set(required or ()) != _REQUIRED_CAPABILITIES or any(
        capabilities.get(key) is not True for key in _REQUIRED_CAPABILITIES
    ):
        raise ReleaseValidationError("runtime capability handshake is incomplete")

    root = manifest_path.parent.resolve()
    entries: dict[str, dict[str, Any]] = {}
    wheelhouse = manifest.get("wheelhouse")
    if not isinstance(wheelhouse, list) or len(wheelhouse) < 2:
        raise ReleaseValidationError("manifest wheelhouse is incomplete")
    for item in wheelhouse:
        fields = {"path", "distribution", "version", "sha256", "size"}
        if not isinstance(item, dict) or set(item) != fields:
            raise ReleaseValidationError("malformed wheelhouse entry")
        path = _safe_wheel(root, item["path"])
        if item["path"] in entries:
            raise ReleaseValidationError("duplicate wheelhouse path")
        if (
            _file_digest(path) != item["sha256"]
            or path.stat().st_size != item["size"]
        ):
            raise ReleaseValidationError(f"wheel artifact mismatch: {path.name}")
        entries[item["path"]] = item
    actual = {
        f"wheelhouse/{path.name}"
        for path in (root / "wheelhouse").glob("*.whl")
        if path.is_file() and not path.is_symlink()
    }
    if actual != set(entries):
        raise ReleaseValidationError("wheelhouse files differ from manifest")
    for name, component in components.items():
        item = entries.get(component["wheel"])
        if item is None or any(
            item[key] != component[key]
            for key in ("distribution", "version", "sha256")
        ):
            raise ReleaseValidationError(f"{name} wheel is not hash-bound")
        wheel = _safe_wheel(root, component["wheel"])
        distribution, version = _wheel_metadata(wheel)
        if (
            _canonical_distribution(distribution)
            != _canonical_distribution(component["distribution"])
            or version != component["version"]
        ):
            raise ReleaseValidationError(f"{name} wheel metadata differs")

    return {
        "paired": True,
        "throwaway": False,
        "manifest_fingerprint": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "release_id": release_id,
        "python": manifest["python"],
        "reviewbot": {
            key: components["reviewbot"][key]
            for key in ("version", "git_sha", "sha256")
        },
        "provider": {
            **{
                key: components["provider"][key]
                for key in ("version", "git_sha", "sha256")
            },
            "resource_revision": capabilities["resource_revision"],
        },
    }


def _declared_runtime(manifest_path: Path) -> dict[str, Any]:
    """Project manifest claims through the normal validator before staging."""
    try:
        manifest = json.loads(manifest_path.read_bytes())
        return {
            "python": manifest["python"],
            "reviewbot_version": manifest["reviewbot"]["version"],
            "provider_version": manifest["provider"]["version"],
            "provider_capabilities": manifest["provider_capabilities"],
        }
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ReleaseValidationError(
            "paired release manifest cannot declare a runtime"
        ) from exc


def _stage_release(manifest_path: Path, destination: Path) -> Path:
    """Copy the already-validated wheelhouse into a private immutable input."""
    raw = manifest_path.read_bytes()
    if not raw or len(raw) > _MANIFEST_LIMIT:
        raise ReleaseValidationError("paired release manifest size is invalid")
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:  # defensive; caller validated it
        raise ReleaseValidationError("paired release manifest changed") from exc
    wheelhouse = manifest.get("wheelhouse") if isinstance(manifest, dict) else None
    if not isinstance(wheelhouse, list) or len(wheelhouse) < 2:
        raise ReleaseValidationError("manifest wheelhouse is incomplete")
    destination.mkdir(mode=0o700, parents=True)
    staged_manifest = destination / "manifest.json"
    staged_manifest.write_bytes(raw)
    staged_wheels = destination / "wheelhouse"
    staged_wheels.mkdir(mode=0o700)
    root = manifest_path.parent.resolve()
    for item in wheelhouse:
        fields = {"path", "distribution", "version", "sha256", "size"}
        if not isinstance(item, dict) or set(item) != fields:
            raise ReleaseValidationError("malformed wheelhouse entry")
        source = _safe_wheel(root, item["path"])
        target = staged_wheels / source.name
        shutil.copyfile(source, target)
        target.chmod(0o600)
        if (
            _file_digest(target) != item["sha256"]
            or target.stat().st_size != item["size"]
        ):
            raise ReleaseValidationError(
                f"wheel changed while staging: {source.name}"
            )
    return staged_manifest


def _run_release_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    purpose: str,
    timeout: int = 600,
) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-1500:]
        raise ReleaseValidationError(f"{purpose} failed: {detail}")


def _fresh_release_venv(
    bootstrap_python: Path,
    manifest_path: Path,
    child_env: dict[str, str],
) -> tuple[TemporaryDirectory[str], Path, Path]:
    """Install the checked pair offline; this interpreter runs the campaign."""
    temporary = TemporaryDirectory(prefix="reviewbot-eval-release-")
    root = Path(temporary.name)
    try:
        release_root = root / "release"
        staged_manifest = _stage_release(manifest_path, release_root)
        # Validate the private snapshot, not paths that could change between
        # validation and pip. No artifact executes before this completes.
        validate_paired_release(
            staged_manifest, _declared_runtime(staged_manifest)
        )
        manifest = json.loads(staged_manifest.read_text(encoding="utf-8"))
        venv = release_root / ".venv"
        _run_release_command(
            [str(bootstrap_python), "-I", "-m", "venv", str(venv)],
            cwd=release_root,
            env=child_env,
            purpose="fresh release venv creation",
        )
        python = _release_python(str(venv / "bin" / "python"))
        install_env = {
            key: value
            for key, value in child_env.items()
            if not key.startswith("PIP_")
        }
        install_env.update({
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_NO_INDEX": "1",
            "PIP_NO_CACHE_DIR": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        })
        wheelhouse = release_root / "wheelhouse"
        roots = [
            str(_safe_wheel(release_root, manifest[name]["wheel"]))
            for name in ("reviewbot", "provider")
        ]
        _run_release_command(
            [
                str(python), "-I", "-m", "pip", "install",
                "--disable-pip-version-check", "--no-input", "--no-index",
                "--no-cache-dir", "--only-binary=:all:",
                "--find-links", str(wheelhouse),
                *roots,
            ],
            cwd=release_root,
            env=install_env,
            purpose="offline paired-wheel installation",
        )
        _run_release_command(
            [str(python), "-I", "-m", "pip", "check"],
            cwd=release_root,
            env=install_env,
            purpose="fresh release dependency check",
            timeout=120,
        )
        return temporary, python, staged_manifest
    except Exception:
        temporary.cleanup()
        raise


def _unpaired_release(runtime: dict[str, Any], reason: str) -> dict[str, Any]:
    capabilities = runtime.get("provider_capabilities") or {}
    return {
        "paired": False,
        "throwaway": True,
        "manifest_fingerprint": "unpaired",
        "release_id": "unpaired",
        "reason": reason[:300],
        "reviewbot": {"version": str(runtime.get("reviewbot_version", "unknown"))},
        "provider": {
            "version": str(runtime.get("provider_version", "unknown")),
            "resource_revision": str(capabilities.get("resource_revision", "unknown")),
        },
    }


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


class Runner:
    def __init__(self) -> None:
        self.tag = os.environ.get("ARM_TAG", "").strip()
        if not self.tag:
            sys.exit("ARM_TAG is required (e.g. ARM_TAG=reviewbot_2026-09)")
        self.gen_reps = int(os.environ.get("GEN_REPLICATES", "3"))
        self.jobs = int(os.environ.get("ARM_JOBS", "2"))
        self.timeout = int(os.environ.get("REVIEWBOT_TIMEOUT_S", "1800"))
        self.python = os.environ.get("REVIEWBOT_PYTHON", "").strip()
        self.release_manifest = os.environ.get(
            "REVIEWBOT_RELEASE_MANIFEST", ""
        ).strip()
        self.allow_unpaired = (
            os.environ.get("REVIEWBOT_EVAL_ALLOW_UNPAIRED") == "1"
        )
        env_file_value = os.environ.get("REVIEWBOT_ENV_FILE", "").strip()
        env_file = Path(env_file_value).expanduser() if env_file_value else None
        # An explicitly selected env file loads first; the measurement contract
        # wins last. Provider source overrides never enter the child process.
        child = dict(os.environ)
        if env_file is not None:
            child.update(_parse_env_file(env_file))
        child = {
            key: value
            for key, value in child.items()
            if not key.startswith("INFERMATRIX_")
        }
        child.pop("PYTHONPATH", None)
        child.pop("PYTHONHOME", None)
        child.update(
            {
                "POST_MODE": "shadow",
                "REVIEW_CONTEXT_MODE": "no_discussion",
                "REVIEWBOT_STATE_DIR": str(STATE_DIR),
                "PYTHONNOUSERSITE": "1",
                "PYTHONSAFEPATH": "1",
            }
        )
        self.child_env = child
        self.expected = {
            int(k): v for k, v in json.loads(EXPECTED_HEADS.read_text()).items()
        }
        self.items = dataset_items()
        self.failures: list[str] = []
        self._lock = threading.Lock()
        self.config: dict | None = None
        self._release_temp: TemporaryDirectory[str] | None = None

    def ensure_config(self) -> dict:
        if self.config is None:
            fresh_temp: TemporaryDirectory[str] | None = None
            try:
                bootstrap_python = _release_python(self.python)
                manifest = _release_manifest_path(
                    bootstrap_python, self.release_manifest
                )
                fresh_temp, python, staged_manifest = _fresh_release_venv(
                    bootstrap_python, manifest, self.child_env
                )
                runtime = _runtime_identity(python, self.child_env)
                release = validate_paired_release(staged_manifest, runtime)
            except (OSError, ReleaseValidationError) as exc:
                if fresh_temp is not None:
                    fresh_temp.cleanup()
                if not self.allow_unpaired:
                    sys.exit(
                        "paired ReviewBot release validation failed: "
                        f"{exc}; set REVIEWBOT_EVAL_ALLOW_UNPAIRED=1 only "
                        "for a non-month throwaway run"
                    )
                if _MONTH_TAG.fullmatch(self.tag):
                    sys.exit(
                        "REVIEWBOT_EVAL_ALLOW_UNPAIRED=1 is forbidden for "
                        "monthly campaign tags"
                    )
                try:
                    python = _release_python(self.python)
                    runtime = _runtime_identity(python, self.child_env)
                except (OSError, ReleaseValidationError) as runtime_exc:
                    sys.exit(
                        "unpaired mode still requires an installed ReviewBot "
                        f"release: {runtime_exc}"
                    )
                release = _unpaired_release(runtime, str(exc))
                print(
                    "[arm] WARNING: unpaired throwaway release; results are "
                    "not eligible for the monthly series",
                    flush=True,
                )
            else:
                self._release_temp = fresh_temp
            self.python = str(python)
            if self._release_temp is not None:
                venv = Path(self.python).parent.parent
                self.child_env["VIRTUAL_ENV"] = str(venv)
                self.child_env["PATH"] = (
                    str(venv / "bin")
                    + os.pathsep
                    + self.child_env.get("PATH", "")
                )
            self.config = build_config(self.child_env, release)
        return self.config

    def close(self) -> None:
        if self._release_temp is not None:
            self._release_temp.cleanup()
            self._release_temp = None

    # --- manifests ---

    def _arm_dir(self, rep: int) -> Path:
        return ARMS / f"{self.tag}_r{rep}"

    def _manifest_path(self, rep: int) -> Path:
        return self._arm_dir(rep) / "manifest.json"

    def _init_manifest(self, rep: int) -> None:
        path = self._manifest_path(rep)
        config = self.ensure_config()
        if path.exists():
            stored = json.loads(path.read_text())
            if stored.get("config") != config:
                sys.exit(
                    f"{path}: existing manifest was generated under a "
                    f"different configuration — refusing to mix.\n"
                    f"stored:  {stored.get('config')}\n"
                    f"current: {config}"
                )
            if stored.get("stems") != [f"pr{n}" for n in self.items]:
                sys.exit(
                    f"{path}: existing manifest targets different items — "
                    "refusing to mix (delete the arm dir to restart)."
                )
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "arm_tag": self.tag,
                    "replicate": rep,
                    "stems": [f"pr{n}" for n in self.items],
                    "config": config,
                    "judge_cap": JUDGE_CAP,
                    "reviewed_heads": {},
                    "started_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    ),
                },
                indent=2,
            )
        )

    def _record_head(self, rep: int, stem: str, head: str) -> None:
        with self._lock:
            path = self._manifest_path(rep)
            manifest = json.loads(path.read_text())
            manifest["reviewed_heads"][stem] = head
            path.write_text(json.dumps(manifest, indent=2))

    # --- invocation ---

    def preflight(self) -> None:
        config = self.ensure_config()
        if config["env"]["AGENT_PROVIDER"] == "cursor" and not os.environ.get(
            "REVIEWBOT_EVAL_ALLOW_CURSOR"
        ):
            sys.exit(
                "AGENT_PROVIDER=cursor: cursor-family models have read the "
                "imreview methodology skills from $HOME before (contamination "
                "ledger). Vault the skill copies first, then set "
                "REVIEWBOT_EVAL_ALLOW_CURSOR=1."
            )
        for n in self.items:
            if n not in self.expected:
                sys.exit(f"pr{n} missing from {EXPECTED_HEADS}")
            if not (GT / f"pr{n}.diff").is_file():
                sys.exit(f"gt/pr{n}.diff missing — cannot validate diff range")
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        doctor = subprocess.run(
            [self.python, "-m", "omni_reviewbot", "doctor"],
            cwd=STATE_DIR, env=self.child_env,
            capture_output=True, text=True, timeout=300, check=False,
        )
        if doctor.returncode != 0:
            sys.exit(
                "omni-reviewbot doctor failed:\n"
                + (doctor.stdout or "") + (doctor.stderr or "")
            )

    def _invoke(self, pr: int, rep: int) -> None:
        stem = f"pr{pr}"
        out_md = self._arm_dir(rep) / f"{stem}.md"
        if out_md.exists() and out_md.stat().st_size > 0:
            return
        completed = subprocess.run(
            [self.python, "-m", "omni_reviewbot", "review", "--pr", str(pr)],
            cwd=STATE_DIR, env=self.child_env,
            capture_output=True, text=True, timeout=self.timeout, check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        if completed.returncode != 0:
            raise RuntimeError(f"exit {completed.returncode}: {output[-800:]}")
        status = _STATUS_LINE.search(completed.stdout or "")
        if not status or status.group(1) != "shadow":
            raise RuntimeError(
                f"outcome was not `status: shadow` — refusing "
                f"(got {status.group(1) if status else 'no status line'})"
            )
        context = _CONTEXT_LINE.search(completed.stdout or "")
        if not context or context.group(1) != "no_discussion" or (
            context.group(2) != "0"
        ):
            raise RuntimeError(
                "no `review_context: no_discussion (0 threads)` evidence — "
                "the run may have seen the ground-truth threads"
            )
        changed = _CHANGED_LINE.search(completed.stdout or "")
        expected_files = gt_changed_files(pr)
        if not changed or int(changed.group(1)) != expected_files:
            raise RuntimeError(
                f"changed_files {changed.group(1) if changed else '?'} != "
                f"frozen GT diff's {expected_files} — diff range drifted"
            )
        artifacts = sorted(
            (STATE_DIR / "artifacts").glob(f"pr-{pr}-*.md"),
            key=lambda p: p.stat().st_mtime,
        )
        if not artifacts:
            raise RuntimeError("no artifact produced")
        artifact = artifacts[-1]
        head = artifact.name[len(f"pr-{pr}-"):-len(".md")]
        if head != self.expected[pr]:
            raise RuntimeError(
                f"reviewed head {head[:12]} != pinned {self.expected[pr][:12]}"
            )
        body = sanitize(artifact.read_text())
        if len(body) > JUDGE_CAP:
            raise RuntimeError(
                f"sanitized review is {len(body)} chars — over the judge's "
                f"{JUDGE_CAP} cap; it would be silently truncated"
            )
        out_md.write_text(body)
        # Move (not copy): the next replicate reuses the same artifact name.
        artifact.unlink()
        self._record_head(rep, stem, head)

    def _run_item(self, pr: int) -> str:
        for rep in range(1, self.gen_reps + 1):
            try:
                self._invoke(pr, rep)
            except Exception as exc:  # noqa: BLE001 — every failure is a verdict
                with self._lock:
                    self.failures.append(f"pr{pr} r{rep}: {exc}")
                return f"pr{pr}: INVALID at r{rep}"
        return f"pr{pr}: ok x{self.gen_reps}"

    def run(self, *, dry_run: bool) -> int:
        plan = [
            f"  pr{n} x{self.gen_reps} -> " + ", ".join(
                str(self._arm_dir(r) / f"pr{n}.md")
                for r in range(1, self.gen_reps + 1)
            )
            for n in self.items
        ]
        print(
            f"[arm] tag={self.tag} items={len(self.items)} "
            f"reps={self.gen_reps} python={self.python or '<execution-required>'} "
            f"provider={self.child_env.get('AGENT_PROVIDER', 'codex')}"
        )
        print("\n".join(plan))
        if dry_run:
            print("[arm] dry run — nothing invoked")
            return 0
        self.preflight()
        (STATE_DIR / "artifacts").mkdir(parents=True, exist_ok=True)
        for rep in range(1, self.gen_reps + 1):
            self._init_manifest(rep)
        with ThreadPoolExecutor(max_workers=self.jobs) as pool:
            futures = {pool.submit(self._run_item, n): n for n in self.items}
            for future in as_completed(futures):
                print(f"[arm] {future.result()}", flush=True)
        if self.failures:
            print(
                f"[arm] {len(self.failures)} INVALID item(s) — the campaign "
                "must not be judged:", flush=True,
            )
            for failure in self.failures:
                print(f"  {failure}")
            return 1
        print("[arm] complete")
        return 0


def main() -> int:
    runner = Runner()
    try:
        if "--preflight" in sys.argv:
            runner.preflight()
            print("[arm] preflight ok")
            return 0
        return runner.run(dry_run="--dry-run" in sys.argv)
    finally:
        runner.close()


if __name__ == "__main__":
    raise SystemExit(main())
