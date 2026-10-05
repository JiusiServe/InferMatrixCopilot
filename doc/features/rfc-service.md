# Portable RFC service

The RFC service creates unpublished drafts, enrolls existing RFCs, tracks linked
implementation evidence, and records human acceptance decisions. It runs on a
local machine or behind an authenticated HTTP endpoint. Local Markdown,
GitHub issues and AtomGit issues use the same lifecycle. No served-repository
knowledge bundle or OpenAI API key is required to draft, import or synchronize.

`infermatrix-rfc` is the standalone command. `infermatrix-copilot rfc` forwards
the same arguments. Options such as `--state-dir`, `--config` and `--local`
precede the subcommand. The default state directory is
`~/.infermatrix-copilot/rfc`; `RFC_STATE_DIR` overrides it.

## Start locally

```sh
infermatrix-rfc --local bootstrap-admin --name Owner
infermatrix-rfc --local serve
```

Bootstrap prints the first administrator's user ID and token once. Store that
token in `RFC_TOKEN` for CLI/SDK use, or use it to sign in at
`http://127.0.0.1:8765`. A second bootstrap is refused. Tokens are user
credentials; provider credentials are separately supplied by the operator.

The server includes the web interface and a background reconciler. Its worker
checks queued operations every 30 seconds and refreshes enrolled RFC sources
when their last verification is at least one hour old by default. Administrators
can change source refresh frequency in the service settings. Use
`serve --interval 60` to change the worker tick, or `serve --no-worker` when a
separate worker owns reconciliation. Run `sync --once` for one local cycle or
`sync --watch` for a foreground worker. These commands work without systemd or
SSH. Package deployment wrappers around the foreground process when needed.

A non-loopback deployment requires `--public-url https://your-host.example` and
a TLS reverse proxy. Browser sessions stay on the configured origin and remember
the signed-in user for 30 days, including after closing the browser or restarting
the service. The persistent HttpOnly cookie contains only an opaque session
secret; personal tokens are not stored in browser storage. Logout, token
revocation, token expiration, or disabling the user invalidates access immediately.
Bind the
HTTP listener to an interface reachable by that proxy; the default listener is
loopback. Public URLs and provider endpoints belong in operator configuration,
not in user action payloads.

## Repositories and a draft

RFC details are a component-based workbench: Outcomes, goals and scope, interactive
roadmaps and work grouped by track, design, acceptance and evidence, then risks and
references. A shared browser projection parses heading tokens and original source
spans, recognizing common English and Chinese sections. Unclassified content and
historical snapshots remain available as collapsed supporting material. Task
descriptions appear under the matching stable feature ID, never as a second full
roadmap. Long sections render when expanded and unchanged sections are reused.

The top Outcome separates declared goals, implemented work and acceptance counts.
Its three recent verified results require passing criteria with non-stale evidence,
verification version and environment. Merged PRs establish implementation only;
performance prose and historical delivery snapshots remain labeled source claims.
Outcome actions locate the corresponding tasks or acceptance records. Authorized
users edit the complete source in a separate dialog, with revision conflict checks
and unsaved input preserved across close/reopen and work updates. API and storage
formats are unchanged.

The language switch provides English and Simplified Chinese views (`?lang=en`
or `?lang=zh`), remembering only the public locale preference. Interface and RFC
display strings are synchronized by GLM through the existing Zcode tool-less
adapter; source Markdown, identifiers, code, links, numbers, owners and acceptance
facts remain authoritative. Translated text stays in the service SQLite cache and
browser session memory. Queue execution and cache reads recheck current RFC/source
access; failed or stale translations never overwrite the source. Pending text
remains readable in its source language with a synchronization indicator.

Enable on an execution host with a logged-in Zcode CLI using provider config:

```json
{"translations":{"enabled":true,"backend":"zcode","model":"GLM-5.3-Flash","reasoning":"low","cli":"/path/to/zcode","timeout_seconds":180}}
```

The standalone worker translates changed text in batches, outside database
transactions and independently of tracking operations. It resumes expired leases
after restart and retries invalid/failed responses with backoff. The public UI
catalog contains only shipped interface literals; RFC translation maps require
the same authorization as the RFC and are filtered to currently visible strings.
The language parameter is additive; API responses retain original canonical text.

