# mcp_policy.py — compatibility boundary

<!-- verified-against: 2026-09-26 -->

This module preserves the existing imports for `PolicyError`,
`authorize_repo_path`, `enforce_mcp_policy`,
`enforce_strict_review_policy`, and `enforce_quality_review_policy`.
It contains no independent validation rules. The headless application owns
those rules in [`app/request_policy.md`](app/request_policy.md); SDK, MCP,
and reserved-run execution use the same implementation.

Do not add a second policy decision here. Existing callers importing this
module retain the same callable objects and exception type.
