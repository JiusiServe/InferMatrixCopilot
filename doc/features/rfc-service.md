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
