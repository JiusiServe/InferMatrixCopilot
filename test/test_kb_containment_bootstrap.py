"""Fresh authority bootstrap with real leases and signatures; no models/network."""
from contextlib import contextmanager
import json
import os
import stat
import time
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.containment import collect_consumer_updates, refresh_policy
from infermatrix_copilot.kb_service.ledger import Ledger
from infermatrix_copilot.knowledge_service.containment import ContainmentError, configured
from infermatrix_copilot.knowledge_service.signing import generate_private_key, verify


@contextmanager
def _umask(value):
    previous = os.umask(value)
    try:
        yield
    finally:
        os.umask(previous)


@pytest.fixture
def leased_authority(tmp_path):
    state = tmp_path / 'service'
    state.mkdir()
    key = generate_private_key(tmp_path / 'service.key')
    ledger = Ledger(state / 'kb.db')
    rt = SimpleNamespace(state_dir=state, ledger=ledger, clock=time.time,
                         outbox=SimpleNamespace(_key=key), publisher_public_key=None,
                         containment_policy_dir=state / 'authority',
                         containment_consumers=[], containment_enforce=False)
    native = tmp_path / 'unenrolled-native'
    try:
        with ledger.lease(renew_every=3600) as owner, configured(
                {'enabled': False, 'consumer_id': 'native', 'state_dir': str(native)}):
            rt.lease_owner = owner
            yield rt, key, native
        assert ledger.live_lease() == ''
    finally:
        ledger.close()


@pytest.mark.parametrize('mask', [0o002, 0o022], ids=['group-writable-umask', 'standard-umask'])
def test_collect_then_refresh_bootstraps_private_signed_empty_authority(leased_authority, mask):
    rt, key, native = leased_authority
    authority = rt.containment_policy_dir
    assert not authority.exists()

    with _umask(mask):
        assert collect_consumer_updates(rt) == {'accepted': 0, 'rejected': 0, 'usage': 0}
        refreshed = refresh_policy(rt)

    assert stat.S_IMODE(authority.stat().st_mode) == 0o700
    assert stat.S_IMODE((authority / 'consumer-import').stat().st_mode) == 0o700
    policy = verify('kb-containment-policy', json.loads((authority / 'policy.json').read_text()), key.public_key())
    outbox = verify('kb-containment-policy', json.loads((rt.state_dir / 'outbox/containment-policy.json').read_text()), key.public_key())
    state = verify('kb-containment-decision', json.loads((authority / 'authority.json').read_text()), key.public_key())
    assert policy == outbox
    assert state == {'schema_version': 1, 'generation': 1, 'consumers': [], 'decisions': []}
    assert {k: policy[k] for k in state} == state
    assert refreshed['generation'] == 1
    assert policy['issued_at'] <= time.time() < policy['expires_at']
    assert rt.ledger.live_lease() == rt.lease_owner
    assert not native.exists()
    assert not (authority / 'acks').exists()


@pytest.mark.parametrize('mode', [0o775, 0o777])
def test_collect_rejects_existing_writable_authority_without_repair(leased_authority, mode):
    rt, _key, native = leased_authority
    authority = rt.containment_policy_dir
    authority.mkdir(mode=0o700)
    authority.chmod(mode)

    with pytest.raises(ContainmentError, match='owner-controlled'):
        collect_consumer_updates(rt)

    assert stat.S_IMODE(authority.stat().st_mode) == mode
    assert not (authority / 'consumer-import').exists()
    assert not (authority / 'authority.json').exists()
    assert not (authority / 'policy.json').exists()
    assert not (rt.state_dir / 'outbox/containment-policy.json').exists()
    assert rt.ledger.live_lease() == rt.lease_owner
    assert not native.exists()
