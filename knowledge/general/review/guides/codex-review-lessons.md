When Codex did the same `task/bot_task` API split on PR #3444 (`codex/pr3444-online-prompt-align`), it shipped two API-design habits I missed on the first pass:

## 1. Source enums from the producing module, not a hardcoded set at the consumer

Wrong (mine): hardcode `_legacy_task_enum = {"t2t", "i2t", "it2i", "t2i"}` literal in `serving_chat.py`.

Right (Codex): `from ...prompt_utils import available_tasks; if bot_task in available_tasks(): ...`.

**Why:** `prompt_utils._TASKS` is the **single source of truth** for the task enum. Duplicating the literal at the consumer means adding a new task (`vid2img` say) needs synchronous edits in 2 places, and any drift produces a silently-incomplete promotion path. Calling the producer's `available_tasks()` removes the duplication.

**How to apply:** Before writing `{"a", "b", ...}` literal as a membership check, grep for an existing `available_*()` / `valid_*()` / `_THINGS` constant in the producing module. If it exists, import it. The exporter usually already exists for tests; reuse it for runtime validation too.

## 2. Expose the escape hatch alongside the enum-typed knob

Wrong (mine): only expose `sys_type: str` (enum: `en_unified` / `en_think_recaption` / `en_vanilla` / `custom` / `dynamic`). The "custom" sys_type branch in `get_system_prompt()` reads a `custom_system_prompt` parameter, but my online API didn't expose any way for the caller to provide it — so `sys_type="custom"` would silently return None.

Right (Codex): expose **two** fields: `sys_type` (or `use_system_prompt` in Codex naming) for enum selection AND `system_prompt` for the verbatim custom body. Thread `system_prompt → custom_system_prompt` through `build_prompt_tokens(..., custom_system_prompt=...)`.

**Why:** Enum-typed knobs forbid covering all behaviors of the underlying function. If the function accepts an enum + a custom override, both belong on the API. Otherwise power users can't trigger the override branch from the outside, and the enum value `"custom"` becomes silently broken.

**How to apply:** When wrapping a `func(enum: str, custom: str | None = None)` shape behind an API, expose BOTH params. Grep the inner function's signature; if it has `custom_*` / `override_*` / `extra_*` / `_path: str | None` kwargs, the API needs them too. Document them as "advanced override, leave blank for default mapping from {enum_field}".

## 3. Bonus — explicit defaults after promotion

Codex's promotion logic explicitly sets `bot_task = "think"` after promoting `prompt_task = bot_task` (legacy form), instead of relying on a downstream `effective_bot_task = bot_task or "think"` fallback. Either works; explicit is slightly clearer in trace logs and harder to silently break if a future refactor moves the default elsewhere.

**Where this came up:** P1 commit of PR #3444 (`617f97ec2 fix(hunyuan_image3): split task / bot_task / sys_type at /v1/images/edits`) was amended after reviewing Codex's parallel patch (`codex/pr3444-online-prompt-align`).
