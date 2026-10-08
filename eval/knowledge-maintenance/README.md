# Human-confirmed maintenance calibration

This directory holds signed evaluation cases, outside served knowledge.
Cases live at `<adapter-repo-id>/cases/<case-id>.json`. Set
`KB_MAINTENANCE_CASES_DIR` to keep the evaluation corpus in durable service storage
when the installed package is read-only.

The owner queues `kb correction resolve --id FINDING_ID --decision confirm
--evidence @FILE`. The command authenticates the actual gh login against
`KB_MAINTENANCE_OWNERS`; the scheduler checks the signed request and immutable
original-source witnesses before creating a case. Every case has an explicit
human `expected` label (`verified`, `contradicted` or `unknown`), actor, immutable
unit, original outcome and verified source spans. Its envelope uses the existing
service key and the purpose `kb-maintenance-human-case`. No signing key belongs
in this directory or in a bot/reviewer installation.

`kb maintain status` lists observation IDs and outcomes, including healthy
`verified` audits. Explicit owner confirmation with `expected: verified` can
create a positive case from those actual audits; merely recording a healthy
observation creates no TODO, candidate or calibration oracle.

Audit cases use `calibration_kind: audit`. Correction cases explicitly use
`calibration_kind: correction` and an owner-supplied `correction_oracle` with
`expected_gate: pass|fail|human`. For `pass`, `expected_page_sha256` hashes the
intended corrected page after restoring the original `updated` value. Never
derive an oracle from the model being evaluated. Calibration needs both positive
and negative audit cases and both passing and rejecting correction cases.

Unlabeled candidates belong in service state at
`maintenance/regression-candidates/`; they are not cases. A dismissal never
creates a label. Neither resolutions nor calibration/drill requests count as
valid nightly audits. See the [operator guide](../../doc/architecture/knowledge-maintenance.md)
for evidence format, queue semantics and safe rollout.
