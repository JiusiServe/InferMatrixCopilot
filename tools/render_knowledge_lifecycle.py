"""Render the knowledge lifecycle and its complete source-derived class inventory.

This tool uses only the standard library and never imports product modules. Its
outputs are deterministic for a given source tree, HEAD and generator version.
The SVG is a conceptual responsibility map; the expandable HTML is the full
Python declaration inventory, including private, nested and function-local
classes. Run again after source edits to refresh the hashes and counts.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PACKAGE = Path("src/infermatrix_copilot")
WIDTH, HEIGHT = 1600, 1350
GROUPS = {
    "init": "核心能力 · 初始化",
    "maintain": "核心能力 · 维护与纠错",
    "content": "核心能力 · 内容与原始证据",
    "assurance": "核心能力 · 审核与准入",
    "distribution": "核心能力 · 分发与撤回",
    "support": "核心能力 · 模型、预算与持久状态",
}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def capability(relative: Path) -> tuple[str, str]:
    parts = relative.parts[2:]
    stem = relative.stem
    if parts[0] not in {"kb_service", "knowledge_service"}:
        owner = ".".join(parts[:-1]) or "package"
        return "external-" + owner.replace(".", "-"), "外部附录 · " + owner
    if parts[0] == "knowledge_service":
        if stem in {"gate_verifier", "verdict", "release_audit"}:
            return "assurance", GROUPS["assurance"]
        if stem in {"containment", "signing"}:
            return "distribution", GROUPS["distribution"]
        return "content", GROUPS["content"]
    if stem.startswith("init_") or stem.startswith("portable_") or stem == "repo_spec":
        return "init", GROUPS["init"]
    if stem.startswith("maintenance") or stem in {"scheduler", "runtime", "sweep", "intake", "refine"}:
        return "maintain", GROUPS["maintain"]
    if stem in {"gate", "local_gate", "calibration", "accept"}:
        return "assurance", GROUPS["assurance"]
    if stem in {"publisher", "activate", "outbox", "reconcile"} or stem.startswith("containment"):
        return "distribution", GROUPS["distribution"]
    if stem in {"sources", "source_links", "git_source", "evidence", "evidence_bundle", "upstream_facts"}:
        return "content", GROUPS["content"]
    return "support", GROUPS["support"]


class ClassInventory(ast.NodeVisitor):
    """Keep lexical function scopes that ast.walk alone would discard."""

    def __init__(self, path: Path, source: str, file_hash: str) -> None:
        self.path = path
        parts = list(path.with_suffix("").parts[1:])
        if parts[-1] == "__init__":
            parts.pop()
        self.module = ".".join(parts)
        self.source = source
        self.file_hash = file_hash
        self.scopes: list[tuple[str, str]] = []
        self.classes: list[dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qual_parts: list[str] = []
        for name, kind in self.scopes:
            qual_parts.append(name)
            if kind == "function":
                qual_parts.append("<locals>")
        qual_parts.append(node.name)
        qualname = ".".join(qual_parts)
        bases = [ast.unparse(base) for base in node.bases]
        decorators = [ast.unparse(item) for item in node.decorator_list]
        if any("dataclass" in item for item in decorators):
            kind = "record"
        elif any(base.rsplit(".", 1)[-1] in {"Protocol"} for base in bases):
            kind = "protocol"
        elif any(base.endswith(("Error", "Exception")) for base in bases):
            kind = "exception"
        else:
            kind = "class"
        group, label = capability(self.path)
        docstring = ast.get_docstring(node) or ""
        self.classes.append({
            "id": f"{self.module}:{qualname}@L{node.lineno}",
            "module": self.module,
            "name": node.name,
            "qualname": qualname,
            "path": self.path.as_posix(),
            "line": node.lineno,
            "end_line": node.end_lineno,
            "bases": bases,
            "decorators": decorators,
            "kind": kind,
            "private": node.name.startswith("_"),
            "nested": any(item[1] == "class" for item in self.scopes),
            "function_local": any(item[1] == "function" for item in self.scopes),
            "core": self.path.parts[2] in {"kb_service", "knowledge_service"},
            "capability": group,
            "capability_label": label,
            "file_sha256": self.file_hash,
            "definition_sha256": digest((ast.get_source_segment(self.source, node) or "").encode()),
            "doc_summary": " ".join(docstring.split())[:360],
        })
        self.scopes.append((node.name, "class"))
        self.generic_visit(node)
        self.scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scopes.append((node.name, "function"))
        self.generic_visit(node)
        self.scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef


def collect(repo: Path) -> dict[str, Any]:
    classes: list[dict[str, Any]] = []
    files = []
    ast_count = 0
    for path in sorted((repo / PACKAGE).rglob("*.py")):
        relative = path.relative_to(repo)
        raw = path.read_bytes()
        source = raw.decode("utf-8")
        tree = ast.parse(source, filename=relative.as_posix())
        file_hash = digest(raw)
        visitor = ClassInventory(relative, source, file_hash)
        visitor.visit(tree)
        classes.extend(visitor.classes)
        class_count = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        assert class_count == len(visitor.classes), relative
        ast_count += class_count
        files.append({"path": relative.as_posix(), "sha256": file_hash, "class_count": class_count})
    ids = [item["id"] for item in classes]
    assert len(ids) == len(set(ids)) == ast_count, "Class identities must be unique and complete"
    counts = {
        "provider": len(classes),
        "core": sum(item["core"] for item in classes),
        "kb_service": sum(item["path"].startswith("src/infermatrix_copilot/kb_service/") for item in classes),
        "knowledge_service": sum(item["path"].startswith("src/infermatrix_copilot/knowledge_service/") for item in classes),
        "function_local": sum(item["function_local"] for item in classes),
        "nested": sum(item["nested"] for item in classes),
        "private": sum(item["private"] for item in classes),
    }
    counts["external"] = counts["provider"] - counts["core"]
    assert counts["core"] == counts["kb_service"] + counts["knowledge_service"]
    tree_bytes = "".join(f"{item['path']}\0{item['sha256']}\n" for item in files).encode()
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return {
        "schema_version": 1,
        "scope": "Every ast.ClassDef under src/infermatrix_copilot/**/*.py; tests and tools excluded",
        "id_format": "module:lexical.qualname@Lline; function scopes include <locals>",
        "source_commit": result.stdout.strip() if result.returncode == 0 else None,
        "source_tree_sha256": digest(tree_bytes),
        "source_file_count": len(files),
        "counts": counts,
        "files": files,
        "classes": classes,
    }


def render_svg(inventory: dict[str, Any]) -> str:
    counts = inventory["counts"]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" id="lifecycle-svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="diagram-title diagram-desc">',
           '<title id="diagram-title">Copilot 知识初始化与维护：五层职责图</title>',
           f'<desc id="diagram-desc">初始化五阶段与维护两步骤共用 WorkflowExecution.execute；领域记录各自持有业务事实和预算。复用内容、证据和审核，经发布及撤回到公开 SDK v1 与 review bot。主图是职责图；完整 {counts["provider"]} 个 Python 类在配套 HTML 和 JSON 中。源码摘要 {inventory["source_tree_sha256"]}。</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#9baabd"/></marker></defs>',
           '<style>text{font-family:Arial,"Droid Sans Fallback",sans-serif} .code{font-family:ui-monospace,"DejaVu Sans Mono",monospace}</style>',
           f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f3f6fa"/>']

    def text(x: int, y: int, value: str, size: int = 20, color: str = "#1e3046", weight: int = 400, code: bool = False) -> None:
        css = ' class="code"' if code else ""
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}"{css}>{html.escape(value)}</text>')

    def rect(x: int, y: int, w: int, h: int, fill: str, stroke: str = "#dbe4ef", radius: int = 14) -> None:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def card(x: int, y: int, h: int, title: str, lines: list[tuple[str, bool]], color: str) -> None:
        rect(x, y, 620, h, "#ffffff")
        svg.append(f'<rect x="{x}" y="{y + 12}" width="5" height="{h - 24}" rx="2" fill="{color}"/>')
        text(x + 24, y + 37, title, 23, color, 700)
        for index, (value, code) in enumerate(lines):
            text(x + 24, y + 72 + index * 29, value, 17 if code else 19, "#4d6179", code=code)

    text(60, 55, "知识初始化与维护", 36, weight=700)
    text(60, 89, "同一执行底座；领域记录各自持有事实与预算；每个 Python 类在展开视图中列出", 20, "#60728b")
    text(60, 124, f"{counts['core']} 个核心类 = {counts['kb_service']} kb_service + {counts['knowledge_service']} knowledge_service   ·   {counts['provider']} 个 provider 类完整清单", 17, "#526a89", code=True)

    rows = [(155, 140, "01", "执行入口"), (327, 185, "02", "流程编排"), (544, 185, "03", "共享领域"), (761, 156, "04", "发布恢复"), (949, 185, "05", "知识消费")]
    for y, height, number, title in rows:
        text(58, y + 34, number, 26, "#9aaac0", 700)
        text(58, y + 65, title, 18, "#52657f", 700)
    for current, following in zip(rows, rows[1:]):
        for x in (490, 1140):
            svg.append(f'<path d="M {x} {current[0] + current[1] + 4} V {following[0] - 8}" stroke="#9baabd" stroke-width="2" marker-end="url(#arrow)"/>')

    blue, green, purple = "#245fc7", "#087c72", "#7251ae"
    card(180, 155, 140, "Copilot 执行入口", [
        ("Copilot / kb init / knowledge.init", True),
        ("绑定范围与版本；提交同一初始化计划", False)], blue)
    card(830, 155, 140, "维护调度入口", [
        ("Scheduler / kb serve → KbRuntime", True),
        ("原有调度顺序与租约；提交维护计划", False)], green)
    card(180, 327, 185, "初始化：建立可验收的知识基线", [
        ("init_execution → WorkflowExecution.execute", True),
        ("prepare → draft → validate", True),
        ("prepare_publication → publish", True),
        ("InitRecord：pin、正文、证据、费用与发布事实", False)], blue)
    card(830, 327, 185, "维护：更新 · 主动复查 · 纠错", [
        ("run_due → WorkflowExecution.execute", True),
        ("correction → nightly_audit（两步均重验）", True),
        ("MaintenanceStore：周期、请求、预留与发现", False),
        ("领域 SQLite 持有进度；执行器不复制业务账本", False)], green)
    card(180, 544, 185, "内容与原始证据", [
        ("Page · Section · Footer · KnowledgeOperation", True),
        ("Claim · Evidence · 适用版本与正文身份", False),
        ("init_content · git_objects（共用机制）", True),
        ("候选有界生成／修复；各入口保留范围约束", False)], purple)
    card(830, 544, 185, "审核与准入", [
        ("gate · maintenance_policy", True),
        ("确定性验证 · 独立语义审核 · 一致性", False),
        ("受保护约束 · 纠错资格 · 当前证据复验", False),
        ("maintenance_resolution 追加负责人处置", True)], purple)
    card(180, 761, 156, "各自权限内的受治理发布", [
        ("InitPublisher · Publisher · activate", True),
        ("签名 → Git 交接 → 合并 → 快照激活", False),
        ("候选成功应用仍不等于正式发布", False)], blue)
    card(830, 761, 156, "撤回、传播与恢复", [
        ("containment · 签名代际 · 消费者 ACK", False),
        ("撤回独立于快照；回滚不能清除禁用", False),
        ("仅恢复获准新内容；历史回执保持完整", False)], green)
    card(180, 949, 185, "任务知识与版本化 SDK v1", [
        ("KnowledgeView · KnowledgeDocs", True),
        ("KnowledgeContextService", True),
        ("ReviewRuntime / KnowledgeCurator", True),
        ("固定快照、限定读取、会话预算和使用回执", False)], blue)
    card(830, 949, 185, "Review bot：经 SDK 读取与消费", [
        ("ReviewPipeline · KnowledgeDistiller", True),
        ("KnowledgeMaintenance · ReviewPublisher", True),
        ("公开边界仅 SDK v1；候选交权威维护审核", False),
        ("Direct / Strict 共用发布前可用性检查", False)], green)
    rect(180, 1165, 1270, 109, "#eaf0f8", "#d6e0ee")
    text(202, 1198, "共享底座：执行锁与恢复 · 预留与结算 · 原生模型回执 · Git 对象 · 原子写入", 21, "#334f73", 700)
    text(202, 1232, "单所有者：InitRecord｜维护 SQLite｜improve 周预算｜发布 outbox｜消费会话｜撤回高水位", 19, "#52657f")
    text(60, 1311, "箭头表达职责与交付关系，不是逐函数调用图。执行内核不反向依赖知识流程；bot 运行代码仅依赖 SDK v1。", 16, "#64758b")
    text(60, 1336, f"源码树摘要：{inventory['source_tree_sha256'][:16]}  ·  完整源路径、嵌套／局部类与文件摘要见 HTML / JSON", 14, "#71829a")
    return "\n".join(svg) + "\n</svg>\n"


HTML_HEAD = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light"><title>知识初始化与维护 · 分层与完整类清单</title>
<style>
:root{--ink:#20324a;--muted:#63758b;--line:#dbe4ee;--accent:#245fc7}*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:var(--ink);font-family:Arial,"Droid Sans Fallback",sans-serif}header,main{max-width:1640px;margin:auto;padding:24px}header{padding-bottom:16px}h1{font-size:29px;letter-spacing:-.02em;margin:0 0 10px}p{line-height:1.7;margin:8px 0;color:var(--muted);font-size:14px}a{color:var(--accent)}button,.download{border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);padding:8px 12px;font-size:13px;text-decoration:none;cursor:pointer;white-space:nowrap}button:hover,.download:hover{background:#edf3ff}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid #94b2f4;outline-offset:3px}.toolbar{position:sticky;top:0;z-index:4;background:#ffffffed;border-block:1px solid var(--line);backdrop-filter:blur(8px)}.toolbar-inner{max-width:1640px;margin:auto;padding:10px 24px;display:flex;align-items:center;flex-wrap:wrap;gap:7px}.toolbar input{flex:1;min-width:180px;max-width:420px;height:36px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:#f8faff}.zoom{font-size:12px;min-width:44px;text-align:center;font-variant-numeric:tabular-nums}.downloads{margin-left:auto;display:flex;gap:6px}.badges{display:flex;gap:7px;flex-wrap:wrap}.badge{font-size:12px;padding:5px 10px;border:1px solid #d9e3f1;border-radius:20px;background:#fff;color:#486482}.diagram{overflow:auto;max-height:82vh;padding:12px;border:1px solid var(--line);border-radius:14px;background:#eaf0f7;scrollbar-gutter:stable}.diagram svg{display:block;max-width:none;background:#fff;border-radius:10px}.inventory-head{padding-top:32px;scroll-margin-top:90px}h2{font-size:23px;margin:0 0 10px}.inventory-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:12px 0 18px}.match-count{font-size:12px;color:var(--muted)}details.capability{background:#fff;border:1px solid var(--line);border-radius:11px;margin:10px 0;scroll-margin-top:90px}details.capability>summary{padding:15px 18px;cursor:pointer;font-size:16px;font-weight:700}details.capability>summary small{font-size:12px;color:var(--muted);font-weight:400;margin-left:8px}.class-list{padding:0 18px 12px}.class-card{border-top:1px solid #e8edf4;scroll-margin-top:95px}.class-card>summary{padding:10px 2px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;cursor:pointer;font-size:13px}.class-name{font-family:ui-monospace,"DejaVu Sans Mono",monospace;color:#20324a;overflow-wrap:anywhere}.module{color:#71839a;font-size:11px;overflow-wrap:anywhere}.kind{font-size:10px;background:#edf3fa;color:#526d90;padding:2px 5px;border-radius:4px}.class-info{padding:0 2px 12px;font-size:12px;line-height:1.7;color:#536983;overflow-wrap:anywhere}.class-info p{font-size:12px;margin:5px 0}.class-info code{font-size:11px}.class-card.search-match{background:#fff5ce;box-shadow:inset 3px 0 #e6b345;padding-left:8px}.class-card.search-active{background:#ffe8a0;box-shadow:inset 3px 0 #b46b0b}.hidden{display:none!important}.note{background:#eaf0f8;border-radius:10px;padding:14px 18px;margin:20px 0;color:#52657e;font-size:12px;line-height:1.8}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}@media(max-width:700px){header,main{padding:18px 12px}h1{font-size:24px}.toolbar-inner{padding:8px 12px}.downloads{margin-left:0}.toolbar input{order:2;max-width:none;flex-basis:100%}.diagram{max-height:65vh}.class-list{padding-inline:10px}details.capability>summary{padding:13px 12px}.module{flex-basis:100%}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style></head><body>
"""


