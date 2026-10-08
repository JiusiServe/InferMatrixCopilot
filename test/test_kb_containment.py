"""Offline protocol and authority failures; no network or models."""
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.knowledge_service.signing import generate_private_key, public_key_text, sign
from infermatrix_copilot.knowledge_service.containment import (
    ContainmentError, _issue_usage, atomic_json, configured, digest, knowledge_availability_check,
    knowledge_maintenance_status, knowledge_policy_install, knowledge_usage_record,
    knowledge_usage_export, knowledge_usage_export_ack, load_policy, policy_identity,
)
from infermatrix_copilot.kb_service.containment import (
    accept_consumer_ack, collect_consumer_updates, pending_holds, record_hold,
    record_restoration, refresh_policy, merge_authorization,
)
from infermatrix_copilot.kb_service.maintenance_units import page_units
from infermatrix_copilot.knowledge_view import KnowledgeView


@pytest.fixture
def containment(tmp_path):
    key = generate_private_key(tmp_path / 'service.key')
    publisher = generate_private_key(tmp_path / 'publisher.key')
    root = tmp_path / 'knowledge'
    page = 'repos/demo/component/rules.md'
    path = root / page
    path.parent.mkdir(parents=True)
    text = '## ONE-1a — exact contract\n\nAlways preserve the value.\n'
    path.write_text(text)
    view = KnowledgeView(root, 'packaged')
    unit = page_units(page, text, 'demo', view.public_snapshot)[0]
    cfg = {'enabled': True, 'consumer_id': 'native', 'public_keys': [public_key_text(key.public_key())],
           'policy_path': str(tmp_path / 'consumer/policy.json'), 'state_dir': str(tmp_path / 'consumer/state')}
    rt = SimpleNamespace(state_dir=tmp_path / 'service', clock=time.time,
                         outbox=SimpleNamespace(_key=key), publisher_public_key=publisher.public_key(),
                         containment_policy_dir=tmp_path / 'authority', containment_consumers=['native'],
                         containment_enforce=True, registry={'demo': SimpleNamespace(enabled=True, auto_merge=True)})
    rt.state_dir.mkdir()
    return SimpleNamespace(key=key, publisher=publisher, cfg=cfg, rt=rt, view=view, unit=unit, page=page, text=text)


def install(c):
    policy = refresh_policy(c.rt)
    envelope = json.loads((c.rt.containment_policy_dir / 'policy.json').read_text())
    ack = knowledge_policy_install(envelope, config=c.cfg, release_id='fixture-release')
    ack.update(runtime_ready=True,runtime_checked_at=time.time(),runtime_config_sha256=digest(c.cfg))
    accept_consumer_ack(c.rt, ack, authenticated_consumer='native')
    return policy, envelope, ack


def finding():
    return {'outcome': 'contradicted', 'reason': 'Original source preserves no value.', 'reviewer': 'other-family:model',
            'evidence': [{'repository': 'owner/demo', 'sha': 'a'*40, 'path': 'source.py',
                          'start_line': 1, 'end_line': 1, 'content_sha256': 'b'*64, 'excerpt': 'pass\n'}]}


def test_disabled_requires_no_crypto_files_and_keeps_compatibility():
    assert knowledge_maintenance_status(config={'enabled': False})['ready']
    assert knowledge_availability_check(None, config={'enabled': False})['allowed']
    assert knowledge_usage_record({}, config={'enabled': False})['injected_units'] == []


def test_signed_freshness_wrong_purpose_and_replay(containment):
    c = containment
    policy, envelope, _ = install(c)
    assert load_policy(c.cfg)[1]['generation'] == policy['generation']
    wrong = sign('kb-containment-decision', envelope['payload'], c.key)
    atomic_json(Path(c.cfg['policy_path']), wrong)
    assert not knowledge_maintenance_status(config=c.cfg)['ready']
    atomic_json(Path(c.cfg['policy_path']), envelope)
    with pytest.raises(ContainmentError, match='stale'):
        load_policy(c.cfg, now=policy['expires_at'])
    newer = {**envelope['payload'], 'generation': policy['generation']+1}
    knowledge_policy_install(sign('kb-containment-policy', newer, c.key), config=c.cfg, release_id='next')
    with pytest.raises(ContainmentError, match='replay'):
        knowledge_policy_install(envelope, config=c.cfg, release_id='rollback')