Draft previews, import previews, and individual content components display rendered
Markdown, including headings, lists, tables, links, and code blocks. The browser uses the
bundled markdown-it 15.0.2 parser (MIT, shipped with its license), with raw HTML
disabled and external image fetching disabled. Original Markdown remains intact
for editing, publication, and export.

Roadmaps retain the original left-to-right Mermaid flowchart format, track
headings, contextual milestones, and source relationships. Current tracking data
supplies work states, additional prerequisites, owners, and acceptance; explicit
dependency decisions override source relationships. Intentionally removed work stays removed,
and new tasks appear even when source diagrams have not been edited. Any number
of tracks is supported, including RFCs without source diagrams. Click or press
Enter/Space on a node to view PRs and evidence, claim work, update its state, or
record acceptance as permitted by the signed-in user's role. Each diagram has
zoom, reset, and SVG download controls; downloaded work nodes link back to the
authorized RFC task view. Green implementation nodes still show pending
acceptance until evidence or an explicit waiver satisfies its criteria.

The same-origin Mermaid 11.12.0 bundle is shipped with licenses and its pinned
dependency lockfile. It is built with esbuild from `mermaid/dist/mermaid.core.mjs`
using `--bundle --format=esm --minify --target=es2020 --legal-comments=linked`.
Source diagrams contribute only limited flowchart topology, never executable
callbacks, settings, or styles. Application event handlers supply node actions.
SVG styles come from the existing same-origin stylesheet, preserving the CSP.

The browser requests `view=summary` for RFC lists and `view=detail` for details
and mutation results. These are additive compact projections; the default SDK
responses and full exports remain unchanged. Suggestions are fetched from the
authorized `rfcs.suggestions` endpoint in pages of 50 instead of downloading the
whole discovery history. Permission filtering and counting use a transaction-local
source index, rebuilt on every request so revoked grants take effect immediately.

Generic static assets support gzip and ETag revalidation. Authenticated data and
the login shell remain `no-store`. Saves reuse the returned RFC projection,
preserve scroll, zoom, and unsaved prose edits, and update SVG labels and colors
without recomputing unchanged layouts. Unchanged Markdown DOM is reused; offscreen
prose and task sections defer layout. Background refresh skips unchanged content
and pauses during editing or an open task dialog. No private data is persisted in
browser storage, and signing out clears the in-memory view state.

Use `request ACTION --data FILE` for all versioned actions; `--data -` reads a
JSON object from stdin. It supports user administration, grants, tokens, RFCs,
operations and audit history without placing credentials in arguments.

Create a repository with `repositories.create`. For a local workspace:

```json
{"name":"Example RFCs","provider":"local"}
```

```sh
infermatrix-rfc request repositories.create --data repository.json
```

Use the returned repository `id` in a draft:

```json
{
  "repo_id":"REPOSITORY_ID",
  "title":"Introduce bounded caching",
  "body":"# RFC: Bounded caching\n\n## Problem\n\nRepeated work adds latency.\n\n## Non-goals\n\nNo distributed cache.\n\n## Alternatives\n\nCompare a local bounded cache with recomputation.\n\n#### F1. Cache implementation\n\nOwner: team-a\n\n#### F2. Integration validation\n\nDepends on: F1\n\n## Acceptance criteria\n\n- Bounded memory at the documented workload.\n- Cache invalidation verified against the pinned implementation.\n"
}
```

```sh
infermatrix-rfc draft --data draft.json
infermatrix-rfc status RFC_ID
infermatrix-rfc next RFC_ID
```

The service validates tracking structure and returns normalized features,
criteria and `content_digest`. Markdown feature headings and acceptance lists
are parsed; structured metadata is also accepted. Use the host model and the
`imdesign`/`imrfc` skills for repository investigation and prose authoring.
There is no implicit model call in these commands.

Import an existing RFC while preserving its body:

```sh
infermatrix-rfc import --repo REPOSITORY_ID --file RFC.md
```

Use `--data metadata.json` for extracted metadata and `--source source.json`
when the original provider/source should be retained. An imported draft remains
unpublished until publication is explicitly requested. Drafts follow repository
permissions; use `rfcs.acl` to narrow their visibility when needed.

## Publication and enrollment

Review the returned body and digest before queuing publication:

```sh
infermatrix-rfc publish RFC_ID --content-digest DIGEST --expected-revision REVISION --idempotency-key publish-rfc-v1 --post
infermatrix-rfc operation OPERATION_ID
```

