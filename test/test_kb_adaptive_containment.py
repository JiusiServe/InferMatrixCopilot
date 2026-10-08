"""Actual adaptive follow-ups remain publication dependencies across restart."""
import json
import time
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.containment import record_hold, refresh_policy
from infermatrix_copilot.kb_service.maintenance_units import page_units
from infermatrix_copilot.kb_service.repo_spec import RepoSpec
from infermatrix_copilot.knowledge_service.containment import (
    ContainmentError, configured, knowledge_availability_check,
    knowledge_policy_install, knowledge_usage_record, knowledge_usage_export,
)
from infermatrix_copilot.knowledge_service.signing import generate_private_key, public_key_text
from infermatrix_copilot.knowledge_view import KnowledgeView, build_manifest
from infermatrix_copilot.sdk.v1 import (
    ChangedPath, DirectClient, DirectCompletionRequest, DirectReviewRequest, RepositoryRef,
)

PIN = 'a'*40
FOLLOWUP = 'repos/r/followup.md'


@pytest.fixture
def adaptive(tmp_path, monkeypatch):
    root = tmp_path/'snapshot/knowledge'
    (root/'repos/r').mkdir(parents=True)
    (root/'AGENTS.md').write_text('Repository knowledge navigation.')
    (root/'repos/r/_index.md').write_text('Repository navigation.')
    guide = root/'general/review/guides/simplification-audit.md'
    guide.parent.mkdir(parents=True)
    guide.write_text('Inspect the actual implementation before publishing conclusions.')
    (root/'repos/r/rules.md').write_text('''---
title: Initial rules
type: rule
---
# Initial rules
## Direct 速查
Initial route points to src/initial.py.
## INIT-1a — initial contract
Initial source inputs retain their explicit ownership throughout processing.
''')
    (root/FOLLOWUP).write_text(f'''---
title: UniqueFollowup contract
type: guide
sources: [acme/r@{PIN}:src/followup.py]
---
# UniqueFollowup contract
## Downstream contract
UniqueFollowup values must preserve the complete downstream source contract.
''')
    (root/'repos/r/_routes.yaml').write_text(yaml.safe_dump({'schema_version':1,'owners':[
        {'owner':'initial','path':'repos/r/rules.md','signals':['initial'],'scope_prefixes':['src/initial.py']}]}))
    spec = RepoSpec('r',aliases=('acme/r',),source_pin=PIN,catalog_hash='b'*64,policy_hash='c'*64)
    (root/'_repositories.yaml').write_text(yaml.safe_dump({'schema_version':1,'repos':{'r':spec.to_dict()}}))
    manifest = build_manifest(root,'adaptive-snapshot')
    (root.parent/'MANIFEST.json').write_text(json.dumps(manifest))
    monkeypatch.setenv('KNOWLEDGE_ROOT',str(root.parent))
    key = generate_private_key(tmp_path/'service.key')
    rt = SimpleNamespace(state_dir=tmp_path/'service',clock=time.time,outbox=SimpleNamespace(_key=key),
        containment_policy_dir=tmp_path/'authority',containment_consumers=['native'],containment_enforce=True,
        registry={'r':SimpleNamespace(enabled=True,auto_merge=True)})
    rt.state_dir.mkdir()
    cfg = {'enabled':True,'consumer_id':'native','public_keys':[public_key_text(key.public_key())],
           'policy_path':str(tmp_path/'consumer/policy.json'),'state_dir':str(tmp_path/'consumer/state')}
    def install():
        refresh_policy(rt)
        envelope = json.loads((rt.containment_policy_dir/'policy.json').read_text())
        knowledge_policy_install(envelope,config=cfg,release_id='adaptive-fixture')
    install()
    request = DirectReviewRequest('adaptive-review',RepositoryRef('r'),1,PIN,'initial','',
                                 (ChangedPath('src/initial.py'),))
    return SimpleNamespace(root=root,rt=rt,cfg=cfg,request=request,install=install,view=KnowledgeView.current(),
                           context_path=tmp_path/'context.sqlite',tmp_path=tmp_path)


def hold_followup(c):
    view = c.view
    unit = page_units(FOLLOWUP,(c.root/FOLLOWUP).read_text(),'r',view.public_snapshot)[0]
    record_hold(c.rt,unit,{'outcome':'contradicted','reason':'Pinned source contradicts follow-up.',
        'reviewer':'independent:judge','evidence':[{'repository':'acme/r','sha':PIN,'path':'src/followup.py',
        'start_line':1,'end_line':1,'content_sha256':'c'*64,'excerpt':'source contract'}]},enforce=True)
    c.install()


def deliver(client, session, operation):
    if operation == 'expand_read':
        client.expand_knowledge_context(session,target_tokens=30000,reason='Read downstream contract')
        operation = 'read'
    if operation == 'read':
        return client.read_knowledge_context(session,FOLLOWUP)
    if operation == 'search':
        return client.search_knowledge_context(session,'UniqueFollowup values')
    return client.related_knowledge_context(session,['src/followup.py'],query='UniqueFollowup')


