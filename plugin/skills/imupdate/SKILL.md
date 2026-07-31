---
name: imupdate
description: Audit a checked-out upstream repository and update InferMatrixCopilot's release-driven knowledge. Use when the user invokes /imupdate or $imupdate, asks to sync knowledge after an upstream release, compare vLLM-Omni tags or SHAs, or refresh the release baseline, model catalog, source maps, and manifests.
---

# InferMatrix update

Treat the user-facing argument as the local upstream Git checkout:

```text
/imupdate <upstream-repo> [target-tag-or-sha]
```

The installed InferMatrixCopilot root is:

```text
{{INFERMATRIX_COPILOT_ROOT}}
```

If that placeholder was not replaced, locate the checkout containing
`tools/audit_vllm_omni_release.py`; do not guess another project.

## Workflow

1. Verify the supplied path is a Git checkout. Do not fetch or checkout unless
   the user explicitly asks.
2. Read `adapters/vllm_omni/release_baseline.yaml`. Use its
   `upstream.audited_sha` as the old revision.
3. Use the optional target revision when supplied; otherwise use the upstream
   checkout's `HEAD`. Resolve both revisions to full SHAs.
4. Create a temporary JSON path and run the read-only audit in report mode:

   ```text
   python <infermatrix-root>/tools/audit_vllm_omni_release.py \
     --from <audited-sha> \
     --to <target-sha> \
     --repo <upstream-repo> \
     --mode report-only \
     --json-output <temporary-json>
   ```

5. Explain the registry, pipeline, deploy, path-routing, source, and pin drift.
   Read the relevant upstream diff before changing InferMatrixCopilot.
6. Update only facts proven by the report and source: the release baseline,
   model catalog, component source maps, pins, or adapter manifest. Never
   generate or rewrite owner rules automatically; report semantic-rule
   candidates for human review.
7. Run the same command with `--mode enforce`, then run:

   ```text
   python knowledge/tools/check_knowledge_tree.py
   python knowledge/tools/check_wiki_lint.py
   python -m pytest test/test_release_audit.py test/test_adapters.py \
     test/test_routing.py test/test_knowledge_source.py \
     test/test_skills_scope.py test/test_capabilities.py -q
   ```

8. Delete the temporary JSON. Return the old and new SHAs, structural deltas,
   files changed, validation results, and any unresolved drift.

The audit is evidence collection, not the updater. Codex performs the bounded
knowledge edits and must not commit, push, or open a PR unless asked.
