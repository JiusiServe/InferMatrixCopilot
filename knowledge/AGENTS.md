# Agent Instructions

Before doing any work, read `CLAUDE.md`. It is the repository-neutral routing and safety entrypoint.

Then follow the exact routing order in `CLAUDE.md`. A scenario that directly
links a guide does not require its topic index first. Use `repos/_index.md` only
when the canonical `repos/<slug>/` is not already verified; never invent a slug
from an upstream URL, display name, or local directory. Once a repository rule
directly identifies the owner, stop navigation. Never apply one repository's
rules, machine paths, credentials, remotes, or model assumptions to another.

Before adding or moving knowledge, read the short `CONTRIBUTING.md` entry and only the relevant topic it links, update the nearest `_index.md`, and run `python tools/check_knowledge_tree.py`.

Before committing or pushing, follow the target repository's own Git and identity rules. Do not inherit a commit identity, SSH host, remote, DCO requirement, or PR format from an unrelated repository entry.

Any PR review, including a request containing only a PR link, must follow the single-review Direct routing in `CLAUDE.md`. The host review resolves the pinned diff once, selects exact owner/model rule groups from the PR title and body, and reuses one evidence packet for correctness and design/subtraction checks. Do not start a second generic review or publish separate review comments. A bounded specialist is allowed only for a novel, contradictory, or still-uncovered high-risk contract; it extends the same evidence packet and returns to the host for one consolidated comment.

Within 60 seconds of starting a Direct review, update the host conversation with the pinned head SHA, current CI status, mergeability, and any early findings. Mark early findings as preliminary, continue the same review, and do not publish this progress update as a GitHub comment.

When the Direct MCP exposes `validate_direct_review`, call it before treating the review as complete or publishing the only final comment. Mark `subtraction_signal=none` when the diff does not add or expand a helper, class, fallback, compatibility branch, or public behavior; this needs no minimality proof. Mark `subtraction_signal=triggered` for those changes and then supply concrete subtraction items or a minimality proof. If it returns `partial_review`, reuse the existing evidence packet; do not invent deletion work just to satisfy the gate.
