"""Independently recheck archived native candidates in a new audit batch.

This never resumes the original batch or publishes a formal catalog. Original
extraction receipts and frozen evidence remain available in the copied archive.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import yaml
from infermatrix_copilot.config import Settings
from infermatrix_copilot.kb_service.feature_discovery_index import DiscoveryIndex,_sha
from infermatrix_copilot.kb_service.init_feature_discovery import DiscoveryEngine,_FeatureDiscovery,SYSTEM_DISCOVER,SYSTEM_REVIEW,_hash
from infermatrix_copilot.kb_service.models import ModelGateway,ModelRole
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.trace_store import TraceStore


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-state',type=Path,required=True)
    p.add_argument('--original-report',type=Path,required=True)
    p.add_argument('--state',type=Path,required=True)
    p.add_argument('--catalog',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    if args.state.resolve().is_relative_to(ROOT) or args.state.exists():
        p.error('a fresh external state directory is required')
    before=json.loads(args.original_report.read_text())
    previous=json.loads((args.original_state/'checkpoint.json').read_text())
    data=json.loads((args.original_state/'index.json').read_text())['data']
    data['tests']=[path for path in data['tests'] if path in {r['path'] for c in before['candidates'] for r in c['evidence']}]
    index=DiscoveryIndex(data,_sha(data))
    if index.sha256!=before['index_sha256']:raise ValueError('frozen pilot evidence differs')
    shutil.copytree(args.original_state/'init/traces',args.state/'init/traces')
    store=TraceStore(args.state/'init/traces')
    imported={r['id'] for r in store.query(kind='model_call',limit=10000)}
    gateway=ModelGateway(Settings(_env_file=None),recorder=trace_recorder(store))
    roles={name:ModelRole.parse(name,value) for name,value in [('generator','zcode:GLM-5.3'),('judge','codex:gpt-6.1-sol:medium')]}
    for role in roles.values():
        if not gateway.subscription_billing(role):raise RuntimeError('both roles require subscription billing')
    seeds=yaml.safe_load(args.catalog.read_text())['features']
    state={'tasks':deepcopy(previous['tasks']),'candidates':deepcopy(previous['candidates']), 'reviews':{}}
    verifier=_FeatureDiscovery.__new__(_FeatureDiscovery)
    verifier.rt=SimpleNamespace(state_dir=args.state,generator=roles['generator'],judge=roles['judge'])
    assert not verifier._validate_saved_archives(state)
    def save():
        temp=args.state/'checkpoint.tmp';temp.write_text(json.dumps(state,ensure_ascii=False));temp.replace(args.state/'checkpoint.json')
    def call(role,system,prompt,validate):
        r=gateway.call_json(roles[role],system=system,prompt=prompt,validate=validate)
        verifier._verify_native_receipt(r)
        print(json.dumps({'role':role,'trace_id':r.trace_id,'seconds':r.seconds}),flush=True)
        return r
    engine=DiscoveryEngine(index,seeds=seeds,owners=sorted({f['owner'] for f in seeds}),state=state,
        call=call,save=save,concurrency=13,repository=before['repo'],pin=before['pin'])
    complete=engine.review();features,outcomes=engine.catalog('repos/'+before['repo'].split('/')[-1])
    records=[r for r in store.query(kind='model_call',limit=10000) if r['id'] not in imported]
    runtime={str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for name in ['src/infermatrix_copilot/kb_service/init_feature_discovery.py','src/infermatrix_copilot/providers/codex.py']:
        target=args.state/'runtime'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        runtime[name]=hashlib.sha256(target.read_bytes()).hexdigest()
    report={'schema_version':1,'kind':'independent-existing-candidate-recheck','repo':before['repo'],'pin':before['pin'],
        'complete':complete,'full_repository_discovery':False,'formal_catalog_modified':False,
        'original_report_sha256':hashlib.sha256(args.original_report.read_bytes()).hexdigest(),
        'original_archive':str(args.original_state),'archive':str(args.state),'inventory':before['inventory'],
        'seed_features':len(seeds),'proposed_features':len(features),'candidates':outcomes,
        'native_calls':[{'id':r['id'],'model':r['model'],'usage':r['usage'],'seconds':r['seconds'],'error':r['error']} for r in records],
        'actual_cost_usd':None,'prompt_sha256':_hash([SYSTEM_DISCOVER,SYSTEM_REVIEW]),'runtime_sha256':runtime,
        'checkpoint_sha256':hashlib.sha256((args.state/'checkpoint.json').read_bytes()).hexdigest(),
        'limitations':'Fresh review of archived generation; extraction not rerun. Explicit original scope only; upstream tests not executed.'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'complete':complete,'calls':len(records),'accepted':sum(c['status']=='accepted' for c in outcomes)}),flush=True)

if __name__=='__main__':main()
