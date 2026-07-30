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

Any PR review, including a request containing only a PR link, must follow the two-role review routing in `CLAUDE.md`. When multi-agent capability is available, the main agent must immediately spawn two independent read-only reviewers for a non-trivial PR: one correctness reviewer and one design/subtraction reviewer. Do not silently perform both roles in one agent. Wait for both results only within the review budget, then consolidate separate verdicts; if spawning is unavailable, state that limitation and run both roles sequentially.