def test_private_issuance_exact_context_and_old_receipt_hold(containment):
    c = containment
    install(c)
    context = {'knowledge_snapshot': c.view.public_snapshot, 'documents': [{'document_id': c.page, 'excerpt': c.text}]}
    with pytest.raises((ContainmentError, OSError)):
        knowledge_usage_record(context, config=c.cfg)
    receipt = _issue_usage(context, view=c.view, config=c.cfg)
    injected = knowledge_usage_record(context, injected=True, config=c.cfg)
    assert receipt['retrieved_units'] and not receipt['injected_units']
    assert injected['injected_units']
    assert knowledge_availability_check(injected, config=c.cfg)['allowed']
    with pytest.raises((ContainmentError, OSError)):
        knowledge_usage_record({**context, 'model_content': 'invented advice'}, config=c.cfg)
    held = record_hold(c.rt, c.unit, finding(), enforce=True)
    assert held['status'] == 'held'
    assert not pending_holds(c.rt)['ready']
    install(c)
    assert pending_holds(c.rt)['ready']
    assert not knowledge_availability_check(receipt, config=c.cfg)['allowed']
    with configured(c.cfg), pytest.raises(ContainmentError):
        c.view.path(c.page)


def test_shadow_never_publishes_or_changes_generation(containment):
    c = containment
    before, _, _ = install(c)
    result = record_hold(c.rt, c.unit, finding(), enforce=False)
    assert result['status'] == 'would_hold'
    assert refresh_policy(c.rt)['generation'] == before['generation']
    assert not list((c.rt.containment_policy_dir / 'decisions').glob('*'))


def test_bad_hash_cannot_disappear_in_higher_generation(containment):
    c = containment
    install(c)
    record_hold(c.rt, c.unit, finding(), enforce=True)
    policy, _, _ = install(c)
    empty = {k:v for k,v in policy.items() if k != 'policy_digest'}
    empty.update(generation=policy['generation']+1, decisions=[])
    with pytest.raises(ContainmentError, match='forget'):
        knowledge_policy_install(sign('kb-containment-policy', empty, c.key), config=c.cfg, release_id='unsafe')


def test_authenticated_usage_roundtrip_retries_and_unregistered_rejection(containment):
    c = containment
    _, _, ack = install(c)
    context = {'documents': [{'document_id': c.page, 'excerpt': c.text}]}
    _issue_usage(context, view=c.view, config=c.cfg)
    knowledge_usage_record(context, injected=True, config=c.cfg)
    usage = knowledge_usage_export(config=c.cfg)
    assert {'retrieved', 'injected'} == {e['kind'] for e in usage['events']}
    assert '"context":' not in json.dumps(usage) and c.text not in json.dumps(usage)
    class Store:
        rows = {}
        def record_usage(self, identity, unit, **kw):
            row = (unit, kw)
            assert self.rows.setdefault(identity, row) == row
    store = Store()
    folder = c.rt.state_dir / 'inbox/containment'
    folder.mkdir(parents=True)
    payload = {'schema_version': 1, 'consumer_id': 'native', 'received_at': time.time(), 'ack': ack, 'usage': usage}
    envelope = sign('kb-containment-transport', payload, c.publisher)
    path = folder / f'{digest(envelope)}.json'
    for _ in range(2):
        atomic_json(path, envelope)
        assert collect_consumer_updates(c.rt, store)['accepted'] == 1
    assert len(store.rows) == len(usage['events'])
    knowledge_usage_export_ack(usage['receipts'], config=c.cfg)
    assert not knowledge_usage_export(config=c.cfg)['events']
    forged = sign('kb-containment-transport', {**payload, 'consumer_id': 'unknown'}, c.publisher)
    atomic_json(folder / f'{digest(forged)}.json', forged)
    assert collect_consumer_updates(c.rt, store)['rejected'] == 1