HTML_SCRIPT = """<script>
(()=>{'use strict';
const diagram=document.getElementById('diagram'),svg=document.getElementById('lifecycle-svg'),zoomValue=document.getElementById('zoom-value');
const native=svg.viewBox.baseVal;let zoom=1,fitMode=true;
function setZoom(value,preserve=true){const next=Math.max(.15,Math.min(3,value));const cx=diagram.scrollLeft+diagram.clientWidth/2-12,cy=diagram.scrollTop+diagram.clientHeight/2-12,ratio=next/zoom;svg.style.width=native.width*next+'px';svg.style.height=native.height*next+'px';zoom=next;zoomValue.textContent=Math.round(zoom*100)+'%';if(preserve){diagram.scrollLeft=cx*ratio+12-diagram.clientWidth/2;diagram.scrollTop=cy*ratio+12-diagram.clientHeight/2;}}
function fit(){fitMode=true;setZoom((diagram.clientWidth-26)/native.width,false);diagram.scrollLeft=0;}
document.getElementById('zoom-in').onclick=()=>{fitMode=false;setZoom(zoom*1.25)};
document.getElementById('zoom-out').onclick=()=>{fitMode=false;setZoom(zoom/1.25)};
document.getElementById('fit').onclick=fit;
const input=document.getElementById('search'),cards=Array.from(document.querySelectorAll('.class-card')),groups=Array.from(document.querySelectorAll('.capability')),status=document.getElementById('matches');let matches=[],active=-1,appliedQuery='';
function showActive(){cards.forEach(e=>e.classList.remove('search-active'));if(matches.length){const item=matches[active];item.classList.add('search-active');item.closest('.capability').open=true;item.scrollIntoView({block:'center'});status.textContent=(active+1)+' / '+matches.length+' 个匹配';}else{status.textContent=input.value.trim()?'无匹配':'全部 '+cards.length+' 个类';}}
function search(){appliedQuery=input.value;const terms=input.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);matches=[];cards.forEach(card=>{const ok=terms.length>0&&terms.every(term=>card.dataset.search.includes(term));card.classList.toggle('search-match',ok);card.classList.remove('search-active');if(ok)matches.push(card)});active=matches.length?0:-1;showActive();}
input.oninput=search;
function move(step){if(!matches.length)return;active=(active+step+matches.length)%matches.length;showActive()}
document.getElementById('previous').onclick=()=>move(-1);document.getElementById('next').onclick=()=>move(1);
input.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();if(input.value!==appliedQuery)search();else move(event.shiftKey?-1:1)}if(event.key==='Escape'){input.value='';search()}};
document.getElementById('expand').onclick=()=>groups.forEach(e=>e.open=true);
document.getElementById('collapse').onclick=()=>{groups.forEach(e=>e.open=false);cards.forEach(e=>e.open=false)};
document.getElementById('reset').onclick=()=>{input.value='';search();groups.forEach(e=>e.open=false);cards.forEach(e=>e.open=false);fit();diagram.scrollTop=0;window.scrollTo({top:0})};
window.addEventListener('resize',()=>{if(fitMode)fit()});fit();requestAnimationFrame(fit);
})();
</script></body></html>
"""