@pytest.mark.parametrize('operation',['read','search','related','expand_read'])
def test_sdk_initial_receipt_includes_restarted_followup_before_final_validation(adaptive, operation):
    c = adaptive
    client = DirectClient(knowledge_context_path=c.context_path,knowledge_maintenance=c.cfg)
    plan = client.plan_adaptive(c.request)
    old_receipt = knowledge_usage_record(plan,config=c.cfg)
    assert FOLLOWUP not in {row['path'] for row in old_receipt['pages']}
    completion = DirectCompletionRequest(review_context_id=plan['review_context_id'],expected_head_sha=PIN,
        evidence_head_sha=PIN,subtraction_signal='none',existing_feedback_status='checked')
    assert client.validate(completion).review_complete
    # A second SDK resumes the actual durable session, not the first instance's memory.
    restarted = DirectClient(knowledge_context_path=c.context_path,knowledge_maintenance=c.cfg)
    followup = deliver(restarted,plan['session_id'],operation)
    assert FOLLOWUP in {row['path'] for row in followup['documents']}
    assert knowledge_availability_check(old_receipt,config=c.cfg)['allowed']
    hold_followup(c)
    assert not knowledge_availability_check(old_receipt,config=c.cfg)['allowed']
    with pytest.raises(ContainmentError):
        client.validate(completion)


@pytest.mark.parametrize('operation',['read','search','related','expand_read'])
def test_raw_mcp_records_actual_injection_and_old_receipt_holds_after_followup(adaptive, monkeypatch, operation):
    import test_thin_mcp_server as helpers
    c = adaptive
    monkeypatch.setattr(helpers,'Settings',partial(helpers.Settings,run_root=c.tmp_path/'runs'))
    server, _ = helpers._fake_mcp(monkeypatch)
    args = {'subtraction_signal':'none','evidence_head_sha':PIN,'existing_feedback_status':'checked'}
    with configured(c.cfg):
        plan = server.tools['review'](target='1',repo='r',title='initial',body='',
            changed_files=['src/initial.py'],expected_head_sha=PIN,knowledge_profile='adaptive')
        receipt = plan['knowledge_usage']
        assert receipt['injected_units']
        assert FOLLOWUP not in {row['path'] for row in receipt['pages']}
        assert server.tools['validate_direct_review'](**args,knowledge_usage=receipt)['publish_ready']
        session = plan['session_id']
        if operation == 'expand_read':
            expanded = server.tools['expand_knowledge_context'](session,30000,'Read downstream contract')
            assert 'model_content' not in expanded and 'knowledge_usage' not in expanded
            operation = 'read'
        if operation == 'read':
            result = server.tools['read_knowledge_context'](session,FOLLOWUP)
        elif operation == 'search':
            result = server.tools['search_knowledge_context'](session,'UniqueFollowup values')
        else:
            result = server.tools['related_knowledge_context'](session,['src/followup.py'],'UniqueFollowup')
        injected = [row for row in result['knowledge_usage']['injected_units'] if row['page']==FOLLOWUP]
        assert injected, 'Actual follow-up model context must be recorded as injected'
        if operation == 'read':
            assert all(not row['partial'] for row in injected)
        if operation == 'search':
            assert all(row['partial'] for row in injected)
        exported = knowledge_usage_export(config=c.cfg)
        assert any(row['kind']=='injected' and row['unit_id']==injected[0]['unit_id'] for row in exported['events'])
        hold_followup(c)
        assert not knowledge_availability_check(receipt,config=c.cfg)['allowed']
        refused = server.tools['validate_direct_review'](**args,knowledge_usage=receipt)
        assert not refused['publish_ready'] and refused['knowledge_availability']['reassessment_required']


@pytest.mark.parametrize('corruption',['missing','foreign_member','duplicate'])
def test_session_journal_corruption_cannot_skip_followups(adaptive, corruption):
    c = adaptive
    client = DirectClient(knowledge_context_path=c.context_path,knowledge_maintenance=c.cfg)
    plan = client.plan_adaptive(c.request)
    receipt = knowledge_usage_record(plan,config=c.cfg)
    client.read_knowledge_context(plan['session_id'],FOLLOWUP)
    path = Path(c.cfg['state_dir'])/'delivery-sessions'/f"{plan['session_id']}.json"
    if corruption == 'missing':
        path.unlink()
    else:
        journal = json.loads(path.read_text())
        if corruption == 'duplicate':
            journal['receipts'].append(journal['receipts'][0])
            path.write_text(json.dumps(journal))
        else:
            member = Path(c.cfg['state_dir'])/'usage'/f"{journal['receipts'][0]}.json"
            record = json.loads(member.read_text())
            record['delivery_session'] = 'f'*64
            member.write_text(json.dumps(record))
    assert not knowledge_availability_check(receipt,config=c.cfg)['allowed']