def test_snapshot_scope_does_not_claim_actual_injection(containment):
    c = containment
    install(c)
    receipt = _issue_usage({'scope':'snapshot','repository':'demo'}, mode='strict', view=c.view, config=c.cfg)
    assert receipt['scope_units'] and receipt['retrieved_units'] == receipt['injected_units'] == []
    assert knowledge_availability_check(receipt, config=c.cfg)['allowed']


def test_restoration_rejects_boolean_only_proof(containment):
    c = containment
    c.rt.ledger = SimpleNamespace(changeset=lambda _: {'kind': 'intake', 'status': 'merged', 'detail': {}})
    with pytest.raises(ContainmentError):
        record_restoration(c.rt, c.unit['unit_id'], approved_hashes=['c'*64], proof={
            'original_source_review':True,'cross_family_judge':True,'quality_gate':True,
            'required_ci':True,'active_bytes':True,'correction_merge_sha':'a'*40})


def test_merge_authorization_current_ack_and_generation(containment):
    c = containment
    install(c)
    changeset = {'kind':'correction','id':'change-1','head_sha':'a'*40,'detail':{'maintenance_policy':'b'*64}}
    proof = merge_authorization(c.rt, changeset)
    assert proof['purpose'] == 'kb-maintenance-merge'
    assert 0 < proof['payload']['expires_at'] - proof['payload']['issued_at'] <= 60
    record_hold(c.rt, c.unit, finding(), enforce=True)
    with pytest.raises(ContainmentError):
        merge_authorization(c.rt, changeset)


def test_actual_offline_revocation_drill_is_policy_and_roster_bound(containment):
    from infermatrix_copilot.kb_service.containment_drill import run_revocation_drill, acceptance_current
    c = containment
    result = run_revocation_drill(c.rt, 'f'*64)
    assert result['passed'], result['scenarios']
    assert acceptance_current(c.rt, 'f'*64)
    assert not acceptance_current(c.rt, 'e'*64)
    c.rt.containment_consumers.append('new-consumer')
    assert not acceptance_current(c.rt, 'f'*64)


def test_enrolled_consumer_cannot_drop_enabled_configuration(containment):
    c = containment
    install(c)
    assert not knowledge_availability_check(None, config={**c.cfg,'enabled':False})['allowed']
    with pytest.raises(ContainmentError, match='cannot disable'):
        load_policy({**c.cfg,'enabled':False})


def test_native_readiness_requires_real_lease_and_current_config(containment, monkeypatch):
    from infermatrix_copilot.kb_service.containment import native_ack
    from infermatrix_copilot.kb_service.ledger import Ledger
    c = containment
    cfg = {**c.cfg, 'policy_path':str(c.rt.containment_policy_dir/'policy.json')}
    monkeypatch.setenv('KB_CONTAINMENT_CONFIG',json.dumps(cfg))
    monkeypatch.setattr(KnowledgeView,'current',classmethod(lambda cls:c.view))
    c.rt.ledger = Ledger(c.rt.state_dir/'kb.db')
    c.rt.lease_owner = c.rt.ledger.acquire_lease('native-fixture')
    refresh_policy(c.rt)
    ack = native_ack(c.rt)
    assert ack['runtime_ready'] and pending_holds(c.rt)['ready']
    c.rt.ledger.release_lease(c.rt.lease_owner)
    with pytest.raises(ContainmentError, match='lease'):
        native_ack(c.rt)
    c.rt.ledger.close()


