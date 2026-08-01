"""Repo-neutrality vocabulary containment (2026-08-01 audit).

`test_repo_neutral_core` pins the NARROW leak regex (the repo name +
`/rebase/`) with per-file ceilings. This suite pins the leak classes that
regex cannot see, so the audit's findings stay structural:

1. ZERO-anywhere classes — machine paths, vllm-omni MODULE names,
   branch/queue/pipeline/wheel-host literals: no core file may carry
   them at all (repo knowledge lives in `adapters/<repo>/`).
2. CONTAINED vocabulary — the parent-parity `omni`/`vllm` identifier
   naming inside the rebase engine (field names like `omni_path`, tool
   names like `git_show_omni_main`, prompt prose, the `imx-omni-pytest`
   script) is RECORDED naming debt: it is locked by the byte-parity
   goldens and the adapter's parent-verbatim tool schemas until the
   post-cutover cleanup (PR7), and this test keeps it from SPREADING —
   any new file using the vocabulary fails until it is either
   neutralized or deliberately added here with the same justification.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src" / "infermatrix_copilot"

# class 1: never anywhere in the core, no ceilings
_FORBIDDEN = re.compile(
    r"/data/zhoutaichang"                       # machine paths
    # vllm-omni module names (NOT `model_config` — that collides
    # with pydantic's own attribute name)
    r"|worker_runner|model_executor|online_serving|input_output"
    r"|dev/vllm-align|releases/v0"              # branch names
    r"|wheels\.vllm\.ai"                        # wheel host
    r"|vllm-omni-rebase(?!-agent)"              # pipeline slug (the
    # -agent sibling default in config.py is ceilinged delegation)
    r"|gpu_1_queue|gpu_4_queue|mithril"         # queue names
    r"|VLLM_PRECOMPILED_WHEEL_COMMIT",          # pin env var
)

# the delegation-by-design files test_repo_neutral_core already ceilings —
# they import/invoke the PARENT and die in PR7
_DELEGATION = {
    "engine/steps/rebase_ext.py",
    "engine/steps/rebase_native.py",
    "rebase/monitor.py",
}

# class 2: files ALLOWED to use the standalone `omni`/`vllm` parity
# vocabulary (identifier names, tool names, golden-pinned prompt prose).
# Additions require the same golden-parity justification; the set shrinks
# at the PR7 cleanup.
_VOCAB_RX = re.compile(r"(?<![A-Za-z])(omni|vllm)(?![A-Za-z])",
                       re.IGNORECASE)
_VOCAB_ALLOWED = _DELEGATION | {
    "rebase_engine/module_rebase.py",
    "rebase_engine/module_pytest.py",
    "rebase_engine/prompt_builder.py",
    "rebase_engine/rebase_tools.py",
    "rebase_engine/test_manifest.py",
    "rebase_engine/worktree.py",
    "engine/steps/rebase_v3.py",
    "config.py",        # rebase_orchestrator_cmd delegation default (PR7)
    "task_spec.py",     # default_repo literal (pinned ceiling)
    "intent.py",        # default_repo parameter defaults (pinned ceiling)
    "__init__.py",      # package docstring (pinned ceiling)
    # env allowlist pass-through prefixes (VLLM_/TORCH_…) — the
    # PARITY-pinned child-env behavior; adapter-configurable
    # prefixes are the recorded post-cutover refinement
    "testing/env_plan.py",
}


def _core_files():
    return sorted(SRC.rglob("*.py"))


def test_forbidden_repo_literals_nowhere():
    for path in _core_files():
        rel = str(path.relative_to(SRC))
        if rel in _DELEGATION:
            continue    # ceilinged delegation, dies in PR7
        hits = _FORBIDDEN.findall(path.read_text(encoding="utf-8"))
        assert not hits, (
            f"{rel}: repo-specific literal(s) {sorted(set(hits))} — this "
            "class has NO ceiling; repo knowledge belongs in "
            "adapters/<repo>/")


def test_parity_vocabulary_is_contained():
    offenders = {}
    for path in _core_files():
        rel = str(path.relative_to(SRC))
        if rel in _VOCAB_ALLOWED:
            continue
        hits = _VOCAB_RX.findall(path.read_text(encoding="utf-8"))
        if hits:
            offenders[rel] = len(hits)
    assert not offenders, (
        f"standalone omni/vllm vocabulary spread beyond the recorded "
        f"parity-debt inventory: {offenders} — neutralize the naming or "
        "justify a golden-parity addition here")


def test_vocabulary_inventory_is_not_stale():
    """Every allowed file actually uses the vocabulary — a file that no
    longer needs the exemption must leave the list (the debt only
    shrinks)."""
    for rel in sorted(_VOCAB_ALLOWED):
        path = SRC / rel
        assert path.exists(), rel
        assert _VOCAB_RX.search(path.read_text(encoding="utf-8")), (
            f"{rel} no longer uses the vocabulary — remove it from "
            "_VOCAB_ALLOWED (the inventory only shrinks)")