def render_html(repo: Path, inventory: dict[str, Any], svg: str) -> str:
    counts = inventory["counts"]
    esc = html.escape
    body = [HTML_HEAD,
            '<header><h1>知识初始化与维护 · 分层与完整类清单</h1>',
            '<p>主图展示五层职责：初始化五阶段和维护两步骤共用执行底座，领域账本各自持有事实与预算，bot 只经公开 SDK v1 消费。展开视图列出实际源码中的每个 Python 类，包括记录、异常、协议和私有／嵌套／函数局部类。</p>',
            '<div class="badges">',
            f'<span class="badge">核心 {counts["core"]} = kb_service {counts["kb_service"]} + knowledge_service {counts["knowledge_service"]}</span>',
            f'<span class="badge">Provider 全量 {counts["provider"]}</span>',
            f'<span class="badge">函数局部类 {counts["function_local"]}</span>',
            f'<span class="badge">源码树 {inventory["source_tree_sha256"][:16]}</span></div></header>',
            '<nav class="toolbar" aria-label="图与清单控制"><div class="toolbar-inner">',
            '<button id="zoom-out" aria-label="缩小主图">−</button><span class="zoom" id="zoom-value">100%</span><button id="zoom-in" aria-label="放大主图">+</button><button id="fit">适应宽度</button><button id="reset">重置</button>',
            '<label for="search" class="sr-only">按类名、模块、路径或类型搜索</label><input id="search" type="search" placeholder="搜索类名、模块或源路径…" autocomplete="off" spellcheck="false">',
            '<button id="previous" aria-label="上一个匹配">↑</button><button id="next" aria-label="下一个匹配">↓</button>',
            '<div class="downloads"><a class="download" href="knowledge-lifecycle.svg" download>SVG</a><a class="download" href="class-inventory.json" download>JSON 清单</a><a class="download" href="coverage-proof.json" download>覆盖证明</a></div></div></nav>',
            '<main><section aria-label="五层职责图"><div id="diagram" class="diagram" tabindex="0">', svg, '</div></section>',
            '<section id="inventory" class="inventory-head"><h2>Python 类展开视图</h2>',
            '<p>按能力浏览核心类；其余 provider 类在外部附录中逐项列出。点击能力分组和类名展开来源、继承及说明；搜索会展开并定位匹配项，不隐藏其他类。</p>',
            '<div class="inventory-actions"><button id="expand">展开全部分组</button><button id="collapse">收起全部</button>',
            f'<span id="matches" class="match-count" aria-live="polite">全部 {counts["provider"]} 个类</span></div>']
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in inventory["classes"]:
        groups[item["capability"]].append(item)
    order = list(GROUPS) + sorted(key for key in groups if key not in GROUPS)
    kinds = {"class": "类", "record": "记录", "exception": "异常", "protocol": "协议"}
    for group in order:
        items = groups.get(group, [])
        if not items:
            continue
        label = items[0]["capability_label"]
        body.append(f'<details class="capability" id="inventory-{esc(group)}"><summary>{esc(label)}<small>{len(items)} 个类</small></summary><div class="class-list">')
        for item in items:
            tags = [kinds[item["kind"]]]
            tags += [label for field, label in (("private", "私有"), ("nested", "嵌套"), ("function_local", "函数局部")) if item[field]]
            flags = [field.replace("_", "-") for field in ("private", "nested", "function_local") if item[field]]
            searchable = " ".join([item["id"], item["path"], item["qualname"], item["kind"], *tags, *flags]).lower()
            body.append(f'<details class="class-card" data-class-id="{esc(item["id"], quote=True)}" data-search="{esc(searchable, quote=True)}"><summary><span class="class-name">{esc(item["qualname"])}</span><span class="kind">{esc(" · ".join(tags))}</span><span class="module">{esc(item["module"])}</span></summary><div class="class-info">')
            href = (repo / item["path"]).as_uri() + f'#L{item["line"]}'
            body.append(f'<a href="{esc(href, quote=True)}">{esc(item["path"])}:{item["line"]}</a> · 至第 {item["end_line"]} 行')
            if item["bases"]:
                body.append(f'<p>基类：<code>{esc(", ".join(item["bases"]))}</code></p>')
            if item["doc_summary"]:
                body.append(f'<p>{esc(item["doc_summary"])}</p>')
            body.append(f'<p>文件 SHA-256：<code>{item["file_sha256"]}</code></p></div></details>')
        body.append('</div></details>')
    body.append(f'<aside class="note">清单范围：src/infermatrix_copilot/**/*.py 的全部 ast.ClassDef；不含 test/ 和 tools/。核心范围仅 kb_service 与 knowledge_service。函数局部类保留 &lt;locals&gt; 词法范围；每个声明由模块、词法名和行号唯一标识。<br>主图箭头是职责关系，不是逐函数调用图。Review bot 名称用于说明 SDK 消费关系，bot 自身源码不在本 provider 清单范围。<br>HEAD：{esc(inventory["source_commit"] or "unknown")}；源码树摘要绑定当前工作树实际字节，包含尚未提交的源文件变化。<br>所有资源均在本地；打开此 HTML 不发起网络请求。</aside></section></main>')
    body.append(HTML_SCRIPT)
    result = "\n".join(body)
    assert result.count('data-class-id="') == counts["provider"]
    return result