def test_held_search_is_omitted_but_stale_policy_refuses(containment):
    from infermatrix_copilot.knowledge_docs import KnowledgeDocs
    c = containment
    install(c)
    record_hold(c.rt,c.unit,finding(),enforce=True)
    _, envelope, _ = install(c)
    with configured(c.cfg):
        assert KnowledgeDocs(c.view.root,'repos/demo').search('preserve') == []
    stale = {**envelope['payload'],'issued_at':time.time()-601,'expires_at':time.time()-1}
    atomic_json(Path(c.cfg['policy_path']),sign('kb-containment-policy',stale,c.key))
    with configured(c.cfg), pytest.raises(ContainmentError):
        KnowledgeDocs(c.view.root,'repos/demo').search('preserve')


def test_real_direct_plan_is_issued_and_rechecks_generation(containment):
    from infermatrix_copilot.sdk.v1 import DirectClient, DirectReviewRequest, DirectCompletionRequest, RepositoryRef, ChangedPath
    c = containment
    install(c)
    client = DirectClient(knowledge_maintenance=c.cfg)
    plan = client.plan(DirectReviewRequest(review_id='containment-real-plan',repository=RepositoryRef(alias='vllm-omni'),
        pr_number=1,expected_head_sha='a'*40,title='scheduler update',body='',changed_paths=(ChangedPath('vllm_omni/core/sched/scheduler.py','modified'),)))
    receipt = knowledge_usage_record(plan.to_dict(),injected=True,config=c.cfg)
    assert receipt['injected_units'] and knowledge_availability_check(receipt,config=c.cfg)['allowed']
    completion = DirectCompletionRequest(review_context_id=plan.review_context_id,
        expected_head_sha='a'*40,evidence_head_sha='a'*40,subtraction_signal='none',existing_feedback_status='checked')
    assert client.validate(completion).review_complete
    view = client._view()
    page = plan.knowledge_routes[0].document.document_id
    unit = page_units(page,(view.root/page).read_text(),'vllm-omni',view.public_snapshot)[0]
    c.rt.registry['vllm-omni'] = SimpleNamespace(enabled=True,auto_merge=True)
    record_hold(c.rt,unit,finding(),enforce=True)
    install(c)
    assert not knowledge_availability_check(receipt,config=c.cfg)['allowed']
    with pytest.raises(ContainmentError):
        client.validate(completion)


@pytest.mark.parametrize('profile', ['legacy', 'adaptive'])
def test_raw_mcp_completion_rechecks_issued_policy_and_public_contract(containment, monkeypatch, tmp_path, profile):
    from functools import partial
    import test_thin_mcp_server as helpers
    from infermatrix_copilot.direct_routing import direct_completion_result
    c = containment
    install(c)
    monkeypatch.setattr(helpers, 'Settings', partial(helpers.Settings, run_root=tmp_path/'runs'))
    server, _ = helpers._fake_mcp(monkeypatch)
    arguments = {'subtraction_signal':'none','evidence_head_sha':'a'*40,'existing_feedback_status':'checked'}
    with configured(c.cfg):
        plan = server.tools['review'](target='1',repo='vllm-omni',title='scheduler update',body='',
            changed_files=['vllm_omni/core/sched/scheduler.py'],expected_head_sha='a'*40,knowledge_profile=profile)
        receipt = plan['knowledge_usage']
        assert server.tools['validate_direct_review'](**arguments,knowledge_usage=receipt)['publish_ready']
        assert direct_completion_result(**arguments,knowledge_usage=receipt)['publish_ready']
        assert not direct_completion_result(**arguments)['publish_ready']
        assert not direct_completion_result(**arguments,knowledge_usage={**receipt,'receipt_id':'f'*64})['publish_ready']
        unit_ref = next(row for row in receipt['scope_units'] if row['repo']=='vllm-omni')
        view = KnowledgeView.current()
        unit = next(row for row in page_units(unit_ref['page'],(view.root/unit_ref['page']).read_text(),
            'vllm-omni',view.public_snapshot) if row['unit_id']==unit_ref['unit_id'])
        c.rt.registry['vllm-omni'] = SimpleNamespace(enabled=True,auto_merge=True)
        record_hold(c.rt,unit,finding(),enforce=True)
        install(c)
        refused = server.tools['validate_direct_review'](**arguments,knowledge_usage=receipt)
        assert refused['status']=='partial_review' and not refused['publish_ready']
        assert refused['knowledge_availability']['reassessment_required']
        assert not direct_completion_result(**arguments,knowledge_usage=receipt)['publish_ready']


