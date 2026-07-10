# intent.py — spec

`LOC ~100 · task layer · refactor-status: ok`

## Responsibility
Classify one NL command into a `TaskSpec` (LLM-only), or a clarifying question;
split compound commands into an ordered list.

## Functionality
The LLM classifies the command (kind / pr / issue / flags) into a `TaskSpec`;
below the confidence gate or with an explicit clarify → a question, never a
guess. `parse_intents` splits on connectors and carries the prior segment's
PR/issue ("… then review it") — segmentation, not classification.

## Public contract
`parse_intent(text, llm?, default_repo, model?) -> IntentResult`;
`parse_intents(...) -> list[IntentResult]`; `IntentResult(spec?, clarify)`.

## Invariants
- **LLM-only classification.** No deterministic keyword parser. Empty command
  or no configured LLM → clarify (never guess).
- **Clarify on ambiguity — never guess**: LLM confidence < 0.7, an explicit
  clarify, a malformed reply, or an unknown kind all → clarify.
- **C7**: only terminal input reaches here; fetched GitHub text never does.
  Injection is defended by channel separation + the LLM's low-confidence signal
  (a suspicious command clarifies, never runs).

## Scope — not here
No execution, no planning, no repo/network reads. Text → TaskSpec only. The
segmentation/carry-over in `parse_intents` is sentence-splitting, not
classification (which is the LLM's).

## Dependencies (allowed)
`llm.py`, `task_spec.py`.

## Extension points
New kind → add it to `TaskKind`/`KIND_TIER` (`task_spec.py`) and the
`_LLM_SYSTEM` prompt's kind list here. No hint table to maintain.

## Tests
`test_intent_taskspec.py` (LLM-path contract: mapping, confidence gate, clarify
passthrough, no-LLM, malformed reply), `test_phase_b.py` (compound split +
carry-over via a fake classifier).

## Refactor notes
`default_repo="vllm-omni"` default args are the 2 allowed repo literals
(leak-capped) — leave them; do not add more. Production always passes an LLM
(`cli.py`); intent now requires one — there is no offline fast-path (the
deliberate cost of LLM-only). If the LLM ever needs to also handle compound
splitting, `parse_intents` could return a list directly and `_COMPOUND_SPLIT`/
carry-over would go too — a bigger change, not needed yet.
