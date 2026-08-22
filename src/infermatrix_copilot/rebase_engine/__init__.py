"""Repo-neutral rebase engine — the merged rebase-agent machinery.

Ported piecewise from the external orchestrator (plan: PR0..PR7). Everything
here is repo-neutral: repo specifics (wheel index URLs, module path maps,
artifact patterns, inheritance maps) arrive as data from `adapters/<repo>/`.
"""