def test_legacy_sdk_document_pages_join_original_review_receipt(adaptive):
    c = adaptive
    client = DirectClient(knowledge_context_path=c.context_path,knowledge_maintenance=c.cfg)
    plan = client.plan(c.request)
    receipt = knowledge_usage_record(plan.to_dict(),config=c.cfg)
    assert FOLLOWUP not in {row['path'] for row in receipt['pages']}
    completion = DirectCompletionRequest(review_context_id=plan.review_context_id,expected_head_sha=PIN,
        evidence_head_sha=PIN,subtraction_signal='none',existing_feedback_status='checked')
    assert client.validate(completion).review_complete
    with pytest.raises(ContainmentError,match='review_context_id'):
        client.read_document(FOLLOWUP)
    first = client.read_document(FOLLOWUP,review_context_id=plan.review_context_id,max_bytes=80)
    second = client.read_document(FOLLOWUP,review_context_id=plan.review_context_id,offset=first.next_offset)
    actual = knowledge_usage_record(second.to_dict(),injected=True,config=c.cfg)
    assert any(row['page']==FOLLOWUP for row in actual['injected_units'])
    assert knowledge_availability_check(receipt,config=c.cfg)['allowed']
    hold_followup(c)
    assert not knowledge_availability_check(receipt,config=c.cfg)['allowed']
    with pytest.raises(ContainmentError):
        client.validate(completion)


@pytest.mark.parametrize('profile',['legacy','adaptive'])
@pytest.mark.parametrize('operation',['read','search'])
def test_raw_document_tools_require_bound_receipt_and_keep_pinned_view(adaptive, monkeypatch, profile, operation):
    import shutil
    import test_thin_mcp_server as helpers
    c = adaptive
    monkeypatch.setattr(helpers,'Settings',partial(helpers.Settings,run_root=c.tmp_path/'runs'))
    server, _ = helpers._fake_mcp(monkeypatch)
    args = {'subtraction_signal':'none','evidence_head_sha':PIN,'existing_feedback_status':'checked'}
    with configured(c.cfg):
        plan = server.tools['review'](target='1',repo='r',title='initial',body='',changed_files=['src/initial.py'],
            expected_head_sha=PIN,knowledge_profile=profile)
        receipt = plan['knowledge_usage']
        tool = server.tools['doc_'+operation]
        parameters = {'repo':'r',**({'path':FOLLOWUP} if operation=='read' else {'query':'UniqueFollowup values'})}
        with pytest.raises(ContainmentError):
            tool(**parameters)
        # A later activation must not switch a registered review's follow-up root.
        newer = c.tmp_path/'newer/knowledge'
        shutil.copytree(c.root,newer)
        (newer/FOLLOWUP).write_text('A completely different activated page.')
        (newer.parent/'MANIFEST.json').write_text(json.dumps(build_manifest(newer,'newer-snapshot')))
        monkeypatch.setenv('KNOWLEDGE_ROOT',str(newer.parent))
        result = tool(**parameters,knowledge_usage=receipt)
        assert result['knowledge_usage']['snapshot']==c.view.public_snapshot
        assert any(row['page']==FOLLOWUP for row in result['knowledge_usage']['injected_units'])
        assert 'UniqueFollowup' in (result.get('content') or result['matches'][0]['text'])
        assert server.tools['validate_direct_review'](**args,knowledge_usage=receipt)['publish_ready']
        hold_followup(c)
        assert not server.tools['validate_direct_review'](**args,knowledge_usage=receipt)['publish_ready']


@pytest.mark.parametrize('surface',['sdk','raw'])
def test_identical_pages_in_concurrent_reviews_keep_distinct_delivery_groups(adaptive, monkeypatch, surface):
    from dataclasses import replace
    c = adaptive
    with configured(c.cfg):
        if surface=='sdk':
            client = DirectClient(knowledge_context_path=c.context_path,knowledge_maintenance=c.cfg)
            plans = [client.plan(replace(c.request,review_id=f'review-{i}')) for i in range(3)]
            receipts = [knowledge_usage_record(plan.to_dict(),config=c.cfg) for plan in plans]
            for plan in plans[:2]:
                client.read_document(FOLLOWUP,review_context_id=plan.review_context_id)
        else:
            import test_thin_mcp_server as helpers
            monkeypatch.setattr(helpers,'Settings',partial(helpers.Settings,run_root=c.tmp_path/'runs'))
            server, _ = helpers._fake_mcp(monkeypatch)
            plans = [server.tools['review'](target=str(i),repo='r',title='initial',changed_files=['src/initial.py'])
                     for i in range(3)]
            receipts = [plan['knowledge_usage'] for plan in plans]
            for receipt in receipts[:2]:
                server.tools['doc_read'](FOLLOWUP,repo='r',knowledge_usage=receipt)
        assert len({receipt['delivery_session'] for receipt in receipts})==3
        hold_followup(c)
        assert [knowledge_availability_check(receipt,config=c.cfg)['allowed'] for receipt in receipts]==[False,False,True]
