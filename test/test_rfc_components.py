"""RFC component projections preserve source context and separate evidence from prose."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest


NODE = shutil.which("node")
WEB = Path(__file__).resolve().parents[1] / "src/infermatrix_copilot/rfc_service/web"
MODULE = WEB / "roadmap-components.mjs"
MARKDOWN = WEB / "markdown-it.min.js"

# Representative excerpts use the headings and feature identifiers of wm-7074.
WORLD_MODEL = """## Topic
This RFC expands a reusable **world-model realtime inference** roadmap.

## LingBot delivery and next steps — 2026-09-25
The September core implementation targets have landed.

## Live PR status
| PR | State |
| --- | --- |
| #6844 | merged |
<!-- roadmap-people: {"6844":{"author":"BruceLoveDecimal"}} -->
<!-- roadmap-status:end -->

## Motivation
One reusable engine should support heterogeneous model bottlenecks.

### Goals
- LingBot reaches at least **12 generated FPS on no more than four H200 GPUs**.
- One request equals one session; one `AsyncOmni.generate()` yields many chunks.

### Non-goals
- NPU enablement in this roadmap.

## Current and Target Execution Semantics
### Historical experimental path (before #6844)
One generate call was made per tick.

### Normal stepwise path (stepwise, streaming decode and camera interaction merged)
One external request retains session-owned state.

## Models
LingBot, MiniMax H3, ABot, and Echo-WM expose different compute bottlenecks.

## Performance Analysis
### Measurement requirements
Report reproducible latency and quality evidence.

### Current measured H200 matrix
| Model | FPS |
| --- | --- |
| LingBot | 14.5 |

### Theoretical H200 estimation
This is a theoretical estimate, not a release acceptance.

### Estimated optimization ceiling
Expected latency is a proposal.

### Local four-GPU pipeline measurement (2026-09-08 to 2026-09-10)
The local mock is evidence toward the gate, not the gate passed.

### MiniMax H3 theoretical-estimation gate
Calibrate against a real baseline.

### Cross-model evidence: ABot and Echo-WM
Separate measured and theoretical results.

### Performance conclusions and priority
Profile DiT and decode independently.

## Feature Roadmap
### Engine features (E)
#### E1. One request, many chunks: stepwise AR-Diffusion — P0
One long-lived generation request replaces per-tick generation.
##### E1 validation details
Validate session isolation.

#### E2. Normal realtime serving and structured interaction — P1
Serve streaming output through the normal realtime path.

### LingBot features (L)
#### L1. Current-geometry paging correctness
Use current latent geometry.

### MiniMax H3 features (M)
#### M1. Base CUDA integration — v0.29 P0
Integrate the native offline baseline.

### Other model considerations
Keep ABot and Echo-WM visible as follow-on models.

## Task Architecture and Feature Dependencies
### Engine dependency graph
```mermaid
flowchart LR
E1[Stepwise] --> E2[Realtime]
```

## Timeline and PR Order
The original delivery schedule is historical.
### September execution order (original plan; core merges completed 2026-09-07)
The core merge date describes a historical snapshot.

## Acceptance Criteria
### Engine-side
- Sessions invoke external generate exactly once.
### LingBot model-side
- Initial release reaches 12 FPS with stated decode placement.
### MiniMax H3 model-side
- The baseline reports native cadence and latency.
### Reference and follow-on models
- Do not claim realtime readiness from DiT-only FPS.

## PR Review Contract
Review measured wall-time and quality evidence.

## Risks and Open Questions
State ownership and decoder quality remain separate concerns.
### Feedback Period
Invite team review.

## Related Work
An umbrella RFC establishes common world-model contracts.

## Four-H200 500 ms end-to-end experiment plan
Target cadence is a proposed experiment.
### Historical measured state, 2026-09-16
The earlier measured state is historical.

