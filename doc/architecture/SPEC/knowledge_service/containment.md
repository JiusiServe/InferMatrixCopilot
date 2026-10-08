# knowledge_service/containment.py — contract

<!-- verified-against: 2026-10-08 -->

External opt-in containment protocol for immutable knowledge and issued review contexts. The module is inert by default and imports crypto only after enforcement is enabled.

A policy is an Ed25519 `kb-containment-policy` envelope with exact fields `schema_version`, `generation`, `issued_at`, `expires_at`, `consumers`, `decisions`. Its validity window is at most ten minutes. Each enrolled consumer has an owner-controlled durable highwater outside releases/snapshots; lower generations, conflicting generation content, older refreshes and forgotten original denied hashes refuse. Corrected bytes are explicitly approved while original bad hashes remain denied through rollback. Expiry never releases a hold.

Provider context issuance is held in a private local registry binding exact context digest, physical pinned knowledge root, snapshot/tree and document hashes. Public usage recording requires this issuance; availability rechecks bytes and current policy. Public receipts contain only portable unit/page identities and hashes, not private physical roots. Bounded usage export returns metadata for authenticated owner transport; successful delivery acknowledges queue entries without deleting original usage receipts.

The installer verifies pinned public keys and strict signature purpose, waits for the shared publication lock, validates highwater and atomically publishes the policy, then records an ACK. The ACK binds consumer/release/generation/digest/freshness plus observed current knowledge snapshot/tree and per-corrected-unit actual byte readiness. The publication guard covers the caller's final availability check and external write. Install and publication use the same lock; neither caller-supplied booleans nor missing usage provenance permit publication.

Focused offline tests: `test_kb_containment.py`, SDK, knowledge-view/routing and context regression suites. The signed offline acceptance drill is implemented separately in `kb_service/containment_drill.py`; it proves isolated SDK protocol behavior and never replaces production consumer ACKs.
