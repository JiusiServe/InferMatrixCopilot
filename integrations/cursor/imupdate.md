Update InferMatrixCopilot's release-driven knowledge from the local upstream
Git checkout supplied with this command.

InferMatrixCopilot root:

```text
{{INFERMATRIX_COPILOT_ROOT}}
```

Read `plugin/skills/imupdate/SKILL.md` from that root and follow its workflow.
Use the baseline's current audited SHA as `--from`, the supplied target or
upstream `HEAD` as `--to`, and run
`tools/audit_vllm_omni_release.py` in report-only mode before editing. Never
generate or rewrite owner rules automatically.
