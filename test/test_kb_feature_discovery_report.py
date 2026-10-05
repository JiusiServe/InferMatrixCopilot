"""Compact publication preserves full evidence in an immutable external file."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from infermatrix_copilot.kb_service.init_feature_discovery import (
    compact_discovery_report, write_full_discovery_report, verify_full_discovery_report,
)
from infermatrix_copilot.kb_service.init_support import InitError


def full_report():
    return {'schema_version': 1, 'repo': 'library', 'pin': 'a' * 40,
            'complete': True, 'done': True, 'catalog_sha256': 'b' * 64,
            'index_sha256': 'c' * 64, 'run_config': {'packet_chars': 96000},
            'feature_ids': ['library'], 'features': [{'id': 'library', 'owner': 'core', 'title': 'Library'}],
            'owner_requests': [], 'counts': {'unknown': 5000}, 'statistics': {'unknown': 5000},
            'catalog_boundary_audit': {'done': True, 'identity': {'version': 'boundary-v1'},
                                       'candidate_ids': ['proposal'] * 5000, 'counts': {'yes': 5000}},
            'candidates': [{'id': f'proposal-{n}', 'description': 'evidence ' * 250,
                            'reason': 'unknown ' * 250, 'generator_receipts': [{'trace_id': 'native'}],
                            'evidence': [{'path': f'src/file-{n}.py', 'start': 1, 'end': 2}]} for n in range(5000)],
            'unassociated_implementation_paths': [f'src/unmapped-{n}.py' for n in range(5000)],
            'unassociated_entry_leads': [{'path': f'src/unmapped-{n}.py', 'symbols': ['entry']} for n in range(5000)],
            'failures': [], 'scope_suggestions': [{'path': f'outside/file-{n}.py'} for n in range(5000)],
            'candidate_limit_task_ids': [f'source:{n}' for n in range(500)],
            'invalid_candidates': [{'reason': 'invalid citation'} for n in range(5000)]}


def test_large_report_is_compact_and_full_bytes_are_preserved(tmp_path):
    full = full_report()
    artifact = write_full_discovery_report(tmp_path, full)
    compact = compact_discovery_report(full, artifact)
    assert len(json.dumps(compact, ensure_ascii=False).encode()) < 100_000
    assert artifact['size_bytes'] > 10_000_000
    assert compact['candidate_count'] == 5000 and 'candidates' not in compact
    assert compact['catalog_boundary_audit']['candidate_count'] == 5000
    assert 'candidate_ids' not in compact['catalog_boundary_audit']
    assert compact['scope_suggestions']['count'] == 5000
    state = {**{k: full[k] for k in ('pin', 'catalog_sha256', 'index_sha256', 'run_config')},
             'report_format': compact['report_format'], 'full_artifact': artifact}
    assert verify_full_discovery_report(tmp_path, compact, state) == full
    raw = Path(artifact['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == artifact['sha256']
    assert write_full_discovery_report(tmp_path, full) == artifact
    assert Path(artifact['path']).read_bytes() == raw


@pytest.mark.parametrize('damage', ['escape', 'symlink', 'checkpoint_binding', 'summary', 'size', 'identity'])
def test_full_report_binding_and_containment_refuse_tampering(tmp_path, damage):
    full = full_report(); full['candidates'] = []
    artifact = write_full_discovery_report(tmp_path, full)
    compact = compact_discovery_report(full, artifact)
    state = {**{k: full[k] for k in ('pin', 'catalog_sha256', 'index_sha256', 'run_config')},
             'report_format': compact['report_format'], 'full_artifact': deepcopy(artifact)}
    if damage == 'escape':
        outside = tmp_path / 'elsewhere.json'; outside.write_bytes(Path(artifact['path']).read_bytes())
        compact['full_artifact']['path'] = str(outside); state['full_artifact'] = deepcopy(compact['full_artifact'])
    elif damage == 'symlink':
        path = Path(artifact['path']); outside = tmp_path / 'elsewhere.json'
        path.rename(outside); path.symlink_to(outside)
    elif damage == 'checkpoint_binding':
        state['full_artifact']['sha256'] = 'd' * 64
    elif damage == 'summary':
        compact['counts']['unknown'] = 0
    elif damage == 'size':
        compact['full_artifact']['size_bytes'] += 1; state['full_artifact'] = deepcopy(compact['full_artifact'])
    else:
        state['catalog_sha256'] = 'd' * 64
    with pytest.raises(InitError, match='full report artifact'):
        verify_full_discovery_report(tmp_path, compact, state)
