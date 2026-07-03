I've now read the full diff, the GLM-Image bridge reference, and the surrounding test files. Here's the review.

---

**BLOCKER scan:**

| Category | Result |
|----------|--------|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS — internal bridge API; matches GLM-Image contract |
| Test Coverage | PASS — three new tests + two updated |
| Documentation | PASS — docstring updated |
| Security | PASS |

---

The fix is straightforward and correct. The old code iterated over every source output (including CFG companions) and returned a list, which #4079's request-level batching contract rejects. The new code takes only `source_outputs[0]` (the parent) and returns a single `dict` or `None`, exactly matching the GLM-Image bridge pattern (`glm_image.py:230-239`).

The `prompt` list-to-scalar normalization (`prompt[0] if prompt else {}`) is identical to the GLM-Image reference, and the empty-list guard (`if not source_outputs: return None`) follows the same pattern used by `minicpmo_4_5_omni.py`, `step_audio2.py`, and `ming_tts.py`.

Tests are solid — three new tests cover the single-payload contract, parent-output selection with companions present, and the empty case. Existing tests are correctly updated for the new return type.

**Recommended verdict: APPROVE** (no inline comments needed).