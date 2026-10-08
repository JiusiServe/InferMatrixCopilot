# Nightly knowledge maintenance

The opt-in maintenance lane challenges admitted knowledge against its immutable
original sources, including entries whose bytes and applicability pin have not
changed. It runs inside `kb serve` under the existing scheduler lease. Intake,
release sweeps, original verdicts, activation and reviewed receipts keep their
own histories. A resolution appends evidence; it does not rewrite an audit.

Maintenance is disabled by default. Before enabling `KB_MAINTENANCE_ENABLED=1`,
configure explicit model accounting in `KB_MAINTENANCE_COSTS`, the owner identity
in `KB_MAINTENANCE_OWNER`, and authenticated consumer transport. A subscription
entry specifies `{"kind":"subscription","accounted_usd":0.5}` per model label;
this is an accounting allowance, not a claimed provider invoice. API entries
require explicit prices and an enforceable transport upper bound; merely
setting prices cannot authorize an unbounded API call. The durable daily ceiling
is $50 with a $10 fairness reserve. `KB_MAINTENANCE_MAX_UNITS` bounds a cycle.

See [knowledge lifecycle layers](knowledge-lifecycle.md) for the relationship
between initialization, maintenance, the existing Copilot executor, and review
bot consumers. The internal `maintenance.plan/status/request/run_due` functions
are the entry points; policy admission and signed owner disposition live in
`maintenance_policy` and `maintenance_resolution`. They preserve the existing
CLI wire output, stores and publication authority. Extracted maintenance code
joins the implementation fingerprint: historical trial nights and calibration
remain recorded but cannot authorize a changed policy.

## Operator commands

Use an adapter repository ID for `--repo`, or `--all` for all eligible repositories:

```sh
infermatrix-copilot kb --state-dir /srv/kb maintain plan --all
infermatrix-copilot kb --state-dir /srv/kb maintain status --repo project
infermatrix-copilot kb --state-dir /srv/kb maintain run --all --request-id recovery-20261008
infermatrix-copilot kb --state-dir /srv/kb maintain run --all --request-id calibration-20261008 --calibrate
infermatrix-copilot kb --state-dir /srv/kb maintain run --all --request-id revocation-20261008 --drill
```

`plan` and `status` make no model calls. `run` only queues an immutable request;
the live scheduler performs it. Repeating the same request ID and inputs is
idempotent. Reusing that ID for different inputs fails. `--calibrate` and
`--drill` are mutually exclusive. Manual requests, owner resolutions,
calibrations and drills do not count as valid nightly runs.

A Shanghai 01:00 cycle pins its first snapshot and policy. Restart resumes that
cycle with those inputs. Reservations are charged before dispatch; a recovered
reservation cannot dispatch the same call again. Missing source pins or missing
original witnesses remain `unknown`; an execution error is recorded separately
from a factual contradiction. Coverage and per-repository fairness use the
frozen eligible denominator, not just the entries selected on a quiet night.
The nightly per-repository acceptance roster includes actual public upstream
repositories. An enabled cross-repository `general` slice remains in coverage
and owner follow-up; unavailable original evidence remains `unknown` rather than
being treated as a successful repository audit.

## Owner resolution and human cases

The resolver obtains the actual logged-in account with the read-only
`gh api user` endpoint. `KB_MAINTENANCE_OWNERS` is an explicit comma- or
whitespace-separated allowlist. A caller cannot supply an actor name. Resolution
requests use the existing service signing key and are verified again by the
lease-holding scheduler. The CLI never borrows or replaces the scheduler lease.

```sh
infermatrix-copilot kb --state-dir /srv/kb correction resolve \
  --id FINDING_ID --decision confirm --evidence @/work/owner-proof.json
infermatrix-copilot kb --state-dir /srv/kb correction resolve \
  --id FINDING_ID --decision dismiss --evidence '{"reason":"Requires narrower applicability evidence."}'
```

A confirmation supplies a nonempty reason, an explicit expected outcome and
original-source witness identities. For example:

```json
{
  "reason": "The pinned assignment sets a capacity of eight.",
  "expected": "contradicted",
  "witnesses": [{
    "repository": "org/project",
    "sha": "FULL_ORIGINAL_SOURCE_SHA",
    "path": "src/queue.py",
    "start_line": 10,
    "end_line": 15,
    "content_sha256": "SHA256_OF_EXACT_ORIGINAL_LINE_SPAN"
  }]
}
```

`expected` is `verified`, `contradicted` or `unknown`. The scheduler rereads
the committed source at the entry's own pin and checks every span/hash; caller
text or a `verified` boolean is not proof. Only a successful explicit confirmation
creates an owner-labeled, signed case under `eval/knowledge-maintenance/<repo>/cases/`
(or `KB_MAINTENANCE_CASES_DIR`). Dismissal appends a reason without creating a
case. `maintain status` includes owner-addressable observation IDs and outcomes,
including healthy `verified` observations. An owner may explicitly confirm a
healthy observation as an audit positive with `expected: verified`; its presence
alone creates neither a TODO nor a labeled case. Unlabeled candidates stay in service state and never become an oracle
automatically.

For a correction calibration case, explicitly supply `calibration_kind` as
`correction` and a `correction_oracle` containing `expected_gate` (`pass`, `fail`
or `human`). A passing oracle also supplies `expected_page_sha256`: the hash of
the intended corrected page with its `updated` metadata normalized back to the
original value. The resolver preserves that owner-supplied oracle; it never
invents a corrected page or expected result. Calibration readiness requires audit
positive/negative cases and passing/rejecting correction oracles.

## Consumer containment and rollout

`KB_CONTAINMENT_CONSUMERS` is the JSON roster of actual consumer IDs; an upstream
slug is not automatically a consumer ID. The existing owner SSH publisher
installs signed policy through the public SDK installer and returns authenticated
ACKs. Public consumer config, signed policy, policy high-water state, issuance
registry and protocol latch live outside physical paired releases. Installation
and review publication share a lock, so an ACK confirms old-generation writes
have drained. Heartbeats run every 60 seconds; stale policy/ACK, invalid
signature, roster mismatch or replay fails closed after rollout is enabled.

Direct records retrieval separately from context injection. Strict forwards its
provider-issued usage record. The shared final publication boundary checks
current availability under the installer lock. A hold retains the original
review and requests reassessment without publishing it or silently removing
claims that the model already consumed. Signed operational containment has its
own monotonic generation, independent of snapshot activation or pair rollback.

Durable correction uses the governed owner rule's existing `retire`/`replace`
operations and quality gates. Installing a local active knowledge snapshot does
not update the provider packaged in the bot; deploy a verified provider/bot pair.
Deploy guards refuse a protocol older than the shared durable latch, including
automatic health-check rollback. Source defaults remain disabled. The explicit
activation sequence below enables the protocol with an empty signed decision
list before trial; automatic corrective holds/publication stay gated by trial,
calibration and authenticated consumer readiness. This document does not enable
a deployment or restart a service.

## Authority, publisher and consumer configuration

Use durable paths outside snapshot directories and physical provider/bot releases.
The authority runs in the existing lease-holding knowledge service, with its
existing protected service key. These example paths are deployment choices:

```dotenv
KB_STATE_DIR=/srv/kb/shared/service
KB_SIGNING_KEY=/srv/kb/owner/service-private.pem
KB_PUBLISHER_PUBKEY=/srv/kb/owner/publisher-public.txt
KB_MAINTENANCE_ENABLED=1
KB_MAINTENANCE_OWNER=knowledge-maintainer
KB_MAINTENANCE_OWNERS=actual-owner-login
KB_MAINTENANCE_MAX_UNITS=20
KB_MAINTENANCE_CASES_DIR=/srv/kb/shared/maintenance-cases
KB_MAINTENANCE_REQUIRED_CHECKS=["suite"]
KB_CONTAINMENT_ENFORCE=1
KB_CONTAINMENT_POLICY_DIR=/srv/kb/shared/containment-authority
KB_CONTAINMENT_CONSUMERS=["native","reviewbot-vllm-omni","reviewbot-vllm-gr"]
KB_CONTAINMENT_CONSUMER_ID=native
KB_CONTAINMENT_PUBLIC_KEY=/srv/kb/owner/service-public.txt
KB_CONTAINMENT_STATE_DIR=/srv/kb/shared/containment-native
KB_CONTAINMENT_RELEASE_FILE=/opt/infermatrix-release/manifest.json
```

