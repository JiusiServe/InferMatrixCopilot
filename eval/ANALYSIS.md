# Analysis — pure skill vs pure copilot vs copilot+skill (DeepSeek v4 pro)

Numbers in [RESULTS.md](./RESULTS.md); metric in [README.md](./README.md);
raw reviews/judgments in `raw/`.

## Headline

| arm | recall_GT | precision | **F1** | tokens/review | seconds |
|---|---|---|---|---|---|
| pure_copilot | 0.12 | 0.83 | **0.19** | ~10k | 52 |
| copilot_skill | 0.08 | 0.67 | **0.13** | ~25k | 65 |
| pure_skill | 0.00 | 0.67 | **0.00** | ~101k | 94 |

**On DeepSeek v4 pro, the copilot's plain structured pass wins** — it is also
10× cheaper than the skill agent. But the far more important result is the
absolute level: **every configuration scored low against what human
maintainers actually raised** (best recall 0.25 on any single PR).

## Why each arm scored what it did

1. **The human review value on these PRs came from knowledge no arm had.**
   The ground-truth issues required: product constraints ("action and sound
   cannot co-occur, simplify the branches" — #4678), project idioms ("call
   `get_ulysses_parallel_world_size()` directly" — #4678), cross-repo
   awareness (in-repo demo clients / docs broken by the SSE default — #4679),
   and live merge state (the file renamed on main → modify/delete conflict —
   #4679). A diff, however carefully read, doesn't contain these.

2. **pure_skill: the skill's discipline works against a weaker model.**
   The skill encodes maintainer ethos — "most PRs should get 1-5 short
   comments; some just get an empty APPROVE", "prioritize high-confidence
   findings over coverage theater". Claude-class models fill that confidence
   bar with real insight; DeepSeek, lacking it, obeys the brevity rule and
   converges to a confident APPROVE plus a style nit (#4678: full blocker-scan
   table, all PASS, verdict APPROVE — both human issues missed). Perfect
   precision when it spoke; zero recall. It spent its 100k tokens *verifying*
   its few claims against the repo (hence precision 1.0 where it commented),
   not discovering issues.

3. **pure_copilot: cheap concreteness pays.** The generic "meticulous
   reviewer, findings with file:line" prompt produces 2 concrete claims per PR
   with no brevity suppression — and twice one of them overlapped the top
   human issue (the stream=True SSE breaking change on #4679; the
   first-output-is-parent assumption area on #4849). Highest specificity
   (0.83) and lowest cost.

4. **copilot_skill: guidance redirected rather than sharpened.** With the
   skill checklist injected but no tools, DeepSeek leaned on the skill's
   process items ("run the affected e2e tests", "verify the benchmark") —
   actionable but not what the humans flagged. Its one partial hit (#4849) had
   perfect precision.

## Fairness caveats (beyond README's)

- The harness gave **no arm** `gh` access (only local diff/metadata/repo).
  The skill's own workflow starts with a `gh`-based gate check that would very
  likely have caught #4679's merge-conflict issue (gt4) natively — so the
  pure-skill arm is handicapped on exactly one GT issue by harness design.
- One PR (#4678) yielded zero recall for all arms — its ground truth is pure
  domain knowledge; it deflates all arms equally.
- n=3 PRs, self-model judge (blind, normalized findings). Directional only.

## What this suggests building

The three arms fail in complementary ways, which points at one configuration
none of them is yet: **copilot's structured evidence steps (fetch diff +
`gh pr checks`/mergeable state + changed-file blame/rename detection) →
skill checklist as the review rubric → repo read tools for verification.**
- The merge-conflict GT and CI-gate class of issues become deterministic
  *steps*, not model insight (the copilot already fails-closed this way
  elsewhere).
- The skill's checklists stay valuable as *what to look for*, with the
  brevity rule relaxed for weaker models (or the review model upgraded —
  rerunning this harness with a Claude-class model is one command).
- The copilot's cheap concrete pass remains the floor: never return an empty
  APPROVE without the evidence steps having run.
