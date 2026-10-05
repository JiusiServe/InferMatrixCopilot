"""Reproduce a bounded native feature-discovery pilot without publishing a catalog.

Explicit pilot scopes are reported separately from the repository's full
inventory. All native traces and resumable checkpoints belong outside Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from infermatrix_copilot.config import Settings
from infermatrix_copilot.kb_service.depth_pacing import SharedZcodePacer
from infermatrix_copilot.kb_service.feature_discovery_index import build_discovery_index
from infermatrix_copilot.kb_service.init_feature_discovery import DiscoveryEngine, _FeatureDiscovery
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.trace_store import TraceStore
import yaml


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--pin', required=True)
    p.add_argument('--source-root', action='append', required=True)
    p.add_argument('--doc-glob', action='append', default=[])
    p.add_argument('--test-glob', action='append', default=[], help='explicit pilot test scope; empty means no tests offered')
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--repo', required=True)
    p.add_argument('--judge-model', default='codex:gpt-6.1-sol:medium')
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.state.resolve().is_relative_to(ROOT):
        p.error('native state must be outside the Git worktree')
    args.state.mkdir(parents=True, exist_ok=True)
    runtime_files = ['eval/feature-discovery/run_pilot.py',
        'src/infermatrix_copilot/kb_service/init_feature_discovery.py',
        'src/infermatrix_copilot/kb_service/feature_discovery_index.py',
        'src/infermatrix_copilot/kb_service/models.py',
        'src/infermatrix_copilot/kb_service/runtime.py']
    runtime_hashes = {name:hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in runtime_files}
    runtime_archive = args.state / 'runtime'
    for name in runtime_files:
        target = runtime_archive / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    manifest = {'runtime_sha256':runtime_hashes, 'concurrency':13,
        'scope':{'source_roots':args.source_root,'doc_globs':args.doc_glob,'test_globs':args.test_glob},
        'pin':args.pin, 'repo':args.repo, 'billing':'subscription', 'actual_cost_usd':None}
    (args.state / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    roles = {'generator': ModelRole.parse('generator', 'zcode:GLM-5.3'),
             'judge': ModelRole.parse('judge', args.judge_model)}
    store = TraceStore(args.state / 'init/traces')
    gateway = ModelGateway(Settings(_env_file=None), recorder=trace_recorder(store))
    gateway.configure_zcode_pacing(SharedZcodePacer(args.state / 'pacing.json'))
    for role in roles.values():
        if not gateway.subscription_billing(role):
            raise RuntimeError('both roles require authenticated subscription billing')
    index = build_discovery_index(args.source, pin=args.pin,
        scope={'roots': args.source_root, 'exclude': ['*/node_modules/*', '*/vendor/*', '*/generated/*']},
        doc_globs=args.doc_glob, cache_path=args.state / 'index.json')
    import fnmatch
    from infermatrix_copilot.kb_service.feature_discovery_index import DiscoveryIndex, _sha
    data = dict(index.data)
    data['tests'] = [path for path in index.tests if any(fnmatch.fnmatchcase(path, pattern) for pattern in args.test_glob)]
    index = DiscoveryIndex(data, _sha(data))
    seed = yaml.safe_load(args.catalog.read_text())['features']
    identity = hashlib.sha256(json.dumps({'index': index.sha256, 'seed': seed, 'models': {k:v.label() for k,v in roles.items()}, 'runtime':runtime_hashes}, sort_keys=True).encode()).hexdigest()
    checkpoint = args.state / 'checkpoint.json'
    state = json.loads(checkpoint.read_text()) if checkpoint.exists() else {'identity': identity}
    if state['identity'] != identity: raise RuntimeError('pilot inputs changed')
    def save():
        temporary = checkpoint.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, ensure_ascii=False))
        temporary.replace(checkpoint)
    archive_verifier = _FeatureDiscovery.__new__(_FeatureDiscovery)
    archive_verifier.rt = SimpleNamespace(state_dir=args.state)
    def call(role, system, prompt, validate):
        result = gateway.call_json(roles[role], system=system, prompt=prompt, validate=validate)
        archive_verifier._verify_native_receipt(result)
        print(json.dumps({'role': role, 'trace_id': result.trace_id, 'served_model': result.served_model or None, 'seconds': result.seconds}), flush=True)
        return result
    engine = DiscoveryEngine(index, seeds=seed, owners=sorted({f['owner'] for f in seed}), state=state,
        call=call, save=save, concurrency=13, repository=args.repo, pin=args.pin)
    complete = engine.scan() and engine.review()
    features, outcomes = engine.catalog('repos/' + args.repo.split('/')[-1])
    records = store.query(kind='model_call', limit=10000)
    report = {'schema_version':1, 'kind':'bounded-native-pilot', 'repo':args.repo, 'pin':args.pin,
        'scope':{'source_roots':args.source_root, 'doc_globs':args.doc_glob, 'test_globs':args.test_glob},
        'pilot_complete':complete, 'full_repository_discovery':False, 'formal_catalog_modified':False,
        'inventory':{'production':len(index.production),'docs':len(index.docs),'tests':len(index.tests)},
        'seed_features':len(seed),'proposed_features':len(features),'candidates':outcomes,
        'unknown_tasks':sum(t['status']=='unknown' for t in state['tasks'].values()),
        'native_calls':[{'id':r['id'],'model':r['model'],'seconds':r['seconds'],'usage':r['usage'],'error':r['error']} for r in records],
        'actual_cost_usd':None, 'state_archive':str(args.state),'index_sha256':index.sha256,
        'checkpoint_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        'runtime_sha256':runtime_hashes, 'concurrency':13,
        'index_version':index.identity['version'],
        'manifest_sha256':hashlib.sha256((args.state / 'manifest.json').read_bytes()).hexdigest(),
        'limitations':'Explicit pilot scope only; no claim of complete discovery or upstream test execution.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'pilot_complete':complete,'calls':len(records),'proposed_features':len(features)},ensure_ascii=False),flush=True)

if __name__ == '__main__': main()