## Unclassified project-specific chapter
Keep this exact project-specific explanation.
"""


def run_contract(check, body=""):
    program = (
        "import assert from 'node:assert/strict';\n"
        "import {createRequire} from 'node:module';\n"
        f"import {{projectRFC,outcomeModel,sectionRules}} from {MODULE.as_uri()!r};\n"
        f"const md=createRequire(import.meta.url)({str(MARKDOWN)!r})({{html:false}});\n"
        f"const body={json.dumps(body)};\n" + check
    )
    result = subprocess.run([NODE, "--input-type=module"], input=program, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


pytestmark = pytest.mark.skipif(not NODE, reason="Node is required for RFC component browser contracts")


def test_world_model_sections_are_exclusive_and_claims_remain_source_claims():
    run_contract(r"""
const original=body, p=projectRFC(body,md);
assert.equal(body,original);
assert.deepEqual(p.goals.map(s=>s.title),['Goals']);
assert.deepEqual(p.scope.map(s=>s.title),['Non-goals']);
assert.equal(Object.keys(p.featureSections).length,4);
assert.equal(p.featureSections.E1.length,2);
assert.equal(p.featureSections.E1[1].featureId,'E1');
const categories=['overview','goals','scope','design','risks','references','supplement','acceptance'];
for(const key of categories) {
  assert(!p[key].some(s=>s.featureId),`${key} repeats feature descriptions`);
  assert(!p[key].some(s=>/roadmap-people|roadmap-status|flowchart LR/.test(s.markdown)));
}
assert.equal(p.acceptance.length,4);
assert(!p.design.some(s=>/model-side/.test(s.title)));
assert(p.references.some(s=>s.title==='Related Work'));
assert(p.risks.some(s=>s.title==='Feedback Period'));
assert(p.design.some(s=>s.title==='Four-H200 500 ms end-to-end experiment plan'&&s.claim==='source'));
assert(p.design.filter(s=>/measured|measurement|estimat|conclusions/i.test(s.title)).every(s=>s.claim==='source'));
for(const title of ['LingBot delivery and next steps — 2026-09-25','Live PR status','Timeline and PR Order','Historical measured state, 2026-09-16']) {
 assert(p.supplement.some(s=>s.title===title&&s.claim==='historical'),title);
 assert(!p.design.some(s=>s.title===title));
}
assert(p.supplement.some(s=>s.markdown==='Keep this exact project-specific explanation.'));
const result=outcomeModel({features:[{id:'E1',implementation:'implemented'}],criteria:[]},p);
assert.equal(result.implementation.implemented,1);
assert.equal(result.verified.length,0);
assert.equal(result.acceptance.passed,0);
""", WORLD_MODEL)


def test_parser_heading_hierarchy_source_positions_and_non_heading_code():
    run_contract(r"""
const p=projectRFC(body,md);
assert.equal(p.goals.length,2);
assert.equal(p.goals[0].title,'Goals');
assert.equal(p.goals[0].startLine,6);
assert.equal(p.goals[0].endLine,9);
assert.equal(p.goals[1].title,'Performance target');
assert.equal(p.goals[1].category,'goals');
assert.equal(p.goals[1].parentId,p.goals[0].id);
assert(p.goals[1].markdown.includes('## not a heading'));
assert(p.goals[1].markdown.includes('<!-- literal comment in a code sample -->'));
assert(!p.tree.flatMap(s=>s.children).some(s=>s.title==='hidden heading'));
assert(!p.goals.some(s=>s.title==='not a heading'));
assert.equal(p.goals[1].level,3);
assert.equal(p.scope[0].startLine,20);
const root=p.tree.find(s=>s.title==='RFC: Example');
assert(root.children.some(s=>s.title==='Goals'));
assert(root.subtreeEndLine===body.split('\n').length);
assert.equal(p.featureSections.RFC,undefined);
""", """# RFC: Example
<!-- roadmap-people:
## hidden heading
-->

Goals
-----
Expected outcome.