Also set `KB_MAINTENANCE_COSTS` to a JSON object keyed by the exact configured
generator/judge labels. For example, a service using the current default role
labels could explicitly account each subscription call at an owner-approved
allowance:

```json
{
  "claude-code:claude-opus-5-5": {"kind":"subscription","accounted_usd":0.5},
  "codex:gpt-6-sol:medium": {"kind":"subscription","accounted_usd":0.5}
}
```

This example is not provider pricing. Use the actual role labels and approved
accounting amounts; an absent entry blocks dispatch. Required CI names likewise
must match the repository's real checks.

The native SDK configuration above uses the authority's signed `policy.json`,
its pinned service public key and a separate durable consumer state directory.
Alternatively, `KB_CONTAINMENT_CONFIG` may supply the complete SDK JSON object
with `enabled`, `policy_path`, `public_keys`, `state_dir` and `consumer_id`.
Do not mix a different explicit config into requests. Use an actual regular
release manifest at `KB_CONTAINMENT_RELEASE_FILE`; the running scheduler hashes
its bytes and proves readiness under its own live lease. Without that file the
SDK falls back to loaded implementation/version hashes, which must be visible
as such in the operator's release inventory. Native readiness is produced by
`native_ack(rt)` on scheduler ticks, not by creating a JSON ACK by hand.

Each bot instance has its own existing `REVIEWBOT_STATE_DIR` and explicit consumer
identity. For example, the Omni instance uses:

```dotenv
KNOWLEDGE_MAINTENANCE_ENABLED=true
KNOWLEDGE_MAINTENANCE_CONSUMER_ID=reviewbot-vllm-omni
KNOWLEDGE_MAINTENANCE_POLICY_PATH=/srv/reviewbot/shared/state/knowledge-maintenance/policy.json
KNOWLEDGE_MAINTENANCE_STATE_DIR=/srv/reviewbot/shared/state/knowledge-maintenance
KNOWLEDGE_MAINTENANCE_PUBLIC_KEYS_FILE=/srv/reviewbot/owner/service-public-keys.json
```

The key file is a JSON list of public `ed25519 BASE64` strings. The GR instance
uses `reviewbot-vllm-gr` and its own shared state directory. Preserve the physical
paired release's existing `REVIEWBOT_RELEASE_MANIFEST`. Prepare each exact SDK
config with `omni-reviewbot knowledge-maintenance-config`; the generated
owner-only `config.json` is the publisher's `config_file`. A running watcher
refreshes it and writes `heartbeat.json` every 60 seconds. Readiness binds its
consumer, accepted generation/digest, protocol, actual manifest bytes and exact
config digest. Missing, stopped/stale, mismatched or disabled instances cannot
satisfy the runtime ACK barrier. A recently stopped watcher can retain readiness
only within the remaining heartbeat freshness window.

The existing owner publisher retains `KB_SERVICE_PUBKEY`, `KB_PUBLISHER_KEY`
and `KB_PUBLISHER_GIT_AUTHOR`. Set `KB_CONTAINMENT_TARGETS_JSON` to the exact
owner SSH targets, for example:

