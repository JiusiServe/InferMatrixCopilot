"""Pinned semantic witnesses, separate from feature/file and rule coverage."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from ..knowledge_service.lifecycle import (
    DEPTH_ABSENCE_DETECTOR, DEPTH_BLOCK as _BLOCK, DEPTH_FACETS as FACETS, Page,
    depth_proof_basis, safe_source_path as safe_path,
)
from .init_stages import neutral_headings
from .knowledge_coverage import _LEXICAL_NO_CODE, inventory, matches

_PROOF = re.compile(r"\n<!-- kb:depth-proof (.*?) -->\s*$", re.S)
_PRIVATE_PATH = re.compile(r"/(?:home/(?!models(?:/|\b)|<)|data/(?!models?(?:/|\b)|<))[A-Za-z0-9_-]+")
_IP = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_draft(data: dict) -> None:
    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) > len(FACETS):
        raise ValueError("sections must list at most seven depth facets")
    seen = set()
    for section in sections:
        if not isinstance(section, dict) or section.get("facet") not in FACETS or section["facet"] in seen:
            raise ValueError("depth facets must be known and unique")
        seen.add(section["facet"])
        body = section.get("body")
        if not isinstance(body, str) or not body.strip() or len(body) > 1400 \
                or re.search(r"(?m)^\s*#", body) or "<!--" in body:
            raise ValueError("a depth section needs bounded prose without headings or metadata")
        if _PRIVATE_PATH.search(body) or any(not m.group().startswith("127.") for m in _IP.finditer(body)) \
                or "-----BEGIN PRIVATE KEY-----" in body:
            raise ValueError("depth prose contains machine-specific information")
        if section.get("interpretation") not in ("fact", "inference"):
            raise ValueError("depth interpretation must be fact or inference")
        basis = section.get("basis", "supported")
        if basis not in ("supported", "verified_absent"):
            raise ValueError("unknown depth basis")
        if basis == "verified_absent":
            if section["facet"] != "validation" or section["interpretation"] != "fact" \
                    or not isinstance(section.get("absence_certificate"), dict) or section.get("trace"):
                raise ValueError("verified absence needs a deterministic validation certificate")
        elif section.get("absence_certificate") is not None:
            raise ValueError("supported knowledge cannot carry an absence certificate")
        evidence = section.get("evidence")
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 4:
            raise ValueError("each depth facet needs one to four evidence spans")
        for item in evidence:
            if not isinstance(item, dict) or not safe_path(item.get("path")) \
                    or type(item.get("start")) is not int or type(item.get("end")) is not int \
                    or not 1 <= item["start"] <= item["end"]:
                raise ValueError("depth evidence needs safe paths and inclusive integer line spans")
        if section["facet"] == "flow":
            trace = section.get("trace")
            if not isinstance(trace, list) or not 2 <= len(trace) <= 6:
                raise ValueError("flow needs two to six named, ordered call steps")
            for step in trace:
                if not isinstance(step, dict) or not isinstance(step.get("symbol"), str) \
                        or not re.fullmatch(r"[\w.$]+", step["symbol"]) \
                        or not safe_path(step.get("path")) or type(step.get("start")) is not int \
                        or type(step.get("end")) is not int or not 1 <= step["start"] <= step["end"]:
                    raise ValueError("flow steps need symbols and source spans")
                if not any(e["path"] == step["path"] and e["start"] <= step["start"] <= step["end"] <= e["end"]
                           for e in evidence):
                    raise ValueError("each flow step must be contained in the cited evidence")


def source_span(tree: Path, entry: dict) -> str:
    if not safe_path(entry.get("path")) or type(entry.get("start")) is not int \
            or type(entry.get("end")) is not int or not 1 <= entry["start"] <= entry["end"]:
        raise ValueError("invalid depth evidence")
    file = tree / entry["path"]
    if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(tree.resolve()):
        raise ValueError("depth evidence escapes the pinned tree")
    lines = file.read_text(encoding="utf-8").splitlines(keepends=True)
    if entry["end"] > len(lines):
        raise ValueError("depth evidence exceeds the pinned file")
    return "".join(lines[entry["start"] - 1:entry["end"]])


def python_definitions(module: ast.AST) -> dict[str, ast.AST]:
    """Keep lexical owners so similarly named methods cannot impersonate one another."""
    found = {}

    def walk(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                found[name] = child
                walk(child, name + ".")
            else:
                walk(child, prefix)

    walk(module)
    return found


def _scope_nodes(node):
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            yield child
            yield from _scope_nodes(child)


def _scope_bindings(node) -> tuple[set[str], set[str], set[str]]:
    """Bindings created in this scope, excluding nested callable bodies."""
    definitions, assigned, imports = set(), set(), set()

    def walk(parent):
        for child in ast.iter_child_nodes(parent):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                definitions.add(child.name)
                # Definition headers run in the enclosing scope. Their named
                # expressions may rebind a callee without entering its body.
                headers = list(child.decorator_list)
                if isinstance(child, ast.ClassDef):
                    headers += list(child.bases) + list(child.keywords)
                else:
                    headers += [child.args] + ([child.returns] if child.returns else [])
                for header in headers:
                    walk(header)
                continue
            if isinstance(child, ast.Lambda):
                walk(child.args)
                continue
            if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                assigned.add(child.id)
            elif isinstance(child, ast.ExceptHandler) and child.name:
                assigned.add(child.name)
            elif isinstance(child, (ast.MatchAs, ast.MatchStar)) and child.name:
                assigned.add(child.name)
            elif isinstance(child, ast.MatchMapping) and child.rest:
                assigned.add(child.rest)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                imports.update(alias.asname or (alias.name.split(".")[0] if isinstance(child, ast.Import)
                                               else alias.name) for alias in child.names)
            walk(child)

    walk(node)
    return definitions, assigned, imports


def python_module_index(paths) -> dict[str, list[str]]:
    """Index tracked Python modules without assuming a configured sys.path."""
    index = {}
    for path in sorted(set(paths)):
        if not safe_path(path) or not path.endswith(".py"):
            continue
        parts = path.removesuffix(".py").removesuffix("/__init__").split("/")
        for offset in range(len(parts)):
            index.setdefault("/".join(parts[offset:]), []).append(path)
    return index


def resolve_python_module(name: str, index: dict[str, list[str]], *, exact: bool = False) -> str | None:
    """Prefer an exact root module; otherwise require one tracked suffix."""
    base = name.replace(".", "/")
    candidates = index.get(base, [])
    direct = [path for path in (base + ".py", base + "/__init__.py") if path in candidates]
    if direct:
        return direct[0] if len(direct) == 1 else None
    return candidates[0] if not exact and len(candidates) == 1 else None


def _module_matches(path: str, caller: str, node: ast.ImportFrom | ast.Import, name: str, *, resolver=None) -> bool:
    if resolver is None:
        return False  # a target suffix alone cannot establish import ownership
    if isinstance(node, ast.ImportFrom) and node.level:
        package = caller.split("/")[:-1]
        if node.level > len(package):
            return False
        prefix = package[:len(package) - node.level + 1]
        return path == resolver(".".join(prefix + (name.split(".") if name else [])), exact=True)
    return path == resolver(name)


def _calls_next(module, definition, step, target, *, resolver=None):
    aliases = {}

    def bind(local, resolved):
        # Conflicting imports do not establish a single pinned binding, even
        # if one branch imports the target. No import-order guess is made.
        aliases[local] = resolved if local not in aliases or aliases[local] == resolved else None

    for node in list(_scope_nodes(module)) + list(_scope_nodes(definition)):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bind(alias.asname or alias.name,
                     alias.name if _module_matches(target["path"], step["path"], node, node.module or "",
                                                    resolver=resolver) else None)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                bind(alias.asname or alias.name.split(".")[0],
                     "" if _module_matches(target["path"], step["path"], node, alias.name,
                                            resolver=resolver) else None)
    owner = step["symbol"].rsplit(".", 1)[0] if "." in step["symbol"] else ""
    parameters = {argument.arg for argument in definition.args.posonlyargs + definition.args.args
                  + definition.args.kwonlyargs}
    parameters.update(argument.arg for argument in (definition.args.vararg, definition.args.kwarg) if argument)
    # Defaults, decorators and annotations run when a definition is created,
    # so their calls cannot witness the function's runtime flow.
    runtime_nodes = []
    for statement in definition.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            runtime_nodes.extend([statement, *_scope_nodes(statement)])
    local_definitions, assigned, local_imports = _scope_bindings(definition)
    assigned.update(local_definitions)
    module_definitions, module_assigned, module_imports = _scope_bindings(module)
    if "*" in local_imports | module_imports:
        return False

    def reference(node, *, qualified=False):
        names = []
        while isinstance(node, ast.Attribute):
            names.insert(0, node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        names.insert(0, node.id)
        if qualified and owner and names[0] in ("self", "cls"):
            names = owner.split(".") + names[1:]
        return tuple(names)

    mutated_attributes = {reference(node, qualified=True) for node in runtime_nodes
                          if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del))}
    for call in runtime_nodes:
        if not isinstance(call, ast.Call) or not step["start"] <= call.lineno <= step["end"]:
            continue
        names = reference(call.func)
        if names is None:
            continue  # object dispatch needs a runtime/type witness, not a name guess
        if reference(call.func, qualified=True) in mutated_attributes:
            continue  # an explicit write invalidates this exact method binding
        root = names[0]
        if root in assigned or root in parameters and not (root in ("self", "cls") and owner):
            continue
        if root in aliases:
            if aliases[root] is None or root in module_assigned or root in module_definitions:
                continue
            resolved = ".".join(((aliases[root],) if aliases[root] else ()) + names[1:])
            if resolved == target["symbol"]:
                return True
        elif step["path"] == target["path"]:
            if root in module_assigned:
                continue
            resolved = ".".join(names)
            if root in ("self", "cls") and owner:
                resolved = owner + "." + ".".join(names[1:])
            if resolved == target["symbol"]:
                return True
    return False


def _lexical_code(raw: str) -> str:
    # Preserve offsets and line boundaries when removing comments/literals.
    return _LEXICAL_NO_CODE.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), raw)


def _closing(code: str, opening: int) -> int:
    pairs = {"(": ")", "{": "}", "[": "]"}
    stack = []
    for index in range(opening, len(code)):
        char = code[index]
        if char in pairs:
            stack.append(pairs[char])
        elif char in pairs.values():
            if not stack or stack.pop() != char:
                break
            if not stack:
                return index
    raise ValueError("flow lexical delimiters are incomplete or ambiguous")


def _function_body(code: str, start: int) -> tuple[int, int]:
    opening = code.find("(", start)
    if opening < 0:
        raise ValueError("flow lexical parameters are unresolved")
    params_end = _closing(code, opening)
    body = code.find("{", params_end + 1)
    between = code[params_end + 1:body].strip() if body >= 0 else ";"
    if body < 0 or ";" in between or "=" in between or between == ":" \
            or between and not between.startswith(":"):
        raise ValueError("flow lexical function body is unresolved")
    return body, _closing(code, body)


def _expression_end(code: str, start: int) -> int:
    end = start
    while end < len(code) and code[end] not in ",;\n)}]":
        end = _closing(code, end) + 1 if code[end] in "({[" else end + 1
    return end


def _lexical_name_writes(code: str, symbol: str) -> list[int]:
    """Conservative direct writes, including compound and destructured forms."""
    name = re.escape(symbol)
    writes = [match.start() for pattern in (
        r"(?<![\w$.])" + name + r"\s*(?:=(?!=|>)|(?:&&|\|\||\?\?|[+*/%&|^\-])=|\+\+|--)",
        r"(?:\+\+|--)\s*" + name + r"\b",
        r"\bdelete\s+" + name + r"\b",
        r"\bfor\s*\(\s*" + name + r"\s+(?:of|in)\b",
    ) for match in re.finditer(pattern, code)]
    for match in re.finditer(r"(?:\[[^\]\n]*\]|\{[^}\n]*\})\s*=(?!=|>)", code):
        if re.search(r"\b" + name + r"\b", match.group()):
            writes.append(match.start())
    return writes


def _lexical_definition(raw: str, step: dict) -> tuple[str, int, int]:
    """Bind a span to one actual module function, never a homonymous method."""
    if "." in step["symbol"]:
        raise ValueError("flow lexical object/type ownership is unresolved")
    code = _lexical_code(raw)
    name = re.escape(step["symbol"])
    declarations = list(re.finditer(r"\b(?:function|fun)\s+" + name + r"\s*\(|\bconst\s+" + name
                                   + r"\s*(?::[^=;\n]+)?=\s*(?:async\s+)?", code))
    matches = []
    for declaration in declarations:
        prefix = code[:declaration.start()]
        boundary = max(prefix.rfind("\n"), prefix.rfind(";"), prefix.rfind("}"))
        if any(prefix.count(a) != prefix.count(b) for a, b in (("{", "}"), ("(", ")"), ("[", "]"))) \
                or prefix[boundary + 1:].strip() not in ("", "export", "async", "export async", "export default", "suspend"):
            continue
        try:
            if declaration.group().lstrip().startswith("const"):
                initializer = declaration.end()
                if code.startswith("function", initializer):
                    body, end = _function_body(code, initializer)
                elif initializer < len(code) and code[initializer] == "(":
                    params_end = _closing(code, initializer)
                    # Parse the initializer's own parameter list. A regex that
                    # searches ahead for an arrow can bind a later declaration
                    # to a non-callable value such as `(1)\nconst other = ...`.
                    arrow = re.match(r"\s*(?::\s*[\w$.[\]<>|?, ]+)?\s*=>", code[params_end + 1:])
                    if not arrow:
                        continue
                    body = params_end + 1 + arrow.end()
                    while body < len(code) and code[body].isspace():
                        body += 1
                    if body >= len(code):
                        continue
                    end = _closing(code, body) if code[body] == "{" else _expression_end(code, body) - 1
                    if end < body:
                        continue
                else:
                    continue
            else:
                body, end = _function_body(code, declaration.start())
        except ValueError:
            continue
        matches.append((declaration.start(), body, end))
    if len(matches) != 1:
        raise ValueError("flow symbol is not declared as one pinned module-level definition")
    start, body, end = matches[0]
    module_scope = _execution_scope(code, -1)
    if any(not start <= write < body for write in _lexical_name_writes(module_scope, step["symbol"])):
        raise ValueError("flow module-level definition binding is overwritten or ambiguous")
    if not step["start"] <= code[:start].count("\n") + 1 <= code[:body].count("\n") + 1 <= step["end"] \
            or step["end"] > code[:end].count("\n") + 1:
        raise ValueError("flow symbol/span is not a pinned module-level definition")
    if "/" in code[body:end + 1]:
        raise ValueError("flow lexical syntax has an unresolved regex, division or JSX boundary")
    lines = code.splitlines(keepends=True)
    offset = sum(map(len, lines[:step["start"] - 1]))
    return "".join(lines[step["start"] - 1:step["end"]]), body - offset - (code[body] != "{"), end - offset


def _execution_scope(span: str, body: int) -> str:
    """Remove nested callable bodies; their creation does not prove execution."""
    scope = list(span)
    ranges = []
    for match in re.finditer(r"\b(?:function|fun)\b|\bclass\b|=>|\b([\w$]+)\s*\(", span[body + 1:]):
        start = body + 1 + match.start()
        token = match.group()
        if token == "class":
            opening = span.find("{", start)
            if opening < 0:
                raise ValueError("flow nested class is unresolved")
            ranges.append((start, _closing(span, opening) + 1))
        elif token in ("function", "fun"):
            _, end = _function_body(span, start)
            ranges.append((start, end + 1))
        elif token == "=>":
            opening = start + 2
            while opening < len(span) and span[opening].isspace():
                opening += 1
            if opening < len(span) and span[opening] == "{":
                end = _closing(span, opening) + 1
            else:
                end = _expression_end(span, opening)
            ranges.append((start, end))
        elif match[1] not in ("if", "for", "while", "switch", "catch", "with"):
            opening = body + 1 + match.end() - 1
            closing = _closing(span, opening)
            after = closing + 1
            while after < len(span) and span[after].isspace():
                after += 1
            if after < len(span) and span[after] in "{:":
                _, end = _function_body(span, start)
                ranges.append((start, end + 1))
    for start, end in ranges:
        scope[start:end] = ["\n" if c == "\n" else " " for c in scope[start:end]]
    return "".join(scope)


def _lexical_calls_next(tree: Path, raw: str, span: str, step: dict, target: dict, *, execution: str) -> bool:
    """Admit only an unshadowed local name or a bound relative ES import."""
    symbol = target["symbol"]
    if "." in symbol:
        return False  # object/type dispatch needs a language-specific witness
    name = re.escape(symbol)
    clean = _LEXICAL_NO_CODE.sub("", raw)
    candidates = []
    if step["path"] == target["path"]:
        declarations = [match for match in re.finditer(
            r"(?:function|fun)\s+" + name + r"\b|\b(?:const|let|var)\s+" + name + r"\s*(?::[^=;\n]+)?=", clean)
            if clean[:match.start()].count("{") == clean[:match.start()].count("}")]
        if len(declarations) != 1:
            return False
        candidates.append((symbol, r"(?<![\w$.])" + name + r"\s*\("))
    else:
        imports = _LEXICAL_NO_CODE.sub(lambda match: match.group() if match.group().startswith(("'", '"'))
                                      else "\n" * match.group().count("\n"), raw)

        def resolves(specifier):
            if not specifier.startswith("."):
                return False
            root = tree.resolve()
            base = (tree / step["path"]).parent.joinpath(specifier).resolve()
            if not base.is_relative_to(root):
                return False
            paths = [base] if base.suffix else [Path(str(base) + extension) for extension in
                    (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")] + [base / ("index" + extension)
                    for extension in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")]
            existing = [path for path in paths if path.is_file() and not path.is_symlink()]
            return len(existing) == 1 and existing[0] == (tree / target["path"]).resolve()

        for bindings, specifier in re.findall(r"\bimport\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", imports):
            if not resolves(specifier):
                continue
            for binding in bindings.split(","):
                match = re.fullmatch(r"\s*([\w$]+)(?:\s+as\s+([\w$]+))?\s*", binding)
                if match and match[1] == symbol:
                    local = match[2] or match[1]
                    candidates.append((local, r"(?<![\w$.])" + re.escape(local) + r"\s*\("))
        for local, specifier in re.findall(r"\bimport\s*\*\s+as\s+([\w$]+)\s*from\s*['\"]([^'\"]+)['\"]", imports):
            if resolves(specifier):
                candidates.append((local, r"(?<![\w$.])" + re.escape(local) + r"\s*\.\s*" + name + r"\s*\("))
    # A TypeScript object type in parameters is not the function body.
    opening = span.find("(")
    level, closing = 0, None
    if opening >= 0:
        for index in range(opening, len(span)):
            level += (span[index] == "(") - (span[index] == ")")
            if level == 0:
                closing = index + 1
                break
    header = span[:closing] if closing else span.split("{", 1)[0]
    for local, pattern in candidates:
        if re.search(r"\b" + re.escape(local) + r"\b", header) \
                or re.search(r"\b(?:const|let|var)\s+" + re.escape(local) + r"\b", span) \
                or re.search(r"\b(?:function|fun|class)\s+" + re.escape(local) + r"\b", span) \
                or _lexical_name_writes(span, local):
            continue
        for call in re.finditer(pattern, execution):
            if not re.search(r"\b(?:function|fun)\s*$", execution[:call.start()]):
                return True
    return False


def verify_trace(tree: Path, trace: list[dict]) -> None:
    """Verify a representative static call chain; no runtime coverage claim."""
    identities = [(s["path"], s["symbol"], s["start"], s["end"]) for s in trace]
    if len(set(identities)) != len(identities) or len(trace) < 2:
        raise ValueError("flow steps must be distinct")
    resolver = None
    for i, step in enumerate(trace):
        raw = (tree / step["path"]).read_text(encoding="utf-8")
        span = source_span(tree, step)
        name = step["symbol"].rsplit(".", 1)[-1]
        if step["path"].endswith(".py"):
            if resolver is None:
                # DepthContext owns the complete tracked-path inventory used
                # by both extraction and pinned proof replay.
                from .depth_inputs import DepthContext
                index = python_module_index(DepthContext(tree, [])._tracked())
                resolver = lambda name, *, exact=False: resolve_python_module(name, index, exact=exact)
            module = ast.parse(raw)
            definition = python_definitions(module).get(step["symbol"])
            _, module_assigned, module_imports = _scope_bindings(module)
            if (not isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef))
                    or not definition.lineno <= step["start"] <= step["end"] <= definition.end_lineno
                    or step["symbol"].split(".")[0] in module_assigned | module_imports
                    or "*" in module_imports):
                raise ValueError("flow symbol/span is not a pinned definition")
            if i + 1 < len(trace):
                if not _calls_next(module, definition, step, trace[i + 1], resolver=resolver):
                    raise ValueError("flow span does not call the next named step")
        else:
            span, body, _ = _lexical_definition(raw, step)
            execution = _execution_scope(span, body)
            if i + 1 < len(trace) and not _lexical_calls_next(tree, raw, span, step, trace[i + 1], execution=execution):
                raise ValueError("flow span does not show the next call")


def build_absence_certificate(tree: Path, policy, feature, pin: str, facet: str = "validation") -> dict | None:
    """Attest absence of statically associated test entries, never global absence.

    The detector owns the complete test inventory and unresolved relationships.
    A generator-provided search, omitted result, or partial scope cannot certify
    absence. Replaying the same factory verifies persisted certificates.
    """
    if facet != "validation":
        return None
    from .depth_inputs import DepthContext

    production = inventory(tree, policy)
    scope = sorted(set(feature.entry_points) | {p for p in production if matches(p, feature.source_globs)})
    if not scope or any(p not in production for p in scope):
        return None
    docs, doc_hashes = [], []
    for path in feature.docs:
        document = tree / path
        if not safe_path(path) or not document.is_file() or document.is_symlink() \
                or not document.resolve().is_relative_to(tree.resolve()):
            return None
        try:
            raw = document.read_bytes()
            docs.append({"path": path, "text": raw.decode("utf-8")})
            doc_hashes.append((path, hashlib.sha256(raw).hexdigest()))
        except (OSError, UnicodeError):
            return None
    try:
        association = DepthContext(tree, production).test_association(feature, docs)
    except (OSError, UnicodeError, SyntaxError, ValueError):
        return None
    if association.get("complete") is not True or association.get("matched_files") \
            or association.get("unresolved_files") or sorted(association.get("source_scope", [])) != scope \
            or association.get("checker_version") != DEPTH_ABSENCE_DETECTOR:
        return None
    source_hashes = []
    for path in scope:
        source = tree / path
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(tree.resolve()):
            return None
        try:
            source_hashes.append((path, hashlib.sha256(source.read_bytes()).hexdigest()))
        except OSError:
            return None
    policy_scope = {"roots": policy.roots, "exclude": policy.exclude, "suffixes": policy.suffixes,
                    "filenames": policy.filenames, "feature": feature.id,
                    "source_globs": feature.source_globs, "entry_points": feature.entry_points, "docs": feature.docs}
    certificate = {"version": 1, "detector": DEPTH_ABSENCE_DETECTOR, "feature": feature.id,
                   "facet": facet, "pin": pin, "policy_sha256": digest(json.dumps(policy_scope, sort_keys=True)),
                   "source_scope_sha256": digest(json.dumps(source_hashes)), "source_files": len(scope),
                   "docs_scope_sha256": digest(json.dumps(doc_hashes)),
                   "test_inventory_sha256": association.get("inventory_sha256"),
                   "test_files": len(association.get("scope_files", []))}
    depth_proof_basis({"basis": "verified_absent", "absence_certificate": certificate}, facet=facet, pin=pin)
    return certificate


def render_block(feature, section: dict, tree: Path, full_name: str, pin: str, *, policy=None) -> str:
    proof = {"evidence": [{**e, "sha256": digest(source_span(tree, e))} for e in section["evidence"]],
             "trace": section.get("trace", []), "basis": section.get("basis", "supported")}
    if proof["basis"] == "verified_absent":
        if policy is None:
            raise ValueError("absence proof needs the reviewed coverage policy")
        certificate = build_absence_certificate(tree, policy, feature, pin, section["facet"])
        if certificate is None or certificate != section.get("absence_certificate"):
            raise ValueError("absence scope is unresolved or differs from the deterministic detector")
        proof["absence_certificate"] = certificate
    depth_proof_basis(proof, facet=section["facet"], pin=pin)
    if section["facet"] == "flow":
        verify_trace(tree, proof["trace"])
    title = " ".join(str(section.get("title") or section["facet"]).replace("#", "").split())
    body = neutral_headings(f"## {title}\n\n")
    if proof["basis"] == "verified_absent":
        body += "已核验缺口（非测试通过证明）：\n\n"
    if section["interpretation"] == "inference":
        body += "设计推断（非作者历史意图）：\n\n"
    body += section["body"].strip() + "\n\n"
    if proof["trace"]:
        body += "调用路径：" + " → ".join(chr(96) + s["path"] + chr(96) + "（" + chr(96) + s["symbol"] + chr(96) + "）"
                                    for s in proof["trace"]) + "\n\n"
    body += "来源：" + ", ".join(
        f"[{e['path']}:L{e['start']}–L{e['end']}](https://github.com/{full_name}/blob/{pin}/"
        f"{quote(e['path'], safe='/')}#L{e['start']}-L{e['end']})" for e in section["evidence"]) + "\n"
    body += "\n<!-- kb:depth-proof " + json.dumps(proof, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + " -->"
    return (f"<!-- kb:depth feature={feature.id} facet={section['facet']} pin={pin} sha256={digest(body)} -->\n"
            + body + "\n<!-- /kb:depth -->")


def verified_blocks(text: str, feature, tree: Path, pin: str, *, policy=None) -> tuple[dict[str, str], list[str]]:
    blocks, problems, invalid = {}, [], set()
    try:
        page = Page.parse(text)
        if page.frontmatter_field("type") not in ("architecture", "guide") or page.rules():
            return {}, ["depth target must be explanatory, without rules"]
    except Exception as exc:
        return {}, [str(exc)]
    for fid, facet, sha, hashed, body in _BLOCK.findall(text):
        if fid != feature.id or facet not in FACETS:
            continue
        try:
            if facet in blocks or facet in invalid or sha != pin or digest(body) != hashed:
                raise ValueError("duplicate, stale or edited depth block")
            match = _PROOF.search(body)
            if not match:
                raise ValueError("depth block has no bound evidence proof")
            proof = json.loads(match.group(1))
            basis = depth_proof_basis(proof, facet=facet, pin=pin)
            if basis == "verified_absent":
                if policy is None or proof["absence_certificate"]["feature"] != feature.id \
                        or build_absence_certificate(tree, policy, feature, pin, facet) != proof["absence_certificate"] \
                        or "已核验缺口（非测试通过证明）" not in body:
                    raise ValueError("absence certificate failed its pinned policy replay")
            if not isinstance(proof.get("evidence"), list) or not 1 <= len(proof["evidence"]) <= 4:
                raise ValueError("invalid depth proof spans")
            for e in proof["evidence"]:
                if e.get("sha256") != digest(source_span(tree, e)):
                    raise ValueError("depth evidence changed at the pin")
            if facet == "flow":
                trace = proof.get("trace", [])
                if not 2 <= len(trace) <= 6 or any(not any(
                        e["path"] == s["path"] and e["start"] <= s["start"] <= s["end"] <= e["end"]
                        for e in proof["evidence"]) for s in trace):
                    raise ValueError("flow trace is not contained in its evidence")
                verify_trace(tree, trace)
            blocks[facet] = (f"<!-- kb:depth feature={fid} facet={facet} pin={sha} sha256={hashed} -->\n"
                             + body + "\n<!-- /kb:depth -->")
        except (ValueError, KeyError, TypeError, SyntaxError, OSError, UnicodeError) as exc:
            problems.append(f"{feature.id}/{facet}: {exc}")
            invalid.add(facet)
            blocks.pop(facet, None)
    return blocks, problems


def depth_page(feature) -> str:
    return str(PurePosixPath(feature.page).with_name(f"feature-depth-{feature.id}.md"))


def audit_depth(head: dict[str, str], tree: Path, policy, pin: str, *, approvals: list[dict] | None = None) -> dict:
    """Recompute positive and recognized coverage without changing the denominator."""
    production = set(inventory(tree, policy))
    witnessed, features, errors, binding_errors = set(), {}, [], []
    approval_index = {}
    if approvals is not None:
        for row in approvals:
            if not isinstance(row, dict) or row.get("facet") not in FACETS or not isinstance(row.get("feature"), str):
                binding_errors.append("malformed native approval binding")
                continue
            key = (row["feature"], row["facet"])
            if key in approval_index:
                approval_index[key] = None
                binding_errors.append("duplicate native approval binding: " + "/".join(key))
            else:
                approval_index[key] = row
    for feature in policy.features:
        page = depth_page(feature)
        blocks, problems = verified_blocks(head[page], feature, tree, pin, policy=policy) if page in head else ({}, [])
        if "flow" in blocks:
            proof = json.loads(_PROOF.search(_BLOCK.search(blocks["flow"]).group(5)).group(1))
            if any(s["path"] not in production for s in proof["trace"]):
                blocks.pop("flow")
                problems.append(f"{feature.id}/flow: trace must use production implementation")
        errors.extend(problems)
        basis = {}
        for facet, block in list(blocks.items()):
            if approvals is not None:
                row = approval_index.get((feature.id, facet))
                expected_dimensions = {"faithful": "yes", "non_contradictory": "yes", "does_not_weaken": "yes"}
                if not row or row.get("page") != page or row.get("block_sha256") != digest(block) \
                        or row.get("dimensions") != expected_dimensions \
                        or not isinstance(row.get("native_trace_id"), str) or not row["native_trace_id"] \
                        or not isinstance(row.get("native_reply_sha256"), str) \
                        or not re.fullmatch(r"[0-9a-f]{64}", row["native_reply_sha256"]) \
                        or row.get("pin", pin) != pin:
                    binding_errors.append(f"{feature.id}/{facet}: missing or mismatched all-yes native approval")
                    blocks.pop(facet)
                    continue
            proof = json.loads(_PROOF.search(_BLOCK.search(block).group(5)).group(1))
            basis[facet] = depth_proof_basis(proof, facet=facet, pin=pin)
            if basis[facet] == "supported":
                witnessed.update(e["path"] for e in proof["evidence"] if e["path"] in production)
        supported = [f for f in FACETS if basis.get(f) == "supported"]
        absent = [f for f in FACETS if basis.get(f) == "verified_absent"]
        recognized = [f for f in FACETS if f in basis]
        unknown = [f for f in FACETS if f not in basis]
        features[feature.id] = {"owner": feature.owner, "page": page, "facets": supported,
                               "missing_facets": [f for f in FACETS if f not in supported],
                               "complete": len(supported) == len(FACETS), "basis": basis,
                               "verified_absent_facets": absent, "recognized_facets": recognized,
                               "unknown_facets": unknown, "recognized_complete": not unknown}
    slots = len(policy.features) * len(FACETS)
    covered = sum(len(x["facets"]) for x in features.values())
    recognized = sum(len(x["recognized_facets"]) for x in features.values())
    threshold = policy.semantic_depth_per_facet_gt
    facet_counts = {}
    for facet in FACETS:
        supported = sum(x["basis"].get(facet) == "supported" for x in features.values())
        absent = sum(x["basis"].get(facet) == "verified_absent" for x in features.values())
        count = supported + absent
        ratio = count / len(features) if features else 0.0
        facet_counts[facet] = {"supported": supported, "verified_absent": absent,
                               "unknown": len(features) - count, "recognized": count, "ratio": ratio,
                               "target_met": threshold is None or ratio > threshold}
    all_features_recognized = bool(features) and all(x["recognized_facets"] for x in features.values())
    target_met = not errors and not binding_errors and (threshold is None or
                 all_features_recognized and all(x["target_met"] for x in facet_counts.values()))
    return {"pin": pin, "features": features, "complete_features": sum(x["complete"] for x in features.values()),
            "total_features": len(features), "covered_facets": covered, "total_facets": slots,
            "facet_ratio": covered / slots if slots else 0.0, "recognized_facets": recognized,
            "recognized_facet_ratio": recognized / slots if slots else 0.0,
            "recognized_complete_features": sum(x["recognized_complete"] for x in features.values()),
            "recognized_feature_count": sum(bool(x["recognized_facets"]) for x in features.values()),
            "facet_counts": facet_counts, "per_facet_gt": threshold, "target_met": target_met,
            "approval_bindings_checked": approvals is not None, "approval_binding_problems": binding_errors,
            "production_files_with_semantic_evidence": sorted(witnessed), "production_files_total": len(production),
            "problems": errors, "complete": covered == slots and not errors and not binding_errors,
            "recognized_complete": recognized == slots and not errors and not binding_errors,
            "interpretation": "Positive supported witnesses remain separate from verified gaps. Recognized coverage "
                              "includes both, without claiming capabilities, exhaustive behavior, or tests passed."}
