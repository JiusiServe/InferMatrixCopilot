# review/change_set.py —— 规范

<!-- verified-against: 2026-09-26 -->

`ChangeSet.capture(repo, base_ref)` freezes the committed range that a PR
mutation workflow intends to push. The base must be explicit and resolve to a
commit. `HEAD` is resolved once; the returned `(base_sha, head_sha, diff_text)`
is immutable. The diff includes binary changes and disables external diff
drivers. A tracked dirty checkout, unresolved ref, or failed diff raises
`ChangeSetError` so the pre-push review blocks rather than approving an
uninspected change. Untracked files are not part of a commit and are excluded.

The patch gate rejects an empty committed range and diffs over its reviewer
budget, then records approval for the exact base and head only after a passing
review. `ci.push` compares the approved head with the current checkout head
before any PR debug/rebase push. A later commit requires another review.
