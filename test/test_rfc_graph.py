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
])
def test_graph_tracking_contract(check):
    program = "import assert from 'node:assert/strict';\n" + f"import {{graphModels,graphSource}} from {MODULE.as_uri()!r};\n" + check
    result = subprocess.run([NODE, "--input-type=module"], input=program, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