### Performance target
The latency target is a goal.
````text
## not a heading
<!-- literal comment in a code sample -->
````
~~~mermaid
flowchart LR
X[Context] --> Y[Work]
~~~
## Scope
Limited scope.
""")


def test_chinese_domains_and_unknown_sections_keep_content():
    run_contract(r"""
const p=projectRFC(body,md);
assert.equal(p.goals[0].title,'问题与目标');
assert.equal(p.scope[0].title,'包含与排除范围');
assert.equal(p.design.length,2);
assert.equal(p.acceptance[0].title,'模型侧');
assert.equal(p.risks[0].title,'模型故障');
assert.equal(p.references[0].title,'模型资料');
assert.equal(p.featureSections.F1.length,1);
assert.equal(p.featureSections.F2.length,1);
assert(p.supplement.some(s=>s.title==='额外说明'&&s.markdown==='保留原始内容。'));
assert(!p.goals[0].markdown.includes('负责人'));
assert.notEqual(p.featureSections.F1[0].id,p.featureSections.F2[0].id);
const noGoals=projectRFC('## Custom\nOnly project-specific text.',md);
assert.deepEqual(noGoals.goals,[]);
assert.equal(noGoals.supplement[0].markdown,'Only project-specific text.');
""", """# RFC：示例
## 问题与目标
改善延迟。
## 包含与排除范围
首版范围。
## 备选方案
比较成本。
## 提议设计
设计接口。
## 工作计划
### 实现
#### F1. 相同名称
负责人：Alice
#### F2. 相同名称
负责人：Bob
## 验收标准
### 模型侧
- 验证当前版本与环境。
## 风险与未决问题
### 模型故障
恢复失败。
## 参考资料
### 模型资料
来源文档。
## 额外说明
保留原始内容。
""")


def test_outcomes_require_current_evidence_and_keep_implementation_separate():
    run_contract(r"""
const p=projectRFC(body,md);
const evidence=(date,extra={})=>({revision:'abc123',environment:'Linux/H200',recorded_at:date,...extra});
const rfc={features:[
 {id:'A',title:'Merged but unaccepted',implementation:'implemented'},
 {id:'B',title:'Partly merged',implementation:'partial',blockers:['A']},
 {id:'C',title:'Ongoing',implementation:'in_progress'},
 {id:'D',title:'Blocked',state:'blocked'},
 {id:'E',title:'Removed',implementation:'implemented',dropped:true},
 {id:'F',title:'Planned',state:'planned'}],criteria:[
 {id:'C1',title:'Current pass',feature_ids:['A'],verdict:'passing',evidence:[evidence('2026-10-03'),evidence('2026-10-05')]},
 {id:'C2',title:'Stale pass',verdict:'passing',evidence:[evidence('2026-10-05',{stale:true})]},
 {id:'C3',title:'No evidence',verdict:'passing',evidence:[]},
 {id:'C4',title:'Explicit waiver',verdict:'waived',evidence:[evidence('2026-10-05')]},
 {id:'C5',title:'Failed quality',verdict:'failing',evidence:[evidence('2026-10-05')]},
 {id:'C6',title:'No environment',verdict:'passing',evidence:[{revision:'abc',recorded_at:'2026-10-05'}]},
 {id:'C7',title:'Second pass',verdict:'passing',evidence:[evidence('2026-10-04')]},
 {id:'C8',title:'Third pass',verdict:'passing',evidence:[evidence('2026-10-02')]},
 {id:'C9',title:'Fourth pass',verdict:'passing',evidence:[evidence('2026-10-01')]}]};