`--post`, the current content digest and an idempotency key are required. The
digest covers the title and body; `--expected-revision` also guards changes to
the tracking structure since the preview. Successful publication enrolls the
RFC for recurring tracking. A
queued operation is not a successful upstream write. The worker rechecks the
actor's current permissions before applying it. Inspect `operation` until it
reaches a terminal state. Use the same key when retrying the same request; an
uncertain provider outcome requires reconciliation instead of a new blind write.
Provider responses supply the resulting source link/path.

For a failed or uncertain operation, its initiating maintainer or an
administrator can explicitly reauthorize recovery with their current credential:

```json
{"operation_id":"OPERATION_ID"}
```

```sh
infermatrix-rfc request operations.retry --data recovery.json
infermatrix-rfc operation OPERATION_ID
```

Uncertain publication is reconciled using the existing operation marker before
another write is attempted. Avoid creating a new operation to bypass recovery.

Enrollment enables recurring tracking. `enroll RFC_ID` uses its published
source. For an existing external issue, use `request rfcs.enroll` with:

```json
{
  "repo_id":"REPOSITORY_ID",
  "source":{"provider":"github","repository":"owner/repo","kind":"issue","identifier":"123","host":"github.com"},
  "scope":"Serving and cache implementation",
  "auto_add":false
}
```

For a local RFC, the source is:

```json
{"provider":"local","repository":"example","kind":"markdown","identifier":"rfcs/cache.md","path":"rfcs/cache.md"}
```

Local source and publication paths stay relative to the registered repository
root. Provider aliases do not make arbitrary filesystem paths writable.
Automatic additions are scope-bounded, attributed in audit history, and can be
turned off. Implementation status is derived from linked provider observations;
feature acceptance is an explicit human decision with evidence. Merging a PR
never automatically passes acceptance.

Use `sync --rfc RFC_ID` to queue a manual refresh. `status` includes freshness,
implementation, acceptance, blockers, suggestion counts and next actions. Failed
source reads leave unavailable/stale evidence visible instead of inventing
progress. Use `rfcs.work` to maintain work and attachments and `rfcs.decision`
for acceptance verdicts. `export RFC_ID --format markdown --out RFC-export.md`
or `--format json` produces a portable result.

Discovery reads updated issue/PR summaries since the last successful scan.
Linked PR progress uses authoritative reads, with shared links fetched once per
sync. A short cursor overlap keeps updates near scan boundaries discoverable.

Work changes, automatic associations, claims and acceptance decisions are
workspace tracking records shown in the web interface and JSON export. Markdown
export exchanges the RFC source body. Tracking changes do not automatically
rewrite the published issue body. File import and Markdown file export preserve
the source line endings, including Windows CRLF.

For compact progress through MCP or the versioned API, use `rfc_status` or
`rfcs.status`; they return suggestion counts with the source body and candidate
list omitted. Inspect candidates through `rfcs.suggestions` with
`{rfc_id, offset:0, limit:50}`. The page limit accepts 1–100, and optional `status`
and `query` filters apply before the visible total is counted. `rfcs.get` and
JSON export retain the full record; the SDK accepts JSON responses up to 16 MiB.

## Provider and state configuration

Set `RFC_CONFIG` or pass `--config providers.json` to select operator settings:

```json
{
  "roots":["/path/to/allowed/repositories"],
  "providers":{
    "github":{"token_env":"GITHUB_TOKEN"},
    "atomgit":{"token_env":"ATOMGIT_TOKEN","api_url":"https://api.atomgit.com/api/v5"}
  }
}
```

Register a local repository `root` within the configured allowed roots to use an
existing checkout. Local repositories without an external root use service-owned
files. Remote repositories use `external_name: "owner/repo"`. Provider API URLs
and token environment names are deployment settings; end users cannot redirect
provider credentials through action payloads. AtomGit capabilities reflect the
API configured by the operator.

The SQLite state holds hashed user credentials, repository/RFC grants, source
snapshots, operations and audit records. The application enforces permissions for
HTTP, CLI, SDK, background execution and MCP alike. Use `users.*`, `grants.set`,
`tokens.*` and `rfcs.acl` actions to manage access. Disabling users, revoking tokens
or removing grants also affects queued work when the worker reauthorizes it.
Recurring enrollment uses the credential that authorized it. If that credential
expires or loses access, refreshes pause; a maintainer must enroll the RFC again
with a current credential to restore tracking. `status` reports
`sync_status: "requires_reauthorization"` and a next action while authorization
is unavailable.

