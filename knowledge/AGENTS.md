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
