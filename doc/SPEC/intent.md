# intent.py — spec

`LOC ~159 · task layer · refactor-status: ok`

## Responsibility
Parse one NL command → `TaskSpec`, or a clarifying question; split compound
commands into an ordered list.

## Functionality
Deterministic keyword/regex parse first; LLM parse as fallback; ambiguity →
clarify. `parse_intents` splits on connectors and carries the prior segment's
PR/issue ("… then review it").

## Public contract
`parse_intent(text, llm?, default_repo, model?) -> IntentResult`;
`parse_intents(...) -> list[IntentResult]`; `IntentResult(spec?, clarify)`.

## Invariants
- Deterministic-first, LLM-fallback, **clarify on ambiguity — never guess**
  (low confidence / injection-looking → clarify).
- **C7**: only terminal input reaches here; fetched GitHub text never does.
- Guards: `pr_*` kind needs a PR number; `repo_*` kinds refuse when a PR present.

## Scope — not here
No execution, no planning, no repo/network reads. Text → TaskSpec only.

## Dependencies (allowed)
`llm.py`, `task_spec.py`.

## Extension points
New kind → a `_KIND_HINTS` row + matching target guard + LLM system-prompt kind
list.

## Tests
`test_intent_taskspec.py`,
`test_profile_steps.py::test_intent_parses_profile_command`.

## Refactor notes
`default_repo="vllm-omni"` default arg is one of the 2 allowed repo literals
(leak-capped) — leave it; do not add more. If kinds grow, consider a small
kind-registry table (hints + guard + prompt fragment) to avoid three
parallel edit sites per kind.