Administrators can read `service.settings` and update `service.configure` through
the web service settings panel or the versioned request command:

```json
{"sync_seconds":3600,"default_max_auto_additions":5}
```

```sh
infermatrix-rfc request service.settings
infermatrix-rfc request service.configure --data service-settings.json
```

Source refresh frequency accepts 60–86400 seconds; the default automatic addition
limit for new RFCs accepts 0–100. Each RFC retains its own scope and addition
policy. Changing source refresh frequency does not change the worker tick.
Provider credentials, filesystem roots and public endpoints remain operator
configuration.

## Private RFC chat and reviewed edits

The RFC workbench includes a collapsible right-hand Zcode Agent panel, with a
full-screen panel on phones. Sections, roadmap nodes, tasks and criteria provide
discussion entries using stable identifiers and original source line ranges.
The same panel moves into the source editor; unsaved manual edits are included
in its context and in the complete candidate reviewed before saving. Page refresh,
task updates and language changes preserve the conversation and editor input.
Conversations are private to the authenticated user, repository and RFC, survive
sign-out and restart, and can be deleted by their owner. Readers may discuss;
editing uses the existing contributor/maintainer rules.

Enable the isolated GLM adapter on a host with a logged-in Zcode CLI:

```json
{"chat":{"enabled":true,"backend":"zcode","model":"GLM-5.3-Flash","reasoning":"low","cli":"/path/to/zcode","timeout_seconds":180}}
```

`serve` runs two independent chat workers, separate from source reconciliation
and translation. Each conversation runs one round at a time. A round makes at
most four model calls within 180 seconds; model I/O never holds a database
transaction. With `serve --no-worker`, use `chat-worker --watch` in a separate
process, or `chat-worker --once` for a single cycle. Worker claims, execution
leases, cancellation and authorization checks fence late or revoked results.
The UI polls normalized job status once a second and displays the final reply
only after validation. Recent context is bounded to 20 messages and a character
budget; a truncation notice is included when history is shortened. Platform
credentials and unrestricted repository tools are never given to the model.

The edit flow is **chat → proposal → source and plan diff → confirm once**.
The service validates raw-text replacement anchors, stable task IDs, dependencies,
current permissions and source/editor versions. A proposal cannot invent merged
implementation, passing evidence, acceptance or waivers. Diff text, conversation
history and source Markdown are not passed through page translation. Answers use
the send-time language; source edits preserve its language unless translation is
explicitly requested. A changed editor or RFC requires a new proposal/review.

Confirmation saves the exact complete candidate, including manual edits, and
creates a durable `rfcs.update_source` operation for an existing source. Drafts
without a source remain unpublished. Task/acceptance metadata stays in the
workspace; only source title/body is written upstream. The source indicator
separates saved, waiting to synchronize, synchronized and source conflict.
Pending or failed writeback protects the saved body from background refresh,
while linked PR observations can still update. Execution rechecks permission and
source version, then reads back the write; uncertain results are reconciled before
retry. Provider APIs do not supply an atomic compare-and-swap guarantee. Known
conflicts preserve the candidate and require a fresh review.

All transports use the same actions under `/api/v1/actions/`: `chat.create`,
`chat.list`, `chat.get`, `chat.send`, `chat.events`, `chat.cancel`, `chat.retry`,
`chat.delete`, and `chat.proposals.preview/apply/reject`. Sending returns a job ID
immediately. Messages and events are paginated; every read rechecks thread
ownership and current RFC/source access. Audit records contain operation identity
and status, never private transcript or raw model events.

```python
from infermatrix_copilot.sdk.v1 import RFCClient

client = RFCClient.from_env()
thread = client.chat_create("RFC_ID")["thread"]
queued = client.chat_send(thread["id"], "Explain the remaining work",
                          idempotency_key="discuss-once", language="en")
print(client.chat_events(thread["id"]))
# After a validated proposal exists, review it before explicit confirmation:
# preview = client.chat_preview("PROPOSAL_ID")
# client.chat_apply("PROPOSAL_ID", candidate_digest=preview["candidate_digest"],
#                   reason=preview["proposal"]["reason"])
```

CLI and Copilot MCP use `request chat.send --data FILE` and
`rfc_request("chat.send", payload)` with the host's configured user credential.
They do not bypass review, authorize model tools independently, or choose another
workspace when the configured remote is unavailable.

