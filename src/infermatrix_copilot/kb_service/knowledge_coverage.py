"""Pinned feature and production-file coverage, separate from rule coverage.

Source-contract cards describe declarations and integration points that can be
checked without executing upstream code. They are structural knowledge, not a
claim that all behavior in a file has been understood or tested.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote

import yaml

from ..knowledge_service.lifecycle import Page
from ..knowledge_service.ops import page_over_capacity
from .init_coverage import Owner, most_specific
from .init_stages import _page_frontmatter

FACETS = ("architecture", "api", "configuration", "tradeoffs", "features", "validation")
SUFFIXES = (".py", ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".kt", ".kts", ".java",
            ".rs", ".go", ".swift", ".ets", ".vue", ".svelte", ".html", ".css", ".scss", ".less",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".ps1", ".psm1", ".cmd", ".bat", ".iss", ".spec")
FILENAMES = ("Dockerfile", "Dockerfile.*", "Makefile", "gradlew")
_FILE = re.compile(r"<!-- kb:file path=(\S+) pin=([a-f0-9]{40}) sha256=([a-f0-9]{64}) -->\n(.*?)\n<!-- /kb:file -->", re.S)
_FACET = re.compile(r"<!-- kb:knowledge owner=feature-([a-z0-9-]+) facet=([a-z]+) pin=([a-f0-9]{40})"
                    r"(?: verdict=(pass|unsure|unjudged))? -->")
_SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
_LEXICAL_NO_CODE = re.compile(r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|/\*[\s\S]*?\*/|//[^\n]*|<!--[\s\S]*?-->''')


@dataclass(frozen=True)
class Feature:
    id: str
    title: str
    owner: str
    source_globs: tuple[str, ...]
    docs: tuple[str, ...]
    page: str
    entry_points: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoveragePolicy:
    roots: tuple[str, ...]
    exclude: tuple[str, ...]
    suffixes: tuple[str, ...]
    features: tuple[Feature, ...]
    target: float = 0.85
    required: bool = True
    filenames: tuple[str, ...] = FILENAMES
    catalog_sources: tuple[str, ...] = ()


def policy_path(repo: str) -> str:
    return f"adapters/{repo}/knowledge-coverage.yaml"


def _paths(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x for x in value):
        raise ValueError(f"{name} must be a non-empty path list")
    for path in value:
        if path.startswith("/") or "\\" in path or any(p in ("", ".", "..") for p in path.rstrip("/").split("/")):
            raise ValueError(f"{name} needs safe repository-relative paths")
    return tuple(value)


def load_policy(text: str, repo_dir: str) -> CoveragePolicy:
    data = yaml.safe_load(text)
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("knowledge coverage needs schema_version: 1")
    if set(data) - {"schema_version", "core", "features", "required", "catalog_sources"}:
        raise ValueError("unknown knowledge coverage policy key")
    core = data.get("core")
    if not isinstance(core, dict) or set(core) - {"roots", "exclude", "suffixes", "filenames", "target"}:
        raise ValueError("core needs roots, exclude, suffixes and target")
    target = core.get("target", 0.85)
    if isinstance(target, bool) or not isinstance(target, (int, float)) or not 0 < target <= 1:
        raise ValueError("core target must be in (0, 1]")
    required = data.get("required", True)
    if not isinstance(required, bool):
        raise ValueError("required must be a boolean")
    extensions = tuple(core.get("suffixes", SUFFIXES))
    if not extensions or any(s not in SUFFIXES for s in extensions):
        raise ValueError("unsupported production-code suffix")
    filenames = core.get("filenames", list(FILENAMES))
    if not isinstance(filenames, list) or any(name not in FILENAMES for name in filenames):
        raise ValueError("unsupported production-code filename pattern")
    features, seen = [], set()
    if not isinstance(data.get("features"), list) or not data["features"]:
        raise ValueError("a non-empty explicit feature inventory is required")
    for item in data["features"]:
        required_keys = {"id", "title", "owner", "source_globs", "docs", "page"}
        if not isinstance(item, dict) or required_keys - set(item) or set(item) - required_keys - {"entry_points"}:
            raise ValueError("each feature needs id, title, owner, source_globs, docs and page")
        if not isinstance(item["id"], str) or not _SLUG.fullmatch(item["id"]) or item["id"] in seen:
            raise ValueError("feature ids must be unique safe slugs")
        if not isinstance(item["owner"], str) or not _SLUG.fullmatch(item["owner"]) or not isinstance(item["title"], str):
            raise ValueError("feature needs an owner slug and title")
        page = _paths([item["page"]], "feature page")[0]
        if not page.startswith(repo_dir + "/components/") or not page.endswith(".md"):
            raise ValueError("feature page must live under this repository's component owner")
        if PurePosixPath(page).parent.name != item["owner"]:
            raise ValueError("feature page must belong to its declared owner")
        features.append(Feature(item["id"], item["title"], item["owner"],
                                _paths(item["source_globs"], "source_globs"),
                                _paths(item["docs"], "docs"), page,
                                _paths(item["entry_points"], "entry_points") if "entry_points" in item else ()))
        seen.add(item["id"])
    return CoveragePolicy(_paths(core.get("roots"), "core roots"),
                          _paths(core.get("exclude"), "core exclude"), extensions,
                          tuple(features), float(target), required, tuple(filenames),
                          _paths(data["catalog_sources"], "catalog_sources") if "catalog_sources" in data else ())


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def inventory(tree: Path, policy: CoveragePolicy) -> list[str]:
    """All files in declared production roots; exclusions never depend on KB content."""
    files = []
    if (tree / ".git").exists():
        names = subprocess.check_output(["git", "-C", str(tree), "ls-files", "-z"], text=True).split("\0")
        candidates = [tree / name for name in names if name]
    else:
        candidates = sorted(tree.rglob("*"))
    for file in candidates:
        if not file.is_file() or file.is_symlink():
            continue
        path = file.relative_to(tree).as_posix()
        if not any(path.startswith(root.rstrip("/") + "/") or path == root for root in policy.roots):
            continue
        if (file.suffix not in policy.suffixes and not matches(file.name, policy.filenames)) or matches(path, policy.exclude):
            continue
        # Empty package markers have no implementation; import/export facades count.
        if file.suffix == ".py":
            try:
                parsed = ast.parse(file.read_text(encoding="utf-8"))
                if not any(not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Constant)
                           or not isinstance(n.value.value, str) for n in parsed.body):
                    continue
            except (SyntaxError, UnicodeError):
                pass  # parser failures stay in the denominator
        files.append(path)
    return sorted(files)


def _clean(text: str, limit: int = 160) -> str:
    return " ".join(text.replace("`", "'").replace("|", "/").replace("<", "&lt;").replace(">", "&gt;").split())[:limit]


def source_contract(path: str, raw: str) -> tuple[str, list[tuple[int, int]]] | None:
    """Extract verifiable interfaces and dependencies; omit unsupported syntax."""
    facts, spans = [], []
    lines = raw.splitlines()
    if path.endswith(".py"):
        try:
            module = ast.parse(raw)
        except SyntaxError:
            return None
        doc = ast.get_docstring(module)
        if doc:
            facts.append("源码对模块职责的说明：" + _clean(doc.split("\n\n", 1)[0]))
        public = [n for n in module.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                  and not n.name.startswith("_")]
        for node in public[:4]:
            if isinstance(node, ast.ClassDef):
                bases = ", ".join(_clean(ast.unparse(b), 50) for b in node.bases)
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                           and (not n.name.startswith("_") or n.name == "__init__")]
                facts.append(f"`{node.name}`" + (f" 继承 `{bases}`" if bases else " 定义类型边界")
                             + ("；方法入口：" + ", ".join(f"`{n}`" for n in methods[:6]) if methods else ""))
            else:
                args = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
                if node.args.vararg:
                    args.append("*" + node.args.vararg.arg)
                if node.args.kwarg:
                    args.append("**" + node.args.kwarg.arg)
                facts.append(("异步入口 " if isinstance(node, ast.AsyncFunctionDef) else "调用入口 ")
                             + f"`{node.name}({', '.join(args[:10])}{', …' if len(args) > 10 else ''})`"
                             + ("；声明返回 `" + _clean(ast.unparse(node.returns), 70) + "`" if node.returns else ""))
            spans.append((node.lineno, min(node.end_lineno or node.lineno, node.lineno + 18)))
        imports = [ast.unparse(n) for n in module.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        if imports:
            facts.append("集成依赖（导入声明，不等于全部运行时依赖）：" + "；".join(f"`{_clean(s, 75)}`" for s in imports[:4]))
            nodes = [n for n in module.body if isinstance(n, (ast.Import, ast.ImportFrom))][:4]
            spans.extend((n.lineno, n.end_lineno or n.lineno) for n in nodes)
        # Constants' names reveal configuration boundaries without copying secrets/default values.
        names = [t.id for n in module.body if isinstance(n, (ast.Assign, ast.AnnAssign))
                 for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
                 if isinstance(t, ast.Name) and t.id.isupper() and not t.id.startswith("_")]
        if names:
            facts.append("模块级配置或常量名称：" + ", ".join(f"`{n}`" for n in names[:8]) + "；实际值与使用条件见源码")
    else:
        # Keep line positions, but don't report declarations from comments or examples in strings.
        code = _LEXICAL_NO_CODE.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), raw).splitlines()
        declarations = []
        pattern = re.compile(r"(?:export\s+(?:default\s+)?|public\s+|private\s+|internal\s+|async\s+|suspend\s+)*"
                             r"(?:function|class|interface|type|enum|const|let|var|fun|struct|fn)\s+([A-Za-z_$][\w$]*)")
        for number, line in enumerate(code, 1):
            hit = pattern.search(line)
            if hit:
                declarations.append((hit.group(1), number))
        if declarations:
            facts.append("源码声明的类型、组件或调用边界：" + ", ".join(f"`{n}`" for n, _ in declarations[:8])
                         + "；这是词法声明索引，不把局部变量当成对外导出 API")
            spans.extend((n, min(n + 3, len(lines))) for _, n in declarations[:4])
        imports = [(n, _clean(lines[n - 1], 100)) for n, line in enumerate(code, 1)
                   if re.match(r"\s*(?:import\b|.*\brequire\(|package\s|source\s|\.\s)", line)]
        if imports:
            facts.append("集成边界的导入/加载声明：" + "；".join(f"`{line}`" for _, line in imports[:4]))
            spans.extend((n, n) for n, _ in imports[:4])
        if path.endswith((".sh", ".ps1", ".cmd", ".bat")):
            commands = [(n, _clean(line, 100)) for n, line in enumerate(lines, 1)
                        if re.match(r"\s*(?:python\b|python3\b|uv\b|npm\b|npx\b|docker\b|git\b|function\b)", line)]
            if commands:
                facts.append("脚本执行边界：" + "；".join(f"`{line}`" for _, line in commands[:4]))
                spans.extend((n, n) for n, _ in commands[:4])
        if path.endswith(".html"):
            elements = [(n, tag) for n, line in enumerate(lines, 1)
                        for tag in re.findall(r"<(script|link|form|main|body)\b", line)]
            if elements:
                facts.append("页面装配边界：" + ", ".join(sorted({t for _, t in elements}))
                             + " 标签；资源装载与宿主连接取决于对应属性和脚本实现")
                spans.extend((n, n) for n, _ in elements[:4])
    if not spans or not facts:
        return None
    body = "\n".join("- " + fact + "。" for fact in facts)
    return body, sorted(set(spans))[:8]


def render_contract(full_name: str, pin: str, path: str, raw: str) -> str | None:
    contract = source_contract(path, raw)
    if contract is None:
        return None
    body, _ = contract
    end = len(raw.splitlines())
    ref = f"[完整声明与实现](https://github.com/{full_name}/blob/{pin}/{quote(path, safe='/')}#L1-L{end})"
    return f"**`{path}`**\n\n{body}\n\n源码依据：{ref}。"


def contract_block(full_name: str, pin: str, path: str, raw: str) -> str | None:
    body = render_contract(full_name, pin, path, raw)
    if body is None:
        return None
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"<!-- kb:file path={quote(path, safe='/')} pin={pin} sha256={digest} -->\n{body}\n<!-- /kb:file -->"


def _citations(text: str, tree: Path, full_name: str, pin: str) -> set[str]:
    pattern = re.compile(r"https://github\.com/" + re.escape(full_name) + r"/blob/" + pin
                         + r"/([^\s)#]+)#L(\d+)(?:-L(\d+))?")
    valid = set()
    for encoded, start, end in pattern.findall(text):
        path = unquote(encoded)
        if path.startswith("/") or ".." in PurePosixPath(path).parts or "\\" in path:
            continue
        source = tree / path
        if source.is_file() and not source.is_symlink():
            size = len(source.read_text(encoding="utf-8", errors="replace").splitlines())
            if 1 <= int(start) <= int(end or start) <= size:
                valid.add(path)
    return valid


def _explained_citations(text: str, tree: Path, full_name: str, pin: str) -> set[str]:
    """A list of links or a source header is not a file explanation."""
    found, previous = set(), False
    for paragraph in re.split(r"\n\s*\n", text):
        plain = re.sub(r"\[[^\]]*\]\([^)]*\)|<!--.*?-->", "", paragraph, flags=re.S)
        prose = re.sub(r"`[^`]*`", "", plain)
        # Setting and interface names carry information, but a filename alone does not.
        meaningful = len(re.sub(r"[\s\W_]+", "", plain)) >= 60 \
            and len(re.sub(r"[\s\W_]+", "", prose)) >= 25 \
            and not plain.lstrip().startswith(("#", "|"))
        source_caption = re.match(r"\s*(?:Sources|Evidence|来源|源码依据|源码与文档|文档依据)\s*[:：/]", plain)
        citation_only = len(plain.strip()) <= 16 and 0 < len(re.findall(r"\[[^\]]*\]\([^)]*\)", paragraph)) <= 8 \
            and not paragraph.lstrip().startswith(("|", "-", "*", "#"))
        if meaningful or (previous and (source_caption or citation_only)):
            found.update(_citations(paragraph, tree, full_name, pin))
        previous = meaningful
    return found


def audit_coverage(head: dict[str, str], tree: Path, policy: CoveragePolicy,
                   *, full_name: str, pin: str) -> dict:
    files = inventory(tree, policy)
    covered, cards, stale = set(), set(), set()
    prose = {}
    for page, text in head.items():
        if not page.endswith(".md"):
            continue
        parsed = Page.parse(text)
        if parsed.frontmatter_field("type") not in ("architecture", "guide"):
            continue
        body = text.split("---", 2)[-1]
        prose[page] = body
        # Existing hand-written explanations count only with actual line citations.
        plain = _FILE.sub("", body)
        if len(plain.strip()) >= 200:
            covered.update(_explained_citations(plain, tree, full_name, pin))
        for encoded, old_pin, digest, card in _FILE.findall(body):
            path = unquote(encoded)
            if path not in files:
                continue
            raw = (tree / path).read_text(encoding="utf-8", errors="replace")
            if old_pin == pin and digest == hashlib.sha256(raw.encode()).hexdigest() \
                    and card == render_contract(full_name, pin, path, raw):
                covered.add(path)
                cards.add(path)
            else:
                stale.add(path)
    features = {}
    production = set(files)
    for feature in policy.features:
        text = prose.get(feature.page, "")
        facets = set()
        markers = list(_FACET.finditer(text))
        for index, marker in enumerate(markers):
            id_, facet, old_pin, verdict = marker.groups()
            section = text[marker.end():markers[index + 1].start() if index + 1 < len(markers) else len(text)]
            if id_ == feature.id and old_pin == pin and verdict in (None, "", "pass") \
                    and _explained_citations(section, tree, full_name, pin):
                facets.add(facet)
        refs = _citations(text, tree, full_name, pin)
        implemented = [p for p in files if matches(p, feature.source_globs)]
        has_source = (bool(feature.entry_points) and set(feature.entry_points) <= refs.intersection(production)) \
            if feature.entry_points else any(matches(p, feature.source_globs) for p in refs.intersection(production))
        has_docs = all((tree / p).is_file() for p in feature.docs) and bool(refs.intersection(feature.docs))
        complete = bool(implemented) and has_source and has_docs and len(text.strip()) >= 500 and set(FACETS) <= facets
        features[feature.id] = {"title": feature.title, "page": feature.page,
                                "covered": complete, "missing_facets": sorted(set(FACETS) - facets),
                                "source_evidence": has_source, "doc_evidence": has_docs,
                                "implemented": bool(implemented)}
    covered.intersection_update(files)
    core_ratio = len(covered) / len(files) if files else 0.0
    feature_count = sum(f["covered"] for f in features.values())
    missing_catalogs = [p for p in policy.catalog_sources if not (tree / p).is_file() or (tree / p).is_symlink()]
    return {"pin": pin, "full_name": full_name, "required": policy.required,
            "definitions": {
                "feature": "Every declared feature has six cited facets, documentation and production entry points. "
                           "This is inventory coverage, not proof of exhaustive feature discovery or runtime correctness.",
                "core_file": "A production file has a cited explanation or a hash-verified static interface/dependency record. "
                             "This is structural knowledge coverage, not exhaustive behavior analysis or test coverage."},
            "catalog_sources": {"declared": list(policy.catalog_sources), "missing": missing_catalogs},
            "met": bool(files) and not missing_catalogs and core_ratio >= policy.target and feature_count == len(features),
            "core": {"target": policy.target, "covered": len(covered), "total": len(files),
                     "ratio": core_ratio, "roots": list(policy.roots), "exclude": list(policy.exclude),
                     "suffixes": list(policy.suffixes), "filenames": list(policy.filenames), "covered_files": sorted(covered),
                     "missing_files": sorted(set(files) - covered), "contract_files": len(cards),
                     "stale_contracts": sorted(stale)},
            "features": {"target": 1.0, "covered": feature_count, "total": len(features), "items": features}}


def add_contract_pages(head: dict[str, str], tree: Path, policy: CoveragePolicy, owners: list[Owner],
                       *, repo_dir: str, full_name: str, pin: str, today: str, tags: list[str], link_page) -> list[str]:
    """Write bounded owner-specific contract pages; never overwrite a stale card."""
    audit = audit_coverage(head, tree, policy, full_name=full_name, pin=pin)
    existing = audit["core"]["covered_files"] + audit["core"]["stale_contracts"]
    paths = [p for p in audit["core"]["missing_files"] if p not in existing]
    def owner_directory(path: str):
        hits = most_specific(path, owners)
        if hits:
            owner = hits[0]
            directory = PurePosixPath(owner.path).parent
            if str(directory) == repo_dir:
                directory = PurePosixPath(repo_dir) / "components" / owner.owner
        else:
            # Explicit feature ownership also covers SDKs and clients absent from old routes.
            features = [f for f in policy.features if matches(path, f.source_globs)]
            if not features:
                return None
            directory = PurePosixPath(repo_dir) / "components" / features[0].owner
        return directory

    owner_paths: dict[PurePosixPath, list[str]] = {}
    for path in inventory(tree, policy):
        directory = owner_directory(path)
        if directory:
            owner_paths.setdefault(directory, []).append(str(PurePosixPath(path).parent))
    source_roots = {directory: PurePosixPath(os.path.commonpath(parents)) for directory, parents in owner_paths.items()}
    skipped = []
    for path in paths:
        raw = (tree / path).read_text(encoding="utf-8", errors="replace")
        block = contract_block(full_name, pin, path, raw)
        directory = owner_directory(path)
        if block is None or directory is None:
            skipped.append(path)
            continue
        # One source area (for example features/chat or runtime/session), not one
        # directory for each individual component file. The roots use the whole
        # denominator so adding knowledge does not change the grouping on reruns.
        relative = list(PurePosixPath(path).parent.relative_to(source_roots[directory]).parts)
        # Layout wrappers aren't useful code areas: frontend/src/features/chat
        # belongs to features-chat, not one giant frontend-src directory.
        while relative and relative[0] in {"frontend", "backend", "src", "harness", "main", "kotlin", "java"}:
            relative.pop(0)
        if relative:
            module = re.sub(r"[^a-z0-9-]+", "-", "-".join(relative[:2]).lower()).strip("-")
            if module in ("components", "models"):
                module += "-root"  # reserved repository owner axes cannot be nested
            directory = directory / module
        part = 1
        while True:
            page = str(directory / f"source-contracts-{part:02d}.md")
            title = f"{directory.name} 源码接口与集成边界 {part:02d}"
            current = head.get(page, _page_frontmatter(title, kind="architecture", today=today, tags=tags)
                               + "本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，"
                               "不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。\n")
            if Page.parse(current).frontmatter_field("type") != "architecture":
                skipped.append(path)
                break
            proposed = current.rstrip() + "\n\n" + block + "\n"
            # Keep well below the warning line; don't fill an owner with huge pages.
            if len(proposed.encode()) > 14_000 or page_over_capacity(proposed):
                part += 1
                continue
            head[page] = Page.parse(proposed).with_frontmatter_field("updated", today).render()
            link_page(page, title)
            break
    return skipped
