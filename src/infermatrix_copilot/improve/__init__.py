"""The meta-improvement engine (design: ``meta-improvement-engine-design.md``).

A propose-only loop over the shared ``trace/1`` store: Tier 1 mechanical
forensics for any traced workflow, Tier 2 outcome-anchored loss attribution
for workflows that declare an outcome adapter, pre-registered paired
experiments in an isolated shadow scope, and proposals as issues. Nothing in
this package changes a production default; every change lands through a PR.

P0 (this package's first slice): workflow declarations (``enroll``), the
declared configuration fingerprint (``fingerprint``) and the trace/1 capture
context the executor binds around every step.
"""