Before deployment, back up the installed program, operator configuration and
SQLite with its backup API. Before rollback, stop all workers and inspect in-flight
source operations; preserve the new chat tables and candidate bodies. Never
restore an older database blindly after an upstream write.

## SDK, MCP and remote workspaces

```python
from infermatrix_copilot.sdk.v1 import RFCClient

client = RFCClient.from_env()
print(client.capabilities())
print(client.list_rfcs())
print(client.get("RFC_ID"))
print(client.status("RFC_ID"))
print(client.suggestions("RFC_ID", offset=0, limit=50))
```

`RFCClient(state_dir=..., token=...)` chooses local execution;
`RFCClient(service_url=..., token=...)` chooses HTTP. The versioned interface is
`GET /api/v1/capabilities` and `POST /api/v1/actions/ACTION`, authenticated with a
Bearer token. SDK imports do not start a server, load model configuration or
initialize local state. The RFC contract version is independent of review APIs.
External service URLs require HTTPS; HTTP is accepted only for loopback development.

Set `RFC_SERVICE_URL` and `RFC_TOKEN` to use a hosted workspace. A remote failure
returns an error and never switches to a new local database. `--local` explicitly
selects local state even when the remote environment variable is set.

The default Copilot MCP exposes `rfc_capabilities`, `rfc_status(rfc_id)` and
`rfc_request(action, payload)`. Their target and credential come from the host's
`RFC_SERVICE_URL`/`RFC_STATE_DIR` and `RFC_TOKEN`. Tool callers cannot supply a
URL or token parameter. The bundled `imrfc` skill guides host-model drafting,
publication previews and evidence-based progress tracking. The existing skill
installer discovers it automatically; no global skill installation is needed
when reviewing this repository change.
The wheel also carries the bundled host skills under the package resource
`_runtime/host_skills`, including `imrfc` and `imdesign`. Installing the wheel
does not modify a host application's skill directory; use the repository's
`scripts/install_mcp.py` when configuring that host.

Personal-Agent remains a usable existing deployment. The portable service does
not take over its schedule or state automatically; migration is an explicit
operator action and should be verified before enabling replacement schedules.

## Users and acceptance evidence

Administrators create users with `users.create` and `{name, admin:false}`, then
grant `reader`, `contributor` or `maintainer` access with
`grants.set` and `{repo_id, user_id, role}`. An empty role removes the grant.
`tokens.create` accepts `{user_id, expires_days:30}` and returns the token once;
`tokens.list` returns metadata, and `tokens.revoke` takes `{token_id}`.
Repository grants bound any narrower RFC ACL. Contributors can record work and
verification evidence; maintainers own structural changes and acceptance verdicts.

A criterion decision uses a criterion ID returned by `status`:

```json
{
  "rfc_id":"RFC_ID",
  "kind":"criterion",
  "criterion_id":"CRITERION_ID",
  "verdict":"passing",
  "evidence":{"revision":"PINNED_SHA","environment":"Linux CPU, Python 3.11","result":"Acceptance workload passed"},
  "reason":"The recorded workload meets the agreed criterion."
}
```

```sh
infermatrix-rfc request rfcs.decision --data decision.json
```

Verdicts are `pending`, `passing`, `failing` or `waived`. Passing requires current
evidence; waivers require a reason. `rfcs.work` takes an `op` (`add`, `update`,
`drop`, `restore`) and `feature_id`/`feature` values. Preserve stable feature IDs;
structural changes and owner changes need a maintainer and explicit reason.

## Personal-Agent migration

Export or copy the existing tracking artifacts into a local source directory,
then compare them against an enrolled RFC in the target service:

```sh
infermatrix-rfc --local migrate-personal-agent --source-dir LEGACY_EXPORT --repo-id REPOSITORY_ID --rfc-id RFC_ID
infermatrix-rfc --local migrate-personal-agent --source-dir LEGACY_EXPORT --repo-id REPOSITORY_ID --rfc-id RFC_ID --apply
```

The command authenticates `RFC_TOKEN` and checks access to the destination. The
first invocation reports the comparison without applying it. The applied import
retains a source namespace and backup information so operators can verify counts
and identities before changing schedules. Keep the existing Personal-Agent job
as the active writer until the comparison is verified; select one writer before
enabling the replacement service's recurring sync.
