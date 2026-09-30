# Knowledge distillation benchmark (`kb-intake.draft`)

A paired, offline benchmark for the knowledge-intake drafting step: the same
merged upstream PRs, the same knowledge tree, the production quality gate as
the judge, and the meta-improvement engine's paired statistics. It exists to
answer one question with numbers instead of impressions: *does a cheaper
generator, under a given drafting strategy, produce knowledge the gate accepts
as often as the production generator does?*

Repo-invariant by construction: every input comes from a knowledge-service
state directory (`kb.db`, `changesets/`, `traces/`) and the adapter registry;
nothing here names an upstream repository.

## Pieces

| File | Role |
|---|---|
| `items.py` | Builds the item set. One item = one intake event (a merged PR) + the exact base commit its production draft used. The recorded generator call is the *incumbent* sample; the prompt is rebuilt from the base tree and must reproduce the recorded prompt byte for byte, which proves the sample is a draw of the current drafting code on that tree. |
| `harness.py` | `replay` the incumbent into the benchmark's own trace store; `run` a live arm (generator × `KB_DRAFT_STRATEGY`, N replicates); `judge` every unit with the production gate `kb_service.gate.run_gate` (L1, upstream fact attestation against a bare mirror, the pinned L2 judge per block with the per-rule evidence expansion, the owner-directory consistency check, protected rules and circuit breakers; a change set the gate fails lands nothing, so its blocks count as failed); `report` the paired deltas per metric with `improve.stats`; `show` a unit's operations and verdicts. |
| `experiment.py` | The engine's protocol: `gold` (the incumbent's gate-passing rules per item, versioned), `register` (hypothesis, metric, item set, both fingerprints — refused if the fingerprint diff is not exactly the declared overrides), `run` (arm and incumbent per item and replicate, scored through `improve.adapters.kb_intake`, adjudicated on the retained items). |

Units carry `context.workflow = kb-intake.draft`, the declared fingerprint
(`improve/workflows/kb-intake.yaml`) and one terminal `decision(type=draft_result)`,
so the engine's reader, Tier 1 lints and the adapter treat them like production
units.

## Metrics (per unit, paired per item)

* `net_pass` — passing rules minus failing rules; an empty draft is 0 (what the
  knowledge base gains from the draft). The pre-registered primary metric.
* `gate_score` — mean of pass=1 / unsure=.5 / fail=0 over the proposed rules.
* `gate_pass` — the gate's own verdict on the change set (1 = it would auto-merge; an empty draft is 1).
* `precision` — pass / (pass + fail), undefined when nothing was judged.
* `yield_pass`, `fail`, `human` (unsure), `empty`, `rejected` (schema/lifecycle
  repairs exhausted).
* `recall_gold` (experiment only) — coverage of the incumbent's gate-passing
  rules (their complete sections are the gold contracts), by a 3-vote `gold_match` judge.

## Running

```bash
S=/path/to/scratch   # a SNAPSHOT of the state dir; never the live one
python -m eval.kb_distill.items --state-dir $S/kbdata --git . --repo vllm-omni --out $S/items.json
H="python -m eval.kb_distill.harness --bench $S/bench --items $S/items.json --git . \
   --mirror $S/upstream/vllm-omni.git --state-dir $S/kbdata"
$H replay                                   # incumbent: the recorded production drafts
$H judge --arm opus-recorded
$H run --arm flash-v2 --generator zcode:GLM-5.3-Flash --strategy v2 --replicates 2 --workers 5
$H judge --arm flash-v2
$H report --arms flash-v2                   # paired vs opus-recorded
E="python -m eval.kb_distill.experiment --bench $S/bench --items $S/items.json --git . \
   --mirror $S/upstream/vllm-omni.git --state-dir $S/kbdata"
$E gold && $E register --metric net_pass_review --arm KB_GENERATOR=zcode:GLM-5.3-Flash \
   --arm KB_DRAFT_STRATEGY=v2 --incumbent KB_GENERATOR=claude-code:claude-opus-5-5 \
   --incumbent KB_DRAFT_STRATEGY=v1 --replicates 2 --min-effect 0.25
$E run exp-...
```

Judge calls go to `KB_JUDGE` (default `codex:gpt-6-sol:medium`, the production
gate's judge); generator calls to the arm's provider. The incumbent side of an
experiment carries its one recorded sample for every replicate (the hypothesis
text says so): it costs nothing and never mislabels a live re-draw as the
production sample.
