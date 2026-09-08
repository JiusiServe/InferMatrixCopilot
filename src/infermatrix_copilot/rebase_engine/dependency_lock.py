"""Check an adapter's exact dependency pin against its uv lock before publish."""

from pathlib import Path
import tomllib


def check_uv_dependency(repo: Path, *, package: str, extra: str,
                        version: str) -> str:
    """Return an actionable mismatch, or an empty string for a consistent pin."""
    try:
        project = tomllib.loads((repo / "pyproject.toml").read_text())
        lock = tomllib.loads((repo / "uv.lock").read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return f"dependency lock could not be read: {exc}"
    requirement = f"{package}=={version}"
    declared = project.get("project", {}).get("optional-dependencies", {}).get(extra, [])
    if requirement not in [value.replace(" ", "") for value in declared]:
        return f"optional dependency {extra!r} must declare {requirement}"
    distributions = lock.get("package", [])
    pinned = [entry for entry in distributions if entry.get("name") == package]
    if not pinned or any(entry.get("version") != version for entry in pinned):
        return f"uv.lock does not resolve {requirement}; regenerate the lock"
    project_name = project.get("project", {}).get("name")
    root = next((entry for entry in distributions
                 if entry.get("name") == project_name), {})
    requirements = root.get("metadata", {}).get("requires-dist", [])
    matching = [entry for entry in requirements if entry.get("name") == package]
    if not matching or any(entry.get("specifier") != f"=={version}"
                           for entry in matching):
        return f"uv.lock project metadata is stale for {requirement}; regenerate the lock"
    return ""
