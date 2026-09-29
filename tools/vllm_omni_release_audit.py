"""Compatibility entry for the vLLM-Omni release audit.

The implementation is the adapter plugin ``adapters/vllm_omni/release_audit.py``
(packaged with the wheel so the knowledge service can load it). This module
re-exports it for the CLI wrapper, CI and tests.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parents[1] / "adapters" / "vllm_omni" / "release_audit.py"
_NAME = "infermatrix_adapter_vllm_omni_release_audit"
if _NAME not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_NAME, _PLUGIN)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_NAME] = _module
    _spec.loader.exec_module(_module)
_module = sys.modules[_NAME]
globals().update({
    name: getattr(_module, name) for name in dir(_module) if not name.startswith("__")
})

if __name__ == "__main__":
    raise SystemExit(main())  # noqa: F821 - re-exported above