def render(repo: Path, output: Path) -> dict[str, Any]:
    inventory = collect(repo)
    svg = render_svg(inventory).encode()
    inventory_json = json_bytes(inventory)
    viewer = render_html(repo, inventory, svg.decode()).encode()
    # A moving working tree must never receive a proof for mixed source versions.
    fresh_files = [{"path": item["path"], "sha256": digest((repo / item["path"]).read_bytes()), "class_count": item["class_count"]} for item in inventory["files"]]
    current_paths = sorted(path.relative_to(repo).as_posix() for path in (repo / PACKAGE).rglob("*.py"))
    assert current_paths == [item["path"] for item in inventory["files"]], "Source file set changed; rerun"
    assert fresh_files == inventory["files"], "Source changed during rendering; rerun"
    outputs = {"knowledge-lifecycle.svg": svg, "class-inventory.json": inventory_json, "knowledge-lifecycle.html": viewer}
    proof = {
        "schema_version": 1,
        "source_commit": inventory["source_commit"],
        "source_tree_sha256": inventory["source_tree_sha256"],
        "source_file_count": inventory["source_file_count"],
        "counts": inventory["counts"],
        "unique_class_ids": len({item["id"] for item in inventory["classes"]}),
        "capability_counts": dict(sorted(Counter(item["capability"] for item in inventory["classes"]).items())),
        "checks": {"ast_declarations_complete": True, "class_ids_unique": True, "html_entries_complete": True, "source_hashes_fresh": True},
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "outputs_sha256": {name: digest(data) for name, data in outputs.items()},
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        (output / name).write_bytes(data)
    (output / "coverage-proof.json").write_bytes(json_bytes(proof))
    return proof


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1], help="Provider repository root; product modules are not imported")
    parser.add_argument("--output", type=Path, help="Output directory for the SVG, HTML, inventory JSON and coverage proof")
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = (args.output or repo / "output/knowledge-lifecycle").resolve()
    if not (repo / PACKAGE).is_dir():
        parser.error(f"Missing provider source directory: {repo / PACKAGE}")
    proof = render(repo, output)
    print(json.dumps({"output": str(output), "counts": proof["counts"], "source_tree_sha256": proof["source_tree_sha256"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