const snapshot=JSON.stringify(rfc), o=outcomeModel(rfc,p);
assert.equal(JSON.stringify(rfc),snapshot);
assert.deepEqual(o.implementation,{total:5,implemented:1,partial:1,inProgress:1,blocked:1,planned:1});
assert.deepEqual(o.acceptance,{total:9,passed:4,failed:1,unverified:3,waived:1});
assert.deepEqual(o.verified.map(v=>v.criterionId),['C1','C7','C8']);
assert.equal(o.verified[0].featureId,'A');
assert.equal(o.verified[0].verifiedAt,'2026-10-05T00:00:00.000Z');
assert.deepEqual(o.next.map(v=>v.id),['B','D','C5']);
assert.equal(o.next[2].criterionId,'C5');
assert(!o.verified.some(v=>v.criterionId==='C4'));
assert.equal(o.goals[0].markdown,'A 500ms target is only a proposal.');
""", "## Goals\nA 500ms target is only a proposal.\n## Performance\nThe prose says 14.5 FPS and gate passed.")


def test_empty_tracking_stale_passing_and_structured_next_targets():
    run_contract(r"""
const p=projectRFC('',md);
const empty=outcomeModel({},p);
assert.equal(empty.implementation.total,0);assert.equal(empty.acceptance.total,0);
assert.equal(empty.verified.length,0);assert.equal(empty.next[0].kind,'work');
const remaining=outcomeModel({features:[{id:'F1',title:'Same name',implementation:'implemented'},{id:'F2',title:'Same name',state:'planned'}],criteria:[
 {id:'C1',title:'Need revalidation',feature_ids:['F1'],verdict:'passing',evidence:[{revision:'x',environment:'test',stale:true}]},
 {id:'C2',title:'Unverified',verdict:'unverified',evidence:[]}]},p);
assert.deepEqual(remaining.next.map(s=>s.id),['C1','C2','F2']);
assert.equal(remaining.next[0].featureId,'F1');
assert.equal(remaining.next[0].criterionId,'C1');
assert.equal(remaining.acceptance.passed,0);
assert.equal(remaining.acceptance.unverified,2);
""")


def test_recent_evidence_sorting_accepts_service_epoch_seconds_and_iso_dates():
    run_contract(r"""
const evidence=time=>({revision:'validated',environment:'linux',recorded_at:time});
const o=outcomeModel({features:[],criteria:[
 {id:'OLD',title:'Earlier',verdict:'passing',evidence:[evidence(1790899200)]},
 {id:'LATEST',title:'Current',verdict:'passing',evidence:[evidence(1790899200),evidence(1791158400)]},
 {id:'MILLIS',title:'Milliseconds',verdict:'passing',evidence:[evidence(1791072000000)]},
 {id:'ISO',title:'ISO',verdict:'passing',evidence:[evidence('2026-10-03T00:00:00Z')]}]},projectRFC('',md));
assert.deepEqual(o.verified.map(s=>s.criterionId),['LATEST','MILLIS','ISO']);
assert.equal(o.verified[0].evidence.recorded_at,1791158400);
assert.equal(o.verified[0].verifiedAt,'2026-10-05T00:00:00.000Z');
assert.equal(o.verified[1].verifiedAt,'2026-10-04T00:00:00.000Z');
""")


def test_unsupported_diagrams_survive_as_source_while_supported_graphs_use_svg():
    run_contract(r"""
const p=projectRFC(body,md);
const source=p.design.map(s=>s.markdown).join('\n');
assert(source.includes('sequenceDiagram'));
assert(source.includes('Alice->>Bob: Retain this source'));
assert(source.includes('classDiagram'));
assert(source.includes('T[Keep tilde source]'));
assert(source.includes('U[Keep uppercase source]'));
assert(!source.includes('A[Context] --> B[Task]'));
assert.equal((source.match(/flowchart LR/g)||[]).length,2);
assert(!source.includes('graph TD'));
assert(source.includes('This supporting explanation is retained.'));
""", """## Design
### Flowchart
```mermaid
flowchart LR
A[Context] --> B[Task]
```
This supporting explanation is retained.
### Graph
```mermaid
graph TD
A[Task] --> B[Next]
```
### Sequence
```mermaid
sequenceDiagram
Alice->>Bob: Retain this source
```
### Class model
```mermaid
classDiagram
class Model
```
### Unrecognized fence syntax
~~~mermaid
flowchart LR
T[Keep tilde source]
~~~
```Mermaid
flowchart LR
U[Keep uppercase source]
```
""")
