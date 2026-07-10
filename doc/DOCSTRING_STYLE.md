# Docstring style — omni-copilot

The house convention for docstrings, grounded in [PEP 257](https://peps.python.org/pep-0257/)
(structure) and the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
(what to document), adapted to this codebase's terse, rationale-first voice.

**Every module, class, function, and method carries a docstring.** It explains
the *logic* (what it does and the non-obvious *why*) and the *inputs/outputs* —
not a restatement of the signature.

## Form (PEP 257)

- Triple double-quotes `"""..."""`. The module docstring is the file's very first
  statement (before `from __future__ import ...` and all imports).
- **Summary line**: one imperative-mood sentence, ≤ ~88 cols, ending in a period.
  For obvious cases the summary line alone is the whole docstring (one-liner).
- Non-trivial cases: summary line, blank line, then the body.
- Closing `"""` on its own line for multi-line docstrings.

## What each kind documents

- **Module** — the one thing the file owns + a one-line note of what it exports.
  For a re-export `__init__.py`, say what the package groups and that the surface
  is re-exported.
- **Class** — its behavior/role in one line; note the key attributes or the
  invariant it upholds when that isn't obvious. `@dataclass` field meaning goes
  in the class docstring (or an inline `#` comment), not a separate `Attributes`
  block unless there are many.
- **Function / method** — summary of behavior, then the inputs → output and the
  non-obvious logic, **in prose**. Name the parameters that carry meaning and say
  what the return represents. Reserve explicit `Args:`/`Returns:` sections for
  functions with many parameters where prose would be harder to read.

## Voice (match the existing code)

- Rationale-first: prefer explaining *why* over narrating *what* the code line-by-line
  already shows. Cite the design/eval when it explains a choice (e.g. "single
  untooled reduction call: a tool-looped reducer over-dropped in live runs").
- Keep the safety/contract framing that the specs use: mention when a function is
  a fail-closed gate, publishes state for a later step (**B2**), degrades to a
  typed BLOCKED result, or records a `capability_gap`.
- Do not invent behavior. If unsure what a branch does, describe it at the level
  the code supports — never guess specifics (line numbers, thresholds) not present.

## Examples (from this repo)

Function — inputs → output + the why:

```python
def guard_push(policy: PushPolicy, protected_branches: list[str]) -> PushDecision:
    """Authorize a push: allow only when `policy.allowed` AND the target branch
    is not in `protected_branches`. Returns a PushDecision carrying the concrete
    git command (never run here) or a deny reason — the single C4 choke point, so
    every push path is authorized in one place."""
```

Class — role + key attribute:

```python
class StepResult:
    """The outcome of one step: `ok` plus, on failure, a typed `failure_kind`
    (drives the engine's retry/replan/escalate branch) and the `state_updates`
    a later step consumes. Never raises across the step boundary — failures are
    values, not exceptions."""
```

Re-export `__init__.py` module:

```python
"""Review subsystem: diff summarization, trigger evaluation, and the patch/plan
reviewers. Re-exports the public surface (`build_diff_summary`, `ReviewVerdict`,
`run_patch_review`) so callers import from the package, not its modules."""
```

## Don't

- Don't add `Args:`/`Returns:`/`Raises:` scaffolding to trivial accessors — a
  one-liner is correct and PEP-257-preferred.
- Don't change code, signatures, or existing (correct) docstrings while adding
  new ones. Docstrings are additive.
- Don't duplicate the per-file SPEC — the docstring is the local, in-code view;
  the spec is the normative contract.