def test_owner_transport_runs_installer_and_requires_actual_heartbeat(containment, tmp_path):
    import hashlib
    import os
    import shlex
    import subprocess
    import sys
    from infermatrix_copilot.kb_service.publisher import Publisher, LocalTransport
    c = containment
    policy, _, _ = install(c)
    config_file, release_file = tmp_path/'config.json', tmp_path/'release.json'
    config_file.write_text(json.dumps(c.cfg))
    release_file.write_bytes(b'{"release":"actual"}\r\n')
    heartbeat = {'protocol_version':1,'consumer_id':'native','ready':True,'release_id':'sha256:'+hashlib.sha256(release_file.read_bytes()).hexdigest(),
                 'generation':policy['generation'],'policy_digest':policy['policy_digest'],
                 'config_sha256':digest(c.cfg),'checked_at':time.time()}
    atomic_json(Path(c.cfg['state_dir'])/'heartbeat.json',heartbeat)
    def local_ssh(argv, **kw):
        assert argv[:5] == ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5']
        assert kw['timeout'] == 20
        env = {**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')}
        return subprocess.run(shlex.split(argv[-1]),env=env,**kw)
    publisher = Publisher(LocalTransport(c.rt.state_dir),c.key.public_key(),c.publisher,SimpleNamespace(),tmp_path/'publisher-state',{},
        containment_targets={'native':{'host':'fixture-owner','python':sys.executable,'config_file':str(config_file),'release_file':str(release_file)}},
        containment_run=local_ssh)
    class Store:
        def record_usage(self,*args,**kw): pass
    assert publisher.sync_containment()['containment_synced'] == 1
    assert collect_consumer_updates(c.rt,Store())['accepted'] == 1
    assert pending_holds(c.rt)['ready']
    # New policy is installed, but a stopped/old watcher cannot ACK it.
    record_hold(c.rt,c.unit,finding(),enforce=True)
    assert publisher.sync_containment()['containment_synced'] == 1
    assert collect_consumer_updates(c.rt,Store())['accepted'] == 1
    assert not pending_holds(c.rt)['ready']


def test_publisher_rechecks_short_authorization_after_generation_change(containment,tmp_path):
    from infermatrix_copilot.kb_service.publisher import Publisher, LocalTransport, PublishError
    from infermatrix_copilot.kb_service.outbox import OutboxItem
    c = containment
    install(c)
    changeset = {'id':'correction-1','kind':'correction','head_sha':'a'*40,'detail':{'maintenance_policy':'b'*64}}
    body = {'changeset_id':changeset['id'],'head_sha':changeset['head_sha'],'maintenance_required':True,
            'maintenance':merge_authorization(c.rt,changeset)}
    item = OutboxItem('1-'+'a'*12,'merge','demo',1,1,time.time(),time.time()+60,body)
    publisher = Publisher(LocalTransport(c.rt.state_dir),c.key.public_key(),c.publisher,SimpleNamespace(),tmp_path/'pub',{})
    publisher._recheck_maintenance(item)
    publisher.clock = lambda:time.time()+61
    with pytest.raises(PublishError,match='maintenance'):
        publisher._recheck_maintenance(item)
    publisher.clock = time.time
    record_hold(c.rt,c.unit,finding(),enforce=True)
    with pytest.raises(PublishError,match='maintenance'):
        publisher._recheck_maintenance(item)


def test_runtime_hop_grace_is_bounded_and_merge_proof_stays_sixty_seconds(containment):
    from infermatrix_copilot.knowledge_service.containment import MAX_RUNTIME_AGE
    c = containment
    _, _, ack = install(c)
    ack['runtime_checked_at'] = time.time()-145
    accept_consumer_ack(c.rt,ack,authenticated_consumer='native')
    assert pending_holds(c.rt)['ready']
    c.rt.clock = lambda:time.time()+MAX_RUNTIME_AGE
    assert not pending_holds(c.rt)['ready']


def test_repeat_independent_hold_keeps_generation_and_audit_receipts(containment):
    c = containment
    install(c)
    first = record_hold(c.rt,c.unit,finding(),enforce=True)
    repeated = record_hold(c.rt,c.unit,finding(),enforce=True)
    assert repeated['generation'] == first['generation']
    again = record_hold(c.rt,c.unit,{**finding(),'reason':'Another independent same contradiction'},enforce=True)
    assert again['generation'] == first['generation']
    assert len(list((c.rt.containment_policy_dir/'decisions').glob('*.json'))) == 2


def test_strict_pins_request_scope_and_drains_running_child(containment,tmp_path,monkeypatch):
    from infermatrix_copilot.app.run_service import RunService
    from infermatrix_copilot.kb_service import repo_spec
    from infermatrix_copilot.sdk.v1 import StrictRuntime
    c = containment
    install(c)
    monkeypatch.setattr(KnowledgeView,'current',classmethod(lambda cls:c.view))
    monkeypatch.setattr(repo_spec,'resolve_snapshot_repo',lambda *_:SimpleNamespace(repo_id='demo'))
    run_root, run_id = tmp_path/'runs', 'strict-test'
    run = run_root/run_id
    run.mkdir(parents=True)
    (run/'request.json').write_text(json.dumps({'repo':'demo'}))
    core = SimpleNamespace(run_root=run_root,settings=SimpleNamespace(knowledge_dir=c.view.root),knowledge_maintenance=c.cfg)
    pin = RunService._pin_knowledge(core,run_id)
    receipt = pin['knowledge_usage']
    assert receipt['scope_units'] and receipt['retrieved_units'] == receipt['injected_units'] == []
    assert knowledge_availability_check(receipt,config=c.cfg)['allowed']
    record_hold(c.rt,c.unit,finding(),enforce=True)
    install(c)
    runtime = object.__new__(StrictRuntime)
    runtime._knowledge_maintenance = c.cfg
    runtime._core = core
    core.get_result = lambda *args,**kw:{'state':'running','result':None}
    running = runtime.get_result(run_id)
    assert running.state == 'running' and running.payload['knowledge_held']
    core.get_result = lambda *args,**kw:{'state':'done','result':None}
    terminal = runtime.get_result(run_id)
    assert terminal.state == 'held' and terminal.payload['knowledge_usage'] == receipt


def test_injection_does_not_attribute_omitted_page_units(containment):
    c = containment
    install(c)
    first = '## FIRST-1a — visible unit\n\nPreserve this visible source contract for the current operation.\n'
    second = '## SECOND-1a — omitted unit\n\nNever inject this omitted source contract in the short excerpt.\n'
    # Use a real provider byte window: pad the first unit beyond excerpt cap.
    first += ('Visible detailed source contract with a unique prefix.\n'*1400)
    (c.view.root/c.page).write_text(first+second)
    data = (first+second).encode()
    context = {'documents':[{'document_id':c.page,'excerpt':data[:65536].decode()}]}
    receipt = _issue_usage(context,view=c.view,config=c.cfg,injected=True)
    assert len(receipt['retrieved_units']) == 2
    assert len(receipt['injected_units']) == 1
    assert receipt['injected_units'][0]['block_id'] == 'FIRST-1a'
    assert receipt['injected_units'][0]['partial']
    assert len(receipt['scope_units']) == 2


def test_provider_issuance_refuses_stale_excerpt_and_forged_resource_hash(containment):
    c = containment
    install(c)
    with pytest.raises(ContainmentError,match='excerpt'):
        _issue_usage({'documents':[{'document_id':c.page,'excerpt':'stale old advice'}]},view=c.view,config=c.cfg)
    with pytest.raises(ContainmentError,match='digest'):
        _issue_usage({'documents':[{'document_id':c.page,'sha256':'sha256:'+'f'*64}]},view=c.view,config=c.cfg)
