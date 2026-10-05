"""The browser's graph model preserves layout without trusting source status."""
import shutil
import subprocess
from pathlib import Path

import pytest


NODE = shutil.which("node")
MODULE = Path(__file__).resolve().parents[1] / "src/infermatrix_copilot/rfc_service/web/roadmap-graph.mjs"


@pytest.mark.skipif(not NODE, reason="Node is required for browser graph contracts")
@pytest.mark.parametrize("check", [
    r"""
const rfc={body:'### Old format\n```mermaid\nflowchart LR\nBASE[Baseline] --> F1[Original label]\nF1 --> F2[Next]\nclass F1 complete\nclick F1 \"javascript:alert(1)\"\n```',
 features:[{id:'F1',title:'First',track:'Engine',implementation:'partial',acceptance:'pending',depends_on:[]},{id:'F2',title:'Second',track:'Engine',depends_on:[],overrides:{depends_on:[]}}]};
const [model]=graphModels(rfc);
assert.equal(model.title,'Old format');
assert.equal(model.nodes.find(n=>n.id==='F1').title,'Original label');
assert.deepEqual(model.edges.map(e=>[e.from,e.to]),[['BASE','F1']]);
const source=graphSource(model,x=>x);
assert.match(source,/:::partial/); assert.match(source,/验收：pending/);
assert.doesNotMatch(source,/click|javascript:|class F1 complete/);
delete rfc.features[1].overrides;
assert(graphModels(rfc)[0].edges.some(e=>e.from==='F1'&&e.to==='F2'));
""",
    r"""
const features=[{id:'F1',title:'Removed',track:'Engine',dropped:true},{id:'F2',title:'Live',track:'Engine',depends_on:['F1']},{id:'F3',title:'Added',track:'Engine',depends_on:['F2']}];
const [model]=graphModels({body:'```mermaid\nflowchart LR\nF1[Old] --> F2[Live]\n```',features});
assert(!model.nodes.some(n=>n.id==='F1'));
assert(model.nodes.some(n=>n.id==='F3'));
assert.deepEqual(model.edges.map(e=>[e.from,e.to]),[['F2','F3']]);
""",
    r"""
const body=Array.from({length:4},(_,i)=>`### Track ${i}\n\`\`\`mermaid\nflowchart LR\nA${i}[Context] --> F${i}[Work]\n\`\`\``).join('\n');
const features=Array.from({length:4},(_,i)=>({id:`F${i}`,title:'Same title',track:`Track ${i}`,depends_on:[]}));
assert.equal(graphModels({body,features}).length,4);
assert.equal(graphModels({body:'',features:[{id:'F1',title:'Same title',depends_on:[]}]}).length,1);
assert.equal(graphModels({features:[]}).length,0);
""",
    r"""
const model=graphModels({features:[{id:'bad-id',title:'\"]\\nclick N0 javascript:alert(1) <img onerror=alert(1)>',owner:'<script>bad</script>',implementation:'implemented',acceptance:'pending',depends_on:[]}]})[0];
const source=graphSource(model,x=>x);
assert(!source.includes('<img')); assert(!source.includes('<script>'));
assert(!source.includes('\nclick')); assert(source.includes('#quot;'));
assert(source.startsWith('flowchart LR\nN0['));
assert(!source.includes(':::accepted'));
""",
    r"""
const rfc={features:[{id:'F1',title:'Stable layout',track:'Engine',depends_on:[],implementation:'planned',acceptance:'pending',owner:''}]};
const initial=graphSource(graphModels(rfc)[0],x=>x,true);
rfc.features[0].implementation='implemented'; rfc.features[0].owner='New owner'; rfc.features[0].acceptance='accepted';
assert.equal(graphSource(graphModels(rfc)[0],x=>x,true),initial);
rfc.features[0].title='Changed work';
assert.notEqual(graphSource(graphModels(rfc)[0],x=>x,true),initial);
""",
    r"""
const rfc={body:'### Source one\n```mermaid\nflowchart LR\nBASE[Baseline] --> F1[First]\nF1 --> AFTER1[After first]\n```\n### Source two\n```mermaid\nflowchart LR\nSTART2[Other context] --> F2[Second]\nF2 --> AFTER2[After second]\n```',
features:[{id:'F1',title:'First',track:'Engine',implementation:'implemented',acceptance:'pending',depends_on:[]},
{id:'F2',title:'Second',track:'Models',implementation:'planned',acceptance:'pending',depends_on:['F1']}],
node_groups:[{id:'group-pair',title:'Shared delivery',feature_ids:['F1','F2']}]};
const before=JSON.stringify(rfc); const models=graphModels(rfc); assert.equal(models.length,1);
const model=models[0], group=model.nodes.find(node=>node.group);
assert.equal(group.id,'group-pair'); assert.equal(group.title,'Shared delivery (2)');
assert.equal(group.feature.title,'Shared delivery'); assert.deepEqual(group.members.map(f=>f.id),['F1','F2']);
assert.equal(group.feature.implementation,'partial'); assert.equal(group.feature.complete,false);
assert.equal(group.feature.acceptance,'pending'); assert.equal(group.feature.counts.implemented,1);
assert(!model.nodes.some(n=>['F1','F2'].includes(n.id)));
assert.deepEqual(model.edges.map(e=>[e.from,e.to]),[['BASE','group-pair'],['group-pair','AFTER1'],['START2','group-pair'],['group-pair','AFTER2']]);
assert.equal(JSON.stringify(rfc),before);
const exported=graphSource(model,x=>x); assert.match(exported,/实现 1\/2 · 验收 0\/2/);
assert.equal(model.title,'Source one / Source two');
""",
    r"""
const features=[{id:'F1',title:'Same title',track:'Engine',implementation:'implemented',acceptance:'accepted',complete:true,depends_on:['BASE']},
{id:'F2',title:'Same title',track:'Models',implementation:'implemented',acceptance:'pending',complete:false,depends_on:['BASE']},
{id:'BASE',title:'Context task',track:'Shared',depends_on:[]},
{id:'NEXT',title:'Remaining',track:'Follow-on',depends_on:['F1','F2']}];
const rfc={features,node_groups:[{id:'group-main',title:'Same title',feature_ids:['F1','F2']}]};
const models=graphModels(rfc); const groupModels=models.filter(model=>model.nodes.some(node=>node.id==='group-main'));
assert.equal(groupModels.length,1); const model=groupModels[0];
assert(model.nodes.some(n=>n.id==='BASE')); assert(model.nodes.some(n=>n.id==='NEXT'));
assert.deepEqual(model.edges.map(e=>[e.from,e.to]),[['BASE','group-main'],['group-main','NEXT']]);
const group=model.nodes.find(n=>n.group);
assert.equal(group.feature.implementation,'implemented'); assert.equal(group.feature.acceptance,'pending');
assert.equal(group.feature.complete,false); assert.deepEqual(group.feature.counts,{total:2,implemented:2,accepted:1,partial:0,in_progress:0,blocked:0,planned:0});
assert.equal(group.feature.owner,'');
const initial=graphSource(model,x=>x,true);
features[1].acceptance='accepted'; features[1].complete=true; features[0].owner='Alice';
const acceptedModel=graphModels(rfc).find(m=>m.nodes.some(n=>n.id==='group-main'));
assert.equal(graphSource(acceptedModel,x=>x,true),initial);
assert.equal(acceptedModel.nodes.find(n=>n.group).feature.complete,true);
assert.match(graphSource(acceptedModel,x=>x),/:::accepted/);
assert.equal(acceptedModel.nodes.find(n=>n.group).feature.owner,'');
features[1].owner='Alice'; assert.equal(graphModels(rfc)[0].nodes.find(n=>n.group).feature.owner,'Alice');
""",
    r"""
const features=[{id:'A',title:'A',track:'One',depends_on:[]},{id:'B',title:'B',track:'Two',depends_on:['A']},
{id:'C',title:'C',track:'Three',depends_on:['B']},{id:'D',title:'D',track:'Four',depends_on:['C']},
{id:'NEXT',title:'Next',track:'Five',depends_on:['A','B','C','D']}];
const node_groups=[{id:'group-ab',title:'Shared',feature_ids:['A','B']},{id:'group-cd',title:'Shared',feature_ids:['C','D']}];
const models=graphModels({features,node_groups}); assert.equal(models.length,1);
assert.deepEqual(models[0].nodes.filter(n=>n.group).map(n=>n.id),['group-ab','group-cd']);
assert.deepEqual(models[0].edges.map(e=>[e.from,e.to]),[['group-ab','group-cd'],['group-ab','NEXT'],['group-cd','NEXT']]);
assert.deepEqual(models[0].nodes.find(n=>n.id==='group-cd').feature.depends_on,['group-ab']);
const before=graphModels({features}); assert.deepEqual(graphModels({features,node_groups:[]}),before);
assert.deepEqual(graphModels({features,node_groups:node_groups.filter(g=>g.id!=='group-ab')})[0].nodes.filter(n=>n.feature&&!n.group).map(n=>n.id),['A']);
""",
    r"""
const features=[{id:'LIVE',title:'Live',track:'Work',depends_on:[]},{id:'DELETED',title:'Removed',track:'Work',dropped:true},
{id:'OTHER',title:'Other',track:'Work',depends_on:['LIVE']}];
const rfc={body:'```mermaid\nflowchart LR\nLIVE[Live] --> DELETED[Removed]\nDELETED --> OTHER[Other]\n```',features};
const initial=graphModels(rfc);
for (const feature_ids of [['DELETED','MISSING'],['LIVE','DELETED','MISSING'],['LIVE','LIVE','DELETED']]) {
assert.deepEqual(graphModels({...rfc,node_groups:[{id:'group-deleted',title:'Archived',feature_ids}]}),initial);
}
const active=graphModels({...rfc,node_groups:[{id:'group-active',title:'Active',feature_ids:['LIVE','OTHER','DELETED','MISSING']}]})[0];
assert.equal(active.nodes.length,1); assert.deepEqual(active.nodes[0].members.map(f=>f.id),['LIVE','OTHER']);
assert.equal(active.nodes[0].counts.total,2); assert.equal(active.edges.length,0);
assert.deepEqual(active.nodes[0].group.feature_ids,['LIVE','OTHER','DELETED','MISSING']);
""",
    r"""
const features=[{id:'A',title:'A',depends_on:[],implementation:'partial',acceptance:'accepted',complete:false},
{id:'B',title:'B',depends_on:[],implementation:'planned',acceptance:'failing',complete:false}];
const rfc={features,node_groups:[{id:'group-ab',title:'Group',feature_ids:['A','B']}]};
const initial=graphSource(graphModels(rfc)[0],x=>x,true);
let group=graphModels(rfc)[0].nodes[0]; assert.equal(group.feature.implementation,'partial'); assert.equal(group.feature.acceptance,'failing');
assert.equal(group.feature.complete,false); assert.equal(group.counts.accepted,0);
features[0].implementation='blocked'; features[0].acceptance='pending';
group=graphModels(rfc)[0].nodes[0]; assert.equal(group.feature.implementation,'blocked');
features[0].implementation='in_progress'; features[1].acceptance='pending';
assert.equal(graphModels(rfc)[0].nodes[0].feature.implementation,'in_progress');
assert.equal(graphSource(graphModels(rfc)[0],x=>x,true),initial);
rfc.node_groups[0].title='Renamed'; assert.notEqual(graphSource(graphModels(rfc)[0],x=>x,true),initial);
rfc.node_groups=[]; assert.notEqual(graphSource(graphModels(rfc)[0],x=>x,true),initial);
""",
    r"""
const title='"]\nclick N0 "javascript:alert(1)" <svg onload=alert(1)> #quot; \\';
const features=[{id:'weird\nA"',title:'One',depends_on:[]},{id:'weird\\B',title:'Two',depends_on:[]}];
const model=graphModels({features,node_groups:[{id:'group-"\nclick BAD',title,feature_ids:features.map(f=>f.id)}]})[0];
model.edges.push({from:model.nodes[0].id,to:model.nodes[0].id,label:title});
const source=graphSource(model,x=>x);
assert(source.startsWith('flowchart LR\nN0[')); assert(!source.includes('\nclick'));
assert(!source.includes('<svg')); assert(!source.includes('group-')); assert(!source.includes('weird'));
assert(source.includes('#quot;')); assert(source.includes('#35;quot;')); assert(source.includes('#92;'));
assert.equal(source.split('\n').filter(line=>line.startsWith('N0[')).length,1);
const standalone=graphSource({nodes:[{id:'A\0B',title:'Title\\'},{id:'C',title:'C'},{id:'A',title:'A'},{id:'B\0C',title:'Other'}],
edges:[{from:'A\0B',to:'C'},{from:'A',to:'B\0C'}]},x=>x);
assert.equal(standalone.split('\n').filter(line=>line.includes(' --> ')).length,2);
""",
    r"""
const features=[{id:'A',title:'A',depends_on:[]},{id:'B',title:'B',depends_on:[]},{id:'C',title:'C',depends_on:[]}];
const model=graphModels({features,node_groups:[{id:'group-ab',title:'AB',feature_ids:['A','B']},
{id:'group-duplicate',title:'Duplicate',feature_ids:['B','C']},
{id:'C',title:'Identifier collision',feature_ids:['A','C']}]})[0];
assert.deepEqual(model.nodes.map(n=>n.id),['group-ab','C']);
assert.equal(model.nodes.filter(n=>n.group).length,1);
""",
])
def test_graph_tracking_contract(check):
    program = "import assert from 'node:assert/strict';\n" + f"import {{graphModels,graphSource}} from {MODULE.as_uri()!r};\n" + check
    result = subprocess.run([NODE, "--input-type=module"], input=program, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
