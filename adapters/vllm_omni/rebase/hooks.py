"""vllm-omni rebase hooks — adapter zero's behavioral overrides.

Declared via `rebase.hooks` in the manifest (human-gated HIGH-RISK section);
the copilot loads this file only for the active adapter. Keep this THIN:
anything expressible as data belongs in the manifest or the rebase data
files, not here.
"""

from infermatrix_copilot.rebase_engine.hooks import RebaseHooks


class VllmOmniHooks(RebaseHooks):
    def adaptive_guidance(self, module: str) -> str:
        # The learned-skills rendering (parent _build_adaptive_guidance:
        # SkillStore.find_for_module + candidate hints) arrives with the
        # assembly PR's knowledge wiring; returning "" keeps the template's
        # neutral placeholder until then. Never raise from here.
        return ""


HOOKS = VllmOmniHooks()