```json
{
  "reviewbot-vllm-omni": {
    "host":"owner@review-host",
    "python":"/srv/reviewbot/current/.venv/bin/python",
    "config_file":"/srv/reviewbot/shared/state/knowledge-maintenance/config.json",
    "release_file":"/srv/reviewbot/current/manifest.json"
  },
  "reviewbot-vllm-gr": {
    "host":"owner@review-host",
    "python":"/srv/reviewbot/current/.venv/bin/python",
    "config_file":"/srv/reviewbot/shared/state-vllm-gr/knowledge-maintenance/config.json",
    "release_file":"/srv/reviewbot/current/manifest.json"
  }
}
```

Every target has exactly `host`, `python`, `config_file` and `release_file`;
all paths are absolute. The interpreter must belong to the actual deployed
pair. Native is acknowledged locally by the running lease owner, so it needs
no duplicate bot SSH target. The publisher installs through the SDK fence,
waits for a matching heartbeat less than 180 seconds old and returns only
publisher-signed authenticated SSH metadata. It refreshes independently of
paid publishing work. A changed generation can therefore install successfully
while readiness stays pending until the next real heartbeat. Arbitrary JSON
or an installer-only receipt cannot satisfy this barrier.
The 180-second runtime window covers the watcher, publisher and service hops;
the signed policy still expires after 10 minutes, and merge authorizations have
their own shorter lifetime. Native protocol heartbeats run independently of paid
audit work while their separate ledger connection verifies the actual lease.

## Activation sequence

1. Deploy the reviewed protocol-capable provider and bot pair with source defaults
   disabled. Use a real merged provider SHA; do not pin an uncommitted change.
   Verify both physical release identities and preserve shared state on rollback.
2. Prepare the explicit roster, public trust, durable paths and authenticated
   transport. Start the signed protocol with an **empty decision list**, without
   enabling automatic maintenance corrections. Enable each actual consumer's
   SDK protocol configuration, prepare its owner config and verify real native
   and bot runtime ACKs. `kb serve` refreshes the authority's signed list; do not
   copy policy files around the installer fence or hand-create readiness files.
3. Enable the bounded nightly audit lane, retaining the configured lifecycle
   modes and shadow correction behavior during the trial. Verify source-pinned
   `unknown` behavior, explicit accounting, fair coverage, protected-entry owner
   routing and preservation of original outcomes. Install no live corrective
   holds on the strength of an uncalibrated trial finding.
4. Accumulate at least **seven consecutive effective actual nightly cycles**.
   Each cycle must include a real definitive original-source semantic review
   for **every eligible public repository**, under the same bound policy and
   frozen denominator. Empty/no-op runs, missing evidence, execution errors,
   budget-limited nights, manual requests and fabricated/backfilled dates do not
   count. No command can substitute seven immediate requests for seven nights.
5. Explicitly confirm real defect findings and healthy verified observation IDs
   with original-source evidence to build the
   audit positive/negative and correction passing/rejecting human corpus. Queue
   calibration and an isolated real-SDK revocation drill using distinct stable
   request IDs. Confirm current calibration, current roster ACKs and drill
   evidence; the isolated drill does not revoke any production knowledge.
6. Review the deployment configuration in a PR and explicitly authorize the
   relevant existing `auto_merge` lifecycle scope. The service never flips a
   repository's mode because a trial passes. Only the already configured
   publishing scope can proceed once all readiness requirements hold. A real
   correction then follows hold propagation, normal gates, exact reviewed head
   and CI, merge, active-byte verification and authenticated restoration ACKs.

Keep source updates, semantic audit coverage, proposed corrections, real merged
and active bytes, and consumer propagation visible separately in `maintain status`.
`no_code_update` refers to the observed immutable release baseline, with the
compared commits and scope included; it does not assert that unobserved upstream
main branches are unchanged. Repositories without a release observer retain
`not_observed` while their independent knowledge audits still run.
Missing releases, empty matching-tag results and resumed saved sweeps also retain
`not_observed`; the report includes the lookup status and any freshly observed
tag separately from the cached or resumed baseline.
An unregistered reader is outside isolation coverage. A policy or implementation
change invalidates readiness for the previous policy; failed owner requests are
retained and routed for follow-up rather than counted as successful nights.
