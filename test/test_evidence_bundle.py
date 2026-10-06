import hashlib
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.evidence_bundle import (
    affected_features, build_evidence_bundle, materialize_bundle,
)


def bundle(tmp_path):
    path = tmp_path / 'library.py'
    path.write_text('def exported():\n    return 1\n')
    idx = SimpleNamespace(identity={'pin': 'a' * 40, 'scope': {'roots': ['.']}},
        sha256='b' * 64, entries={'library.py': {'status': 'ready', 'kind': 'source',
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'lines': path.read_text().splitlines()}})
    ref = {'path': 'library.py', 'start': 1, 'end': 2}
    return build_evidence_bundle(idx, 'exported', catalog_hash='c' * 64,
                                 refs=[ref, ref], unit_ids=['one', 'one'])


def test_discovery_handoff_contains_exact_source_span(tmp_path):
    value = bundle(tmp_path)
    result = materialize_bundle(value, tmp_path, pin='a' * 40, catalog_hash='c' * 64)
    assert len(value['refs']) == 1 and value['unit_ids'] == ['one']
    assert result[0]['text'] == '1: def exported():\n2:     return 1'
    assert affected_features({'exported': value}, ['library.py']) == ['exported']


@pytest.mark.parametrize('change', ['body', 'source', 'pin', 'catalog'])
def test_changed_discovery_handoff_fails_closed(tmp_path, change):
    value = bundle(tmp_path)
    pin, catalog = 'a' * 40, 'c' * 64
    if change == 'body': value['feature_id'] = 'other'
    if change == 'source': (tmp_path / 'library.py').write_text('return 2\n')
    if change == 'pin': pin = 'd' * 40
    if change == 'catalog': catalog = 'd' * 64
    with pytest.raises(ValueError):
        materialize_bundle(value, tmp_path, pin=pin, catalog_hash=catalog)
