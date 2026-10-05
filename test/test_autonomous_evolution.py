"""Autonomous objectives, deployed bytes, and recovery without judges/annotations."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import yaml

from test_evolution import bench, Model
from infermatrix_copilot.improve import artifacts, objectives, runtime, evolution
from infermatrix_copilot.improve.isolation import SandboxUnavailable
from infermatrix_copilot.config import Settings


class ObjectiveWorker:
    def __init__(self): self.calls = []; self.bad = False; self.interrupt = False
    def check(self): return {'ready': True, 'reason': ''}
    def run(self, source, payload, work, **kwargs):
        self.calls.append(payload)
        assert 'objective' not in payload['input'] if payload['mode'] != 'tests' else True
        meta = artifacts.verify(source)
        arm = '# improved' in (source / 'src/infermatrix_copilot/improve/forensics.py').read_text()
        result = {'source_sha': meta['tree_sha'], 'package_path': '/candidate/src/infermatrix_copilot/__init__.py', '_broker_calls': 1}
        if payload['mode'] == 'tests': return {**result, 'rc': 0}
        if self.interrupt:
            self.interrupt = False
            raise KeyboardInterrupt()
        if self.bad: return {**result, 'execution_error': 'injected failure'}
        data = payload['input']
        if payload['driver'] == 'objective-lints': return {**result, 'findings': []}
        stage, evidence = 'S0', []
        for record in data['records']:
            kind = record.get('result', {}).get('type')
            if record.get('result', {}).get('stop_reason') == 'max_tokens': stage, evidence = 'S4', [record['id']]
            if kind == 'cap': stage, evidence = 'S3', [record['id']]
            if kind == 'planner_zero_output': stage, evidence = 'S7', [record['id']]
        if not arm: stage, evidence = 'S0', []
        return {**result, 'scores': {'contract_success': 999}, 'attributions': [dict(gold_id=gid, stage=stage, evidence=evidence, disputed=False) for gid in data['cells']]}


@pytest.fixture
def autonomous(bench):
    st, store, _, model = bench()
    st = st.model_copy(update={'improve_evaluation_mode': 'objective', 'improve_promotion_mode': 'pr', 'improve_judge': '', 'performance_model': ''})
    path = Path(st.improve_workflows_dirs) / 'workflow.yaml'
    doc = yaml.safe_load(path.read_text()); doc['objective'] = {'min_effect': .5, 'prior_sd': .15}
    path.write_text(yaml.safe_dump(doc))
    root = objectives.data_root(st) / objectives.ENGINE
    (root / 'dataset.json').unlink()
    objectives.prepare(st, store, workflow=objectives.ENGINE)
    manifest = json.loads((root / 'dataset.json').read_text())
    # A deterministic positive cohort for the large-effect integration case;
    # negative controls are independently asserted below.
    manifest['items'] = [r for r in manifest['items'] if not r['objective'].get('negative')]
    artifacts.atomic_json(root / 'dataset.json', manifest)
    return st, store, model, ObjectiveWorker()


def test_default_is_one_model_objective_and_automatic():
    st = Settings(_env_file=None, eco_model='claude-sonnet-5', performance_model='')
    assert st.improve_evaluation_mode == 'objective' and st.improve_promotion_mode == 'automatic'
    single = objectives.execution_settings(st)
    assert single.tier_target('eco').model == single.tier_target('performance').model == 'claude-sonnet-5'


def test_readiness_has_no_human_gold_or_judge_requirement(autonomous):
    st, store, _, worker = autonomous
    report = evolution.check(st, store, objectives.ENGINE, sandbox=worker)
    assert report['ready'], report
    assert report['evaluation_mode'] == 'objective'
    assert not any('human' in r or 'gold' in r or 'judge' in r for r in report['reasons'])
    assert not report['semantic_quality_claim']


@pytest.mark.parametrize('fault', objectives.FAULTS)
def test_causal_witness_scores_complete_denominator_and_negative_controls(fault):
    data, clean, witness = objectives.fault_case('abcdef0123456789', fault)
    row = {'payload': data, 'objective': witness, 'origin': {'kind': 'controlled-intervention'}}
    correct = {'attributions': [{'gold_id': witness['cell'], 'stage': witness['stage'], 'evidence': [witness['evidence']]}]}
    assert objectives.score('meta', row, correct) == 1
    assert objectives.score('meta', row, {'scores': {'accuracy': 1}, 'attributions': []}) == 0
    wrong = copy.deepcopy(correct); wrong['attributions'][0]['evidence'] = ['not-in-trace']
    assert objectives.score('meta', row, wrong) == 0
    negative = {'payload': clean, 'objective': {'negative': True}, 'origin': row['origin']}
    assert objectives.score('meta', negative, {'attributions': []}) == 1
    assert objectives.score('meta', negative, correct) == 0


def test_generate_evaluate_with_one_model_no_judge_no_annotations(autonomous):
    st, store, model, worker = autonomous
    result = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert result['state'] == 'pr-ready', result
    assert result['evaluation']['promotable'] and result['evaluation']['protocol'] == objectives.PROTOCOL
    assert result['evaluation']['replicates'] == 3
    assert result['evaluation']['n_items'] >= 8
    assert len(model.calls) == 1
    assert model.calls[0]['model'] == st.eco_model
    assert all(p.get('settings', {}).get('performance_model') == st.eco_model for p in worker.calls)
    assert not result['evaluation']['semantic_quality_claim']
    path = evolution.directory(st) / 'candidates' / result['id'] / 'PR.md'
    assert path.exists()


def verified(autonomous):
    st, store, model, worker = autonomous
    c = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert c['state'] == 'pr-ready', c
    return st.model_copy(update={'improve_promotion_mode': 'automatic'}), store, model, worker, c


def test_automatic_activation_reuses_exact_artifact_without_pr(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    assert c['state'] == 'canary'
    entry = runtime.active(st)
    assert entry['source_sha'] == c['artifact']['tree_sha'] and not c.get('pr')
    assert runtime.baseline(st, c['workflow'], Path(st.improve_ledger_dir) / 'next-base')['tree_sha'] == entry['source_sha']
    runtime.promote(st, store, c, sandbox=worker)
    assert runtime.active(st)['candidate'] == c['id']
    assert len(model.calls) == 1


def test_tampered_verdict_cannot_activate(autonomous):
    st, store, _, worker, c = verified(autonomous)
    c['evaluation']['mean'] = 900
    with pytest.raises(artifacts.ArtifactError, match='persisted controller verdict'):
        runtime.promote(st, store, c, sandbox=worker)
    assert not runtime.active(st)


def test_live_failure_restores_exact_previous_bytes(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    previous = runtime.active(st)['previous']['source_sha']
    data, _, _ = objectives.fault_case('abcdef0123456789', 'ceiling')
    worker.bad = True
    with pytest.raises(artifacts.ArtifactError): runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    assert runtime.active(st)['source_sha'] == previous
    assert evolution.candidate(st, c['id'])['state'] == 'rolled-back'


def test_merged_or_activated_does_not_attest_deployment(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    assert not c.get('deployed_record')
    data, _, _ = objectives.fault_case('abcdef0123456789', 'ceiling')
    runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    updated = evolution.candidate(st, c['id'])
    record = store.get(updated['deployed_record'])
    assert record['result']['source_sha'] == c['artifact']['tree_sha']
    assert record['result']['pair']['previous_calls'] == 1


def test_canary_timeout_rolls_back_without_human(autonomous):
    st, store, _, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    runtime.sync(st, store, now=c['activated_at'] + 8 * 86400)
    assert evolution.candidate(st, c['id'])['state'] == 'rolled-back'


def test_eight_distinct_verified_production_pairs_retain_release(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    # Deterministic clock removes process timing noise from this retention test.
    from unittest.mock import patch
    counter = iter(range(10000))
    with patch.object(runtime.time, 'monotonic', side_effect=lambda: next(counter)):
        for i in range(8):
            data, _, _ = objectives.fault_case(f'{i:016x}', 'discard')
            runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    runtime.sync(st, store)
    updated = evolution.candidate(st, c['id'])
    assert updated['state'] == 'retained', updated
    assert updated['observation']['resource_gain']['n_items'] == 8


def test_interrupted_paid_pair_is_excluded_and_never_replayed(autonomous):
    st, store, model, worker = autonomous
    worker.interrupt = True
    with pytest.raises(KeyboardInterrupt): evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    result = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert len(model.calls) == 1
    exp = json.loads((evolution.directory(st) / 'candidates' / result['id'] / 'objective.json').read_text())
    assert any(r['state'] == 'excluded' for r in exp['progress'].values())
    assert not result['evaluation']['promotable']


def test_trace_inputs_are_automatically_frozen_and_clustered(tmp_path):
    from infermatrix_copilot.trace_store import TraceStore
    st = Settings(_env_file=None, improve_ledger_dir=str(tmp_path / 'ledger'))
    store = TraceStore(tmp_path / 'trace')
    for _ in range(3): objectives.capture(store, 'kb-intake.draft', 'repo#1', {'files': {}, 'repo': 'repo'})
    assert objectives.collect(st, store, 'kb-intake.draft') == 1
    assert len(objectives.rows(st, 'kb-intake.draft')) == 1
    row = objectives.rows(st, 'kb-intake.draft')[0]
    (objectives.data_root(st) / 'kb-intake.draft' / row['input']).write_text('{}')
    with pytest.raises(artifacts.ArtifactError): objectives.rows(st, 'kb-intake.draft')


def test_empty_kb_is_not_rewarded_as_an_error():
    row = {'payload': {'files': {}, 'repo_dir': 'repos/demo', 'release': 'v1', 'today': '2026-10-04'}}
    assert objectives.score('kb-intake', row, {'operations': [], 'rejected': False}) == 1
    assert objectives.score('kb-intake', row, {'operations': [], 'rejected': True}) == 0


def test_resource_change_preserves_carried_findings_and_verdict():
    original = {'review_comments': [], 'review_verdict': 'APPROVE', 'review_recheck_missing': ['id']}
    modified = {**original, 'review_recheck_missing': []}
    assert objectives.canonical('pr-review', original) != objectives.canonical('pr-review', modified)


def test_kill_switch_prevents_live_candidate_execution(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    calls = len(worker.calls)
    assert runtime.execute(st.model_copy(update={'improve_enabled': False}), store, c['workflow'], {}, model, sandbox=worker) is None
    assert len(worker.calls) == calls


def test_injected_lint_faults_and_clean_controls_are_real(tmp_path):
    from infermatrix_copilot.trace_store import TraceStore
    from infermatrix_copilot.improve.meta import _unit_from
    from infermatrix_copilot.improve.lints import run_lints, Baseline
    for fault in objectives.FAULTS:
        positive, clean, witness = objectives.fault_case('abcdef0123456789', fault)
        store = TraceStore(tmp_path / fault)
        for ref, text in positive['blobs'].items(): assert store.put_blob(text) == ref
        findings = run_lints(_unit_from(positive['records']), store, Baseline(settings=Settings(_env_file=None)))
        assert witness['lint'] in {f.lint for f in findings}
        assert not run_lints(_unit_from(clean['records']), store, Baseline(settings=Settings(_env_file=None)))


def test_three_objective_workflows_need_no_labels_or_judge(bench):
    for driver, workflow in [('pr-review', 'pr-review.agent.review_diff'), ('kb-intake', 'kb-intake.draft')]:
        st, store, _, model = bench(driver, workflow)
        st = st.model_copy(update={'improve_evaluation_mode': 'objective', 'improve_promotion_mode': 'pr', 'improve_judge': '', 'performance_model': ''})
        decl_path = Path(st.improve_workflows_dirs) / 'workflow.yaml'
        doc = yaml.safe_load(decl_path.read_text()); doc['objective'] = {'min_effect': .5, 'prior_sd': .15}; decl_path.write_text(yaml.safe_dump(doc))
        manifest_path = objectives.data_root(st) / workflow / 'dataset.json'
        manifest = json.loads(manifest_path.read_text())
        for row in manifest['items']:
            for key in ('labels', 'label_source', 'gold'): row.pop(key, None)
        artifacts.atomic_json(manifest_path, manifest)
        class Worker:
            def check(self): return {'ready': True, 'reason': ''}
            def run(self, source, payload, work, **kwargs):
                meta = artifacts.verify(source)
                improved = '# improved' in next((source / 'src').rglob('*.py')).read_text()
                result = {'source_sha': meta['tree_sha'], '_broker_calls': 1}
                if payload['mode'] == 'tests': return {**result, 'rc': 0}
                if driver == 'pr-review': return {**result, 'review_text': 'complete report' if improved else '', 'review_comments': []}
                return {**result, 'operations': [], 'rejected': not improved}
        result = evolution.run(st, store, workflow=workflow, llm=model, sandbox=Worker())
        assert result['state'] == 'pr-ready', result
        assert result['evaluation']['promotable'] and not result['evaluation']['semantic_quality_claim']
        assert len(model.calls) == 1


def test_active_source_tampering_rolls_back_without_running_it(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    root = Path(runtime.active(st)['artifact'])
    (root / 'src/infermatrix_copilot/improve/forensics.py').write_text('tampered')
    calls = len(worker.calls)
    data, _, _ = objectives.fault_case('abcdef0123456789', 'ceiling')
    with pytest.raises(artifacts.ArtifactError): runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    assert len(worker.calls) == calls
    assert evolution.candidate(st, c['id'])['state'] == 'rolled-back'


def test_rollback_failure_disables_release_instead_of_running_unverified_bytes(autonomous):
    st, store, _, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    previous = Path(runtime.active(st)['previous']['artifact'])
    (previous / 'src/infermatrix_copilot/improve/forensics.py').write_text('corrupt baseline')
    runtime.rollback(st, store, c, 'regression')
    assert runtime.active(st)['disabled'] and c['state'] == 'rollback-blocked'


def test_isolation_loss_blocks_automatic_promotion(autonomous):
    st, store, _, worker, c = verified(autonomous)
    worker.check = lambda: {'ready': False, 'reason': 'user namespaces disabled'}
    runtime.promote(st, store, c, sandbox=worker)
    assert c['state'] == 'deferred' and not runtime.active(st)


def test_better_model_override_is_rejected_before_evaluation(autonomous):
    st, store, model, worker = autonomous
    model.proposal['overrides'] = {'PERFORMANCE_MODEL': 'stronger-model'}
    result = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert result['state'] == 'rejected' and len(worker.calls) == 0


def test_canary_production_resource_regression_is_automatically_reverted(autonomous):
    st, store, _, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    c['production_records'] = []
    for i in range(8):
        r = store.append('decision', result={'type': 'runtime_result', 'source_sha': c['artifact']['tree_sha'], 'contract_success': 1,
             'pair': {'item': str(i), 'arm_usd': 2, 'previous_usd': 1, 'arm_seconds': 1, 'previous_seconds': 1}})
        c['production_records'].append(r['id'])
    evolution.save(st, c, store)
    runtime.sync(st, store)
    assert evolution.candidate(st, c['id'])['state'] == 'rolled-back'


def test_retained_release_keeps_bounded_weekly_shadow_comparison(autonomous):
    from unittest.mock import patch
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    c.update(state='retained', retained_at=c['activated_at'])
    evolution.save(st, c, store)
    counter = iter(range(10000))
    before = len(worker.calls)
    with patch.object(runtime.time, 'monotonic', side_effect=lambda: next(counter)):
        for i in range(10):
            data, _, _ = objectives.fault_case(f'{i:016x}', 'discard')
            runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    assert len(worker.calls) - before == 18  # ten live calls + eight shadow pairs
    updated = evolution.candidate(st, c['id'])
    assert len(updated['monitor_records']) == 8
    runtime.sync(st, store)
    assert evolution.candidate(st, c['id'])['state'] == 'retained'


def test_activation_intent_recovers_before_registry_write(autonomous):
    st, store, _, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    previous = runtime.active(st)['previous']
    artifacts.atomic_json(runtime.registry(st), previous)
    runtime.sync(st, store)
    assert evolution.candidate(st, c['id'])['state'] == 'pr-ready'
    runtime.promote(st, store, evolution.candidate(st, c['id']), sandbox=worker)
    assert runtime.active(st)['candidate'] == c['id']


def test_rollback_intent_recovers_after_registry_restore(autonomous):
    st, store, _, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    previous = runtime.active(st)['previous']
    c['rollback_pending'] = 'interrupted restore'
    evolution.save(st, c, store)
    artifacts.atomic_json(runtime.registry(st), previous)
    runtime.sync(st, store)
    assert evolution.candidate(st, c['id'])['state'] == 'rolled-back'


def test_underpowered_resume_uses_fresh_scenarios_without_regeneration(autonomous):
    st, store, model, worker = autonomous
    worker.interrupt = True
    with pytest.raises(KeyboardInterrupt): evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    first = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert first['evaluation']['blocking'] == 'data'
    first_ids = set(first['evaluation']['snapshot_versions'])
    objectives.prepare(st, store, workflow=objectives.ENGINE)
    manifest_path = objectives.data_root(st) / objectives.ENGINE / 'dataset.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['items'] = [r for r in manifest['items'] if not r['objective'].get('negative')]
    artifacts.atomic_json(manifest_path, manifest)
    second = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert second['state'] == 'pr-ready' and len(model.calls) == 1
    assert not first_ids.intersection(second['evaluation']['snapshot_versions'])
    assert len(second['objective_trials']) == 1


def test_mixed_routes_are_explicitly_deferred(autonomous):
    st, store, model, worker = autonomous
    st = st.model_copy(update={'review_lens_backends': {'correctness': 'harness'}})
    result = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert result['state'] == 'deferred' and not worker.calls and not model.calls


def test_objective_score_rejects_extra_predictions_and_report_loss():
    data, _, witness = objectives.fault_case('abcdef0123456789', 'ceiling')
    row = {'payload': data, 'objective': witness, 'origin': {'kind': 'controlled-intervention'}}
    a = {'gold_id': witness['cell'], 'stage': witness['stage'], 'evidence': [witness['evidence']]}
    assert objectives.score('meta', row, {'attributions': [a, {**a, 'gold_id': 'extra'}]}) == 0
    base = {'review_text': 'A supported finding', 'review_comments': []}
    assert objectives.canonical('pr-review', base) != objectives.canonical('pr-review', {**base, 'review_text': 'No finding'})


def test_kb_objective_refuses_rename_outside_owner():
    row = {'payload': {'files': {}, 'repo_dir': 'repos/demo', 'release': 'v1', 'today': '2026-10-04'}}
    output = {'operations': [{'kind': 'rename_page', 'page': 'repos/demo/rules.md', 'new_page': 'repos/other/rules.md'}]}
    assert objectives.score('kb-intake', row, output) == 0


def test_optional_audit_pr_does_not_interrupt_canary(autonomous):
    from infermatrix_copilot.improve import evolution_publish
    st, store, _, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    outbox = Path(st.improve_ledger_dir) / 'audit'
    st = st.model_copy(update={'improve_evolve_outbox_dir': str(outbox)})
    artifacts.atomic_json(outbox / 'acks' / (c['id'] + '.json'), {'candidate': c['id'], 'source_sha': c['artifact']['tree_sha'],
        'ok': True, 'url': 'https://example.test/audit/1'})
    evolution_publish.sync(st, store)
    updated = evolution.candidate(st, c['id'])
    assert updated['state'] == 'canary' and updated['pr'].endswith('/1')


def test_objective_coordinator_never_calls_legacy_dual_model_forensics(autonomous, monkeypatch):
    from infermatrix_copilot.improve import coordinator
    from infermatrix_copilot.engine.steps import improve
    st, store, model, worker = autonomous
    # Keep this large-effect routing test's positive cohort above the
    # coordinator's replenishment floor, including after its eight holdouts
    # are consumed. Negative controls are independently asserted above.
    objectives.prepare(st, store, workflow=objectives.ENGINE)
    path = objectives.data_root(st) / objectives.ENGINE / 'dataset.json'
    manifest = json.loads(path.read_text())
    manifest['items'] = [r for r in manifest['items'] if not r['objective'].get('negative')]
    artifacts.atomic_json(path, manifest)
    assert sum(r['split'] == 'holdout' for r in manifest['items']) >= 88
    def forbidden(*args, **kwargs): raise AssertionError('legacy model or human benchmark requested')
    monkeypatch.setattr(improve, '_forensics', forbidden)
    result = coordinator.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert result['stages']['evolve']['state'] == 'pr-ready', result
    count = len(model.calls)
    resumed = coordinator.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    assert resumed['state'] == 'complete' and len(model.calls) == count


def test_interrupted_generation_is_retired_without_manual_unblocking(autonomous):
    st, store, _, worker = autonomous
    class Interrupted:
        def create(self, **kwargs): raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt): evolution.run(st, store, workflow=objectives.ENGINE, llm=Interrupted(), sandbox=worker)
    result = evolution.run(st, store, workflow=objectives.ENGINE, llm=Interrupted(), sandbox=worker)
    assert result['state'] == 'rejected' and result['generation_interrupted']
    assert evolution.run(st, store, workflow=objectives.ENGINE, llm=Interrupted(), sandbox=worker)['reason'] == 'weekly-candidate-limit'


def test_unchanged_lints_cannot_consume_attribution_canary_items(autonomous):
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    data, _, _ = objectives.fault_case('abcdef0123456789', 'ceiling')
    count = len(worker.calls)
    runtime.execute(st, store, c['workflow'], data, model, sandbox=worker, driver_override='objective-lints')
    assert len(worker.calls) == count + 1
    runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    updated = evolution.candidate(st, c['id'])
    assert len(updated['canary_items']) == 1 and len(updated['production_records']) == 1
    assert store.get(updated['production_records'][0])['result']['pair']


def test_rollback_clears_current_deployment_attestation(autonomous):
    from infermatrix_copilot.improve.ledger import Ledger
    st, store, model, worker, c = verified(autonomous)
    runtime.promote(st, store, c, sandbox=worker)
    data, _, _ = objectives.fault_case('abcdef0123456789', 'ceiling')
    runtime.execute(st, store, c['workflow'], data, model, sandbox=worker)
    assert Ledger(Path(st.improve_ledger_dir)).load(c['workflow']).baseline['deployed_source']['candidate'] == c['id']
    runtime.rollback(st, store, evolution.candidate(st, c['id']), 'verified regression')
    assert 'deployed_source' not in Ledger(Path(st.improve_ledger_dir)).load(c['workflow']).baseline


def test_finished_candidate_does_not_block_following_week_hypothesis(autonomous):
    from infermatrix_copilot.improve import coordinator
    from infermatrix_copilot.improve.ledger import Ledger
    st, store, model, worker = autonomous
    c = evolution.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker)
    c['state'] = 'rejected'
    evolution.save(st, c, store)
    result = coordinator.run(st, store, workflow=objectives.ENGINE, llm=model, sandbox=worker, now=c['created_at'] + 8 * 86400)
    next_candidate = result['stages']['evolve']
    assert next_candidate.get('id') != c['id'] and next_candidate.get('proposal') != c['proposal']
    proposals = Ledger(Path(st.improve_ledger_dir)).load(c['workflow']).proposals
    assert next(p for p in proposals if p.id == c['proposal']).state == 'closed'
