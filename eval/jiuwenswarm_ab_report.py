"""Build a compact Chinese report from immutable JiuwenSwarm eval receipts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
from urllib.parse import quote
from zoneinfo import ZoneInfo

FACETS = {"flow": "执行流程", "api": "API 契约", "configuration": "配置与默认行为",
          "dependencies": "依赖与关联功能", "failure_modes": "失败与降级行为",
          "tradeoffs": "设计取舍", "validation": "验证与测试入口"}
PIN = "f0a69728c96b5961d993449f1a901cbd2f4dac5b"
KNOWLEDGE_COMMIT = "58279d334cd827adb631891a760bb14efe376420"


def load(path, default=None):
    path = Path(path)
    return json.loads(path.read_bytes()) if path.is_file() else default


def binding(path):
    path = Path(path)
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def public_paths(value, state, project):
    """Publish logical artifact names; retain machine paths only in raw receipts."""
    if isinstance(value, dict): return {k: public_paths(v, state, project) for k, v in value.items()}
    if isinstance(value, list): return [public_paths(v, state, project) for v in value]
    if isinstance(value, str) and value.startswith("/"):
        path = Path(value)
        if path.is_relative_to(state): return f"{state.name}/{path.relative_to(state).as_posix()}"
        if path.is_relative_to(project): return f"repository/{path.relative_to(project).as_posix()}"
        return f"external-artifact/{path.name}"
    return value


def validate_evaluation(study, campaign, collection, truth, scores):
    """Never turn equal counters from different experiments into A/B results."""
    campaign_sha = binding(study / "campaign.json")["sha256"]
    identity = load(study / "identity.json", {})
    if identity and identity.get("campaign_sha256") != campaign_sha:
        raise ValueError("runtime belongs to a different campaign")
    if identity:
        unsigned = {k: v for k, v in identity.items() if k != "identity_sha256"}
        if hashlib.sha256(json.dumps(unsigned, sort_keys=True).encode()).hexdigest() != identity.get("identity_sha256"):
            raise ValueError("runtime identity digest changed")
    if collection and (not identity or collection.get("identity_sha256") != identity.get("identity_sha256")):
        raise ValueError("collection identity does not match the frozen runtime")
    if truth and truth.get("campaign_sha256") != campaign_sha:
        raise ValueError("truth belongs to a different campaign")
    if truth:
        cases = {c["number"]: c for c in campaign["cases"]}
        rows = truth.get("cases", [])
        if len(rows) != len(cases) or {r["pr"] for r in rows} != set(cases):
            raise ValueError("truth must account for each frozen PR once")
        for row in rows:
            path = Path(row["path"])
            record = load(path, {})
            case = cases[row["pr"]]
            if not path.is_file() or binding(path)["sha256"] != row.get("sha256") or record.get("pr") != row["pr"] or \
                    any(record.get(k) != case[k] for k in ("base", "head")) or \
                    record.get("campaign_sha256") != campaign_sha or record.get("status") != row.get("status"):
                raise ValueError("truth source identity or frozen bytes changed")
        prerequisite = load(study / "truth-prerequisite.json", {})
        if prerequisite and prerequisite.get("sha256") != binding(study / "private-codex/truth-manifest.json")["sha256"]:
            raise ValueError("pre-review truth freeze changed")
    expected = {(c["number"], a, r) for c in campaign["cases"] for a in ("A", "B") for r in range(3)}
    formal = [r for r in collection.get("results", []) if not r.get("preflight")]
    slots = [(r["number"], r["arm"], r["repetition"] - 1) for r in formal]
    if len(slots) != len(set(slots)) or not set(slots).issubset(expected):
        raise ValueError("invalid or duplicate native review slots")
    if collection and (len(formal) != collection.get("completed_results") or
                       sum(r["status"] == "valid" for r in formal) != collection.get("valid_reviews")):
        raise ValueError("native completion counts do not match receipts")
    if scores:
        if scores.get("campaign_sha256") != campaign_sha:
            raise ValueError("scores belong to a different campaign")
        for key, path in (("truth_manifest_sha256", study / "private-codex/truth-manifest.json"),
                          ("reviews_manifest_sha256", study / "reviews-manifest.json")):
            if not path.exists() or scores.get(key) != binding(path)["sha256"]:
                raise ValueError("scoring frozen inputs changed")
        scored_slots = [(r["pr"], r["arm"], r["repeat"]) for r in scores.get("samples", [])]
        if len(scored_slots) != len(set(scored_slots)) or set(scored_slots) != expected or set(slots) != expected:
            raise ValueError("scoring must account for all 72 native review slots")
        completed_score = sum(r["status"] == "complete" for r in scores["samples"])
        if completed_score != scores.get("scoring_completion", {}).get("scored_review_samples"):
            raise ValueError("scoring counts do not match samples")


def pct(value):
    return "不可计算" if value is None else f"{100 * value:.2f}%"


def num(value):
    return "未知" if value is None else f"{value:.2f}"


def source_link(path, line=None):
    return f"https://github.com/openJiuwen-ai/jiuwenswarm/blob/{PIN}/{quote(path, safe='/')}" + (f"#L{line}" if line else "")


def knowledge_link(path):
    return f"https://github.com/JiusiServe/InferMatrixCopilot/blob/{KNOWLEDGE_COMMIT}/{quote(path, safe='/')}"


def distribution(values):
    values = sorted(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))
    def percentile(fraction):
        if not values: return None
        index = (len(values) - 1) * fraction
        low = int(index)
        high = min(low + 1, len(values) - 1)
        return values[low] + (values[high] - values[low]) * (index - low)
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
            "p50": percentile(.5), "p90_linear": percentile(.9)}


def subgroup_operational(reviews, samples, prs):
    """Keep failures in completion and distinguish classification from advice."""
    result = {}
    for arm in ("A", "B"):
        rows = [r for r in reviews if not r.get("preflight") and r["number"] in prs and r["arm"] == arm]
        valid = [r for r in rows if r["status"] == "valid"]
        scored = [r["metrics"] for r in samples if r["pr"] in prs and r["arm"] == arm and r["status"] == "complete"]
        counts = {k: sum(r.get(k, 0) or 0 for r in scored) for k in
                  ("TP", "FP", "unknown", "nondefect_advice", "novel_valid_defects", "advice_valid", "advice_invalid", "advice_unknown", "advice_valid_actionable")}
        if any(r.get("novel_valid_defects") is None for r in scored):
            counts["novel_valid_defects"] = None
        defects = counts["TP"] + counts["FP"] + counts["unknown"]
        result[arm] = {"expected": len(prs) * 3, "valid": len(valid), "terminal": len(rows), "scored": len(scored), "counts": counts,
                       "unknown_share": counts["unknown"] / defects if defects else None,
                       "classification_unit": "root causes deduplicated within review; repeat findings remain separate samples",
                       "timings_valid": {k: distribution([r.get(k) for r in valid]) for k in
                                         ("native_seconds", "queue_seconds", "end_to_end_seconds")}}
    return result


def knowledge_exposure(reviews, campaign):
    """Measure supplied bytes; a router label alone is not an intact facet."""
    from infermatrix_copilot.knowledge_service.lifecycle import depth_sections
    result = {}
    for arm in ("A", "B"):
        rows = [r for r in reviews if not r.get("preflight") and r["arm"] == arm]
        full, partial, available, extra_chars, totals = [], [], [], [], []
        for row in rows:
            attempt = row["attempts"][-1]
            related = load(Path(attempt["attempt_root"]) / "related.json", {})
            f = p = a = 0
            for doc in related.get("documents", []):
                path = Path(campaign["arms"][arm]["doc_root"]) / doc["path"]
                if binding(path)["sha256"] != doc["snapshot_sha256"]:
                    raise ValueError("injected document snapshot changed")
                sections = {s["facet"]: s for s in depth_sections(path.read_text())}
                a += len(doc.get("available_facets", []))
                for facet in doc.get("included_facets", []):
                    section = sections.get(facet)
                    if section and section["content"].strip() in doc["content"]:
                        f += 1
                    else:
                        p += 1
            full.append(f); partial.append(p); available.append(a)
            total = attempt.get("knowledge_chars_cumulative")
            if total is not None:
                if total > 6000: raise ValueError("actual knowledge consumption exceeds review budget")
                totals.append(total)
                extra_chars.append(total - row["initial_knowledge_chars"])
        result[arm] = {"review_samples": len(rows), "initial_intact_facets": distribution(full),
                       "initial_partial_facets": distribution(partial), "available_facets_on_selected_pages": distribution(available),
                       "knowledge_chars_consumed": distribution(totals), "followup_knowledge_chars": distribution(extra_chars),
                       "interpretation": "A has no KB facet markers; zero labels does not mean zero explanatory content."}
    return result


def paired_quality(per_pr):
    value = {}
    for field in ("defect_precision", "confirmed_recall", "advice_validity"):
        pairs = [{"pr": row["pr"], "A": row["arms"]["A"][field], "B": row["arms"]["B"][field]}
                 for row in per_pr if all(row["arms"][arm].get(field) is not None for arm in ("A", "B"))]
        a = statistics.mean(p["A"] for p in pairs) if pairs else None
        b = statistics.mean(p["B"] for p in pairs) if pairs else None
        value[field] = {"A": a, "B": b, "B_minus_A": b-a if pairs else None,
                        "applicable_prs": len(pairs), "prs": [p["pr"] for p in pairs]}
    return value


def refresh_upstream(state):
    """Observe develop at delivery; never move the knowledge or PR source pins."""
    from eval.jiuwenswarm_docs_compare import coverage_policy
    state = Path(state).resolve()
    inv = load(state / "mapping/inventory.json")
    campaign = load(state / "evaluation-v2/campaign.json")
    project = Path(__file__).resolve().parents[1]
    source = Path(campaign["baseline_source_root"])
    def command(args):
        return subprocess.check_output(args, cwd=source)
    raw = command(["gh", "api", "repos/openJiuwen-ai/jiuwenswarm/branches/develop"])
    observed = json.loads(raw)
    head = observed["commit"]["sha"]
    if subprocess.run(["git", "cat-file", "-e", head + "^{commit}"], cwd=source, capture_output=True).returncode:
        command(["git", "fetch", "--no-tags", "--no-write-fetch-head", "origin", head])
    behind, ahead = map(int, command(["git", "rev-list", "--left-right", "--count", f"{PIN}...{head}"]).split())
    changed = [p for p in command(["git", "diff", "--name-only", "-z", PIN, head, "--"]).decode().split("\0") if p]
    policy = coverage_policy(project)
    affected = [f.id for f in policy.features if any(fnmatch.fnmatchcase(p, g) for p in changed for g in (*f.source_globs, *f.docs))]
    production = sorted(set(changed).intersection(inv["production"]))
    receipt = state / "freshness-branch-develop.json"
    receipt.write_bytes(raw)
    value = {"schema": "jiuwenswarm-upstream-freshness-v1", "source_pin": PIN,
             "checked_at_cn": datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
             "head_sha": head, "head_date": observed["commit"]["commit"]["committer"]["date"],
             "ahead_by": ahead, "behind_by": behind, "changed_production_files": len(production),
             "production_scope": "same fixed 2199-file inventory; new files are listed separately in changed_paths",
             "affected_features": affected, "changed_paths": changed, "branch_receipt": binding(receipt),
             "consistency_claim": "one observed branch snapshot; not a continuously live guarantee"}
    (state / "upstream-freshness.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return value


def build(state: Path, output: Path, study: Path | None = None):
    from eval.jiuwenswarm_ab_judge import aggregate
    from eval.jiuwenswarm_ab_diagnostics import diagnose_run

    state, output = state.resolve(), output.resolve()
    study = (study or state / "evaluation-v2").resolve()
    project = Path(__file__).resolve().parents[1]
    inventory = load(state / "mapping/inventory.json")
    mapping = load(state / "mapping/author-mapping.json")
    if inventory is None or mapping is None or inventory["pin"] != PIN or mapping["pin"] != PIN:
        raise ValueError("original mapping and inventories must exist at the exact source pin")
    if inventory["feature_count"] != 79 or mapping["facet_denominator"] != 553:
        raise ValueError("fixed feature/facet denominators changed")
    if inventory["knowledge_commit"] != KNOWLEDGE_COMMIT:
        raise ValueError("knowledge snapshot is not the fixed merged PR290 content")
    final = load(project / "eval/knowledge-depth/jiuwenswarm-repair63-final-20261002.json")
    if final["source_pin"] != PIN:
        raise ValueError("knowledge acceptance source pin changed")
    campaign = load(study / "campaign.json")
    collection = load(study / "collection.json", {})
    scores = load(study / "private-codex/results.json", {})
    truth = load(study / "private-codex/truth-manifest.json", {})
    validate_evaluation(study, campaign, collection, truth, scores)
    exposure = knowledge_exposure(collection.get("results", []), campaign)
    diagnostics = diagnose_run(study) if collection else {}
    if diagnostics.get("campaign_sha256") not in (None, binding(study / "campaign.json")["sha256"]):
        raise ValueError("diagnostics belong to another campaign")
    timing = load(state / "extraction-timing.json", {})
    freshness = load(state / "upstream-freshness.json", {})
    validation = public_paths(load(state / "final-validation.json", {}), state, project)
    groups = campaign.get("analysis_groups", {})
    subgroup = {}
    for name, prs in groups.items():
        selected = [r for r in scores.get("samples", []) if r["pr"] in prs]
        subgroup[name] = aggregate(selected, prs)
        subgroup[name]["review_completion"]["expected"] = len(prs) * 6
        subgroup[name]["scoring_completion"]["expected"] = len(prs) * 6
        subgroup[name]["operational"] = subgroup_operational(collection.get("results", []), selected, prs)
        subgroup[name]["paired_quality"] = paired_quality(subgroup[name]["per_pr"])
    mapped = {f: {s: mapping["counts"][f].get(s, 0) for s in ("supported", "conflict", "unknown")}
              for f in FACETS}
    mapping_total = {s: sum(r[s] for r in mapped.values()) for s in ("supported", "conflict", "unknown")}
    completed = collection.get("completed_results", 0)
    scored = scores.get("scoring_completion", {}).get("scored_review_samples", 0)
    refs = {arm: inventory[label]["production_references"] for arm, label in (("A", "original"), ("B", "current"))}
    inputs = {}
    for name, path in {
        "inventory": state / "mapping/inventory.json", "author_mapping": state / "mapping/author-mapping.json",
        "campaign": study / "campaign.json", "collection": study / "collection.json",
        "truth": study / "private-codex/truth-manifest.json", "scores": study / "private-codex/results.json",
        "extraction_timing": state / "extraction-timing.json", "freshness": state / "upstream-freshness.json",
        "validation": state / "final-validation.json", "knowledge_acceptance": project / "eval/knowledge-depth/jiuwenswarm-repair63-final-20261002.json",
        "runtime_identity": study / "identity.json", "codex_runtime": study / "private-codex/runtime-snapshot.json",
        "codex_score_runtime": study / "private-codex/score-runtime-snapshot.json",
        "codex_preflight": study / "private-codex/preflight.json", "reviews_manifest": study / "reviews-manifest.json",
    }.items():
        if path.exists(): inputs[name] = binding(path)
    terminal = completed == 72 and len(scores.get("samples", [])) == 72 and truth.get("frozen") and \
               all(s["status"] in ("complete", "failed") for s in scores.get("samples", []))
    value = {"schema": "jiuwenswarm-original-vs-current-report-v1",
             "generated_at_cn": datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
             "status": ("completed" if collection.get("valid_reviews") == scored == 72 else "completed_with_failures") if terminal else "incomplete",
             "source_pin": PIN, "baseline_knowledge_commit": inventory["knowledge_commit"],
             "original": {"documents": inventory["original"]["documents"], "associated_features": inventory["association_count"],
                          "association_distinct_documents": inventory["association_distinct_documents"],
                          "mapped_facets": mapping_total, "by_facet": mapped, "source_consistency": mapping["source_consistency"],
                          "explicit_production_references": len(refs["A"])},
             "current": {"recognized": final["recognized_facets"], "strict": final["strict_recognized_facets"],
                         "lightweight": final["lightweight_recognized_facets"], "unknown": final["unknown_facets"],
                         "facet_counts": final["facet_counts"], "structural_files": 2043, "production_files": 2199,
                         "depth_witness_files": 205, "explicit_production_references": len(refs["B"])},
             "experiment": {"scheduled": 72, "terminal_results": completed, "valid_reviews": collection.get("valid_reviews", 0),
                            "scored_reviews": scored, "by_arm": collection.get("by_arm", {}),
                            "groups": groups, "subgroups": subgroup, "overall_macro": scores.get("macro", {}), "knowledge_exposure": exposure,
                            "diagnostics": diagnostics,
                            "per_pr": scores.get("per_pr", []), "truth_frozen": truth.get("frozen", False),
                            "truth_complete_prs": sum(r.get("status") == "complete" for r in truth.get("cases", [])),
                            "truth_unknown_prs": [r["pr"] for r in truth.get("cases", []) if r.get("status") != "complete"],
                            "cases": [{"pr": c["number"], "target": c["target"], "base": c["base"], "head": c["head"],
                                       "changed_files": len(c["changed_files"]), "older_fork": c["target_base_diverged"]} for c in campaign["cases"]]},
             "freshness": freshness, "validation": validation, "actual_invoice_cost": None,
             "inputs": inputs, "raw_trace_archive": state.name,
             "snapshot_sha256": {a: inventory["snapshots"][a]["sha256"] for a in ("A", "B")},
             "limitations": ["Author mapping is bounded evidence coverage, not exhaustive absence or current-KB recognition.",
                             "Explicit source references, structural cards and depth witness files have different meanings.",
                             "Eight direct-baseline PRs form the primary comparison; four older forks are exploratory.",
                             "Independent automated Codex truth is a partial confirmed-issue set, not a maintainer gold standard.",
                             "Unknown findings are not false positives; failures remain in completion denominators.",
                             "Actual billing is unknown unless provider-reported."]}
    primary = subgroup.get("primary_prospective", {})
    conclusion = "正式评审或独立评分尚未全部完成，暂不发布准确率和加速结论。"
    if terminal:
        metrics = []
        for field, label in (("defect_precision", "缺陷评论精确率"), ("confirmed_recall", "已确认问题召回率")):
            metric = primary.get("paired_quality", {}).get(field, {})
            a, b = metric.get("A"), metric.get("B")
            delta = f"，B−A 为 {100*(b-a):+.2f} 个百分点" if a is not None and b is not None else "，分母不足时不可计算"
            metrics.append(f"{label} A {pct(a)}、B {pct(b)}{delta}（共同适用 {metric.get('applicable_prs',0)} PR）")
        latencies = [primary.get("operational", {}).get(a, {}).get("timings_valid", {}).get("native_seconds", {}).get("p50") for a in ("A", "B")]
        change = f"（B−A {(latencies[1]/latencies[0]-1)*100:+.2f}%）" if all(v is not None and v > 0 for v in latencies) else ""
        conclusion = "主样本实测：" + "；".join(metrics) + f"。有效评审的原生耗时 P50 为 A {num(latencies[0])} 秒、B {num(latencies[1])} 秒{change}；此处为观察差，包含限流和工具等待。结果来自 8 个所选 PR，不能推广为全项目准确率。"
    value["conclusion_cn"] = conclusion
    lines = ["# JiuwenSwarm 原项目文档与当前知识库对比报告", "",
             f"生成时间：{value['generated_at_cn']}（北京时间）。源码知识基线：`{PIN}`；当前知识内容为 PR #290 已合并版本。", "",
             "当前知识库在功能组织、源码关联和可审计性方面更完整；原资料保留了作者的设计意图、被拒绝方案、完整使用手册和维护风险，两者都能为评审提供有价值的上下文。",
             f"当前认可 **552/553（99.82%）**；原作者正文在本次有界映射中提供 **{mapping_total['supported']}/553（{100*mapping_total['supported']/553:.2f}%）** 项说明。两项统计的依据不同，不能将其差额直接解释为新增正确知识。", "",
             f"实测状态：**{value['status']}**；72 个计划评审中已有 {completed} 个终态结果、{collection.get('valid_reviews',0)} 个有效评审、{scored} 个完成独立评分。", "",
             conclusion, "",
             "## 内容与覆盖", "",
             "| 指标 | 原项目作者资料 | 当前知识库 | 统计含义 |", "| --- | ---: | ---: | --- |",
             f"| Markdown 库存 | {inventory['original']['documents']} | {inventory['current']['documents']} | 文档数不是知识数；包含不同语言及不同粒度 |",
             "| 功能与原文档关联 | 79/79，55 篇不同文档 | 沿用这些原文档并结合源码 | 文件存在或目录关联，不证明正文充分说明 |",
             f"| 七维正文映射/认可 | 支持 {mapping_total['supported']}、冲突 {mapping_total['conflict']}、未知 {mapping_total['unknown']} | 认可 552、未知 1 | 原正文映射与当前认可流程分别展示 |",
             f"| 解释性正文明确引用生产文件 | {len(refs['A'])}/2199（{100*len(refs['A'])/2199:.2f}%） | {len(refs['B'])}/2199（{100*len(refs['B'])/2199:.2f}%） | 相同保守解析规则的引用下界；排除扫描清单与机器卡片 |",
             "| 生产文件结构覆盖 | 无同口径审计，无法比较 | 2043/2199（92.91%） | 结构卡片覆盖，不是整个文件的行为验证 |",
             "| 深度知识的生产文件证据 | 无同口径审计，无法比较 | 205 个文件 | 已使用的源码证明文件，不是结构覆盖分母 |", "",
             "| 维度 | 原正文支持 | 原正文冲突 | 原正文未知 | 当前认可 |", "| --- | ---: | ---: | ---: | ---: |"]
    for facet, label in FACETS.items():
        row = mapped[facet]
        lines.append(f"| {label} | {row['supported']}/79 | {row['conflict']} | {row['unknown']} | {final['facet_counts'][facet]['recognized']}/79 |")
    lines += ["", "当前 552 项包括严格认可 207 项和轻量认可 345 项，均为 supported，verified_absent 为零。唯一未知是 `im-feishu / 设计取舍`，不能据此声称飞书功能或测试不存在。",
              "79 个功能均有深度说明，78 个功能七维齐全。一个维度认可表示至少有一段可用解释；代表流程或单个 API 契约不能证明该功能的所有分支、接口或文件均已解释。",
              "原文档映射每个功能一次独立 Codex 调用；只计入实际解释该功能的原作者行段。候选段落有预算，未知包含未检索到、内容不足、引用不合法和读取失败，不能解释为项目没有相关知识。",
              "每功能映射最多提供 24,000 字符作者正文和 16,000 字符源码候选，仅 15/79 个功能的候选正文全部送入，因此原资料的解释数是有界审计结果。初次整体格式校验只有 19/79 通过；随后对既有 79 份答复确定性重放，允许原文空行连接，不增加模型调用或声明。仍不合法的 7 个维度保持未知。",
              "这次原资料映射的完整 CLI 流未全部保存；精确输入、原始答复、哈希及已报告用量保留。后续 PR A/B 则保存完整原生流和工具记录，两者不混算。",
              f"原正文与固定实现的一致性另计：{mapping['source_consistency'].get('supported',0)} 项得到所提供源码支持，{mapping['source_consistency'].get('conflict',0)} 项冲突，其余 {mapping['source_consistency'].get('unknown',0)} 项无法确认。无法确认不等于过时。", "",
              "## 双方内容的价值与时效性", "",
              f"原资料的 [AgentServer 预热会话 ADR]({source_link('.doc_project_maintainer/decisions/ADR-0001-agentserver-owned-prewarmed-sessions.md')}) 记录决策、后果和被拒绝方案，适合判断 PR 是否违背作者意图。原维护资料还集中保留 AgentServer 风险、审计状态与健康维度；这些内容不能被一个七维计数替代。",
              "当前知识库按 owner 和功能整理代表流程、API 义务、配置默认值、失败分支及源码引用，减少评审时重新寻找入口的工作。轻量认可允许明确标注的推断；这与原作者明确陈述的设计理由分别呈现。",
              "", "| 内容 | 原作者资料的具体价值 | 当前知识的具体价值及评审用途 |", "| --- | --- | --- |",
              f"| 架构 | [Runtime Session 参考链]({source_link('.doc_project_maintainer/project/flows/runtime-session-reference-chain.md')}) 解释迁移边界 | 按 owner 组织入口与下游，附固定源码和认可记录，便于回查实现 |",
              f"| 流程 | [Skill 自演进指南]({source_link('docs/zh/Skill自演进.md',92)}) 解释用户发起与审批过程 | [Skill 深读]({knowledge_link('knowledge/repos/jiuwenswarm/components/agent-server-runtime/feature-depth-skill-evolution.md')}) 补充 no_evolution_no_records 分支的返回映射 |",
              f"| API | 同一指南给出 `/evolve <skill_name> [user_intent]` 及提案义务 | [Cron 深读]({knowledge_link('knowledge/repos/jiuwenswarm/components/cron-scheduling/feature-depth-cron.md')}) 明确 update_job 空 id 与任务不存在时的异常契约 |",
              f"| 配置 | [配置信息]({source_link('docs/zh/配置信息.md')}) 提供用户配置操作 | Cron 深读说明默认 file、仅显式 etcd 生效及空 endpoints 不回落 file，帮助识别错误默认假设 |",
              f"| 依赖 | [A2A 指南]({source_link('docs/zh/A2A.md',24)}) 解释入站链路、SDK 和服务边界 | Cron 深读定位 mod_revision 条件写与 EtcdError 包装，帮助检查并发更新 |",
              "| 失败行为 | 使用与维护文档保留故障提示及恢复指南 | Cron 的 CAS 单次重试、Skill 超时读取失败的 fallback，都有具体实现引用 |",
              "| 设计取舍 | 预热会话 ADR 有作者明确意图和被否决方案 | Cron 默认后端与 Skill watcher 代价明确标注为设计推断，不代替作者意图 |",
              "| 验证入口 | 测试、SDK 和客户端资料有完整操作指南 | Cron 表达式与文件锁断言、Skill helper 断言定位精确，并明确不是本次测试执行结果 |", "",
              f"原资料也存在局部不同步：较早的 [架构说明]({source_link('.doc_project_maintainer/project/architecture.md')}) 与较新的 [Runtime 会话参考链]({source_link('.doc_project_maintainer/project/flows/runtime-session-reference-chain.md')}) 对 AgentServer 迁移状态的表述不同。文档日期、源码版本和实际声明需逐项检查，不能用一次最后提交时间判定全部内容新鲜。",
              "原维护资料标为 partial；历史 ledger 的符号审计分母和统计日期与本报告不同。历史的 trusted/expired 数字不作为当前源码上的正确率。", "",
              "| 时效性证据 | 原作者资料 | 当前知识库 |", "| --- | --- | --- |",
              "| 文档/记录日期 | README 为 2026-08-01，manifest 为 2026-09-08，部分流程为 2026-09-11；不代表所有正文同日复核 | 本轮深度补齐于 2026-10-02，报告于 2026-10-03 复核 |",
              "| 声明版本 | 旧扫描记录仍声明 7 月版本 10afedf2，部分正文无可确认实现版本 | 生效深度区块绑定完整 f0a69728 SHA、引用哈希及严格/轻量认可记录 |",
              "| 与源码一致性 | 有界核查 89 支持、12 冲突、452 未知 | 552 项通过已有固定版本审计；未来 PR 仍须重新验证受影响声明 |", "",
              "本报告固定知识在 f0a69728；它不能自动保证对后来 PR 头部仍然有效。评审必须回到冻结 PR 源码验证。"]
    lines += [f"交付核查的 develop 为 `{freshness.get('head_sha','未知')}`，核查时间 {freshness.get('checked_at_cn','未知')}；相对知识基线的新增提交数为 {freshness.get('ahead_by','未知')}，变更生产文件数为 {freshness.get('changed_production_files','未知')}。", "",
              "验证维度有内容不等于运行时测试覆盖：当前分类包括 27 个运行时测试入口、1 个源码文本断言、14 个辅助函数测试、9 个文档手工验证入口和 28 个历史未分类区块。本轮 PR 评审是只读实验，没有执行 JiuwenSwarm 上游测试，也没有把作者历史测试通过的声明当成本轮通过。", "",
              "## GLM‑5.3 PR 评审实测", "",
              "A 组只检索原作者资料；B 组只检索当前 JiuwenSwarm 知识库。两组使用相同冻结源码、提示词、检索算法、两页初始检索和 6000 字符累计知识预算。后续搜索和读取扣除余量。并发 13，共享排期；每评审最多 60 次源码调用，每次结果最多 24,000 字符，原生超时 30 分钟。",
              "12 PR × 两组 × 三重复，共 72 个评审。GitHub 的目标分支 SHA 与 PR 实际 diff 基线分开记录；diff 使用真实 merge-base→head，不将目标分支的历史变化当作 PR 修改。",
              "8 个直接基于 f0a69728 的 PR 为主样本；#7639、#7654、#7655、#7656 从较旧提交分叉，且头部提交早于知识基线，只作探索性对照。其知识可能描述较新的目标分支实现，不能混同为无时间泄漏的前瞻准确率。",
              "独立 Codex 在正式 GLM 评审前冻结确认问题；随后对匿名、随机顺序的评论核验。只有新增或加重且有源码证据的缺陷计 TP；证实不成立计 FP；证据不足计 unknown。风格、文档和其他建议另计有效性。召回仅指对自动独立审计已确认问题的召回，无法覆盖全部真实缺陷。", ""]
    lines += [f"源码基准审计成功 {value['experiment']['truth_complete_prs']}/12，未知 PR 为 {value['experiment']['truth_unknown_prs'] or '无'}。#7656 的原答复缺少现有源码的基线证据，未重抽样；它的确认问题数和召回率保持未知。主样本只在 #7647、#7649 确认各一个问题，主样本召回率最多有 2 个适用 PR，应谨慎解读。", ""]
    for group_name, label in (("primary_prospective", "主样本：8 PR / 48 次"), ("older_fork_exploratory", "旧分叉探索：4 PR / 24 次")):
        result = subgroup.get(group_name, {})
        lines += [f"### {label}", "", "| 指标（先每 PR 三重复均值，再按 PR 平均） | A 原资料 | B 当前知识 |", "| --- | ---: | ---: |"]
        for field, title in (("defect_precision", "缺陷评论精确率"), ("confirmed_recall", "已确认问题召回率"), ("advice_validity", "非缺陷建议有效率")):
            cells = []
            for arm in ("A", "B"):
                metric = result.get("macro", {}).get(arm, {}).get(field, {})
                cells.append(f"{pct(metric.get('mean'))}（适用 {metric.get('applicable_prs',0)} PR）")
            lines.append(f"| {title} | {cells[0]} | {cells[1]} |")
        operational = result.get("operational", {})
        lines.append(f"| 缺陷判断中的未知比例 | {pct(operational.get('A',{}).get('unknown_share'))} | {pct(operational.get('B',{}).get('unknown_share'))} |")
        for field, title in (("TP", "有效缺陷评论"), ("FP", "误报"), ("unknown", "未知缺陷判断"),
                             ("nondefect_advice", "非缺陷建议"), ("advice_valid_actionable", "有效且可操作的建议"),
                             ("advice_unknown", "有效性未知的建议"), ("novel_valid_defects", "新发现有效缺陷（不回填召回基准）")):
            values = [operational.get(a, {}).get("counts", {}).get(field, 0) for a in ("A", "B")]
            values = ["未知" if v is None else v for v in values]
            lines.append(f"| {title} | {values[0]} | {values[1]} |")
        for field, title in (("native_seconds", "原生耗时"), ("queue_seconds", "worker 内排期等待"), ("end_to_end_seconds", "端到端耗时")):
            cells = []
            for arm in ("A", "B"):
                row = operational.get(arm, {}).get("timings_valid", {}).get(field, {})
                cells.append(f"P50 {num(row.get('p50'))} 秒 / P90 {num(row.get('p90_linear'))} 秒，n={row.get('n',0)}")
            lines.append(f"| {title} | {cells[0]} | {cells[1]} |")
        lines.append("| 有效评审 / 计划评审 | " + " | ".join(f"{operational.get(a,{}).get('valid',0)}/{operational.get(a,{}).get('expected',0)}" for a in ('A','B')) + " |")
        lines += ["", "两组各自适用 PR 可能不同，以上条件宏平均不直接作因果差异。共同适用的 PR 对照如下：", "",
                  "| 共同适用 PR 的指标 | A | B | B−A | PR 数 |", "| --- | ---: | ---: | ---: | ---: |"]
        for field, title in (("defect_precision", "缺陷评论精确率"), ("confirmed_recall", "已确认问题召回率"), ("advice_validity", "建议有效率")):
            metric = result.get("paired_quality", {}).get(field, {})
            delta = metric.get("B_minus_A")
            lines.append(f"| {title} | {pct(metric.get('A'))} | {pct(metric.get('B'))} | {100*delta:+.2f} 个百分点 | {metric.get('applicable_prs',0)} |" if delta is not None else
                         f"| {title} | 不可计算 | 不可计算 | 不可计算 | {metric.get('applicable_prs',0)} |")
        lines.append("")
    lines += ["评论数按每次评审的根因去重，三次重复仍是三个观测，不称作不同缺陷总数。未知比例为 unknown/(TP+FP+unknown)，非缺陷建议不进入该分母。精确率排除未知，须结合未知比例和完成率阅读。", ""]
    lines += ["### 速度、完成率与实际注入", "", "| 指标 | A 原资料 | B 当前知识 |", "| --- | ---: | ---: |"]
    for kind, title in (("native_seconds", "原生评审耗时"), ("queue_seconds", "worker 内排期等待"), ("retrieval_seconds", "初始知识检索耗时"), ("end_to_end_seconds", "每评审端到端耗时")):
        cells = []
        for arm in ("A", "B"):
            row = collection.get("by_arm", {}).get(arm, {}).get("timings_valid", {}).get(kind, {})
            cells.append(f"P50 {num(row.get('p50'))} 秒 / P90 {num(row.get('p90_linear'))} 秒，n={row.get('n',0)}")
        lines.append(f"| {title} | {cells[0]} | {cells[1]} |")
    for field, title in (("valid", "有效评审数 / 36"), ("failed", "终态失败数"), ("actual_attempts", "实际原生调用次数（含传输重试）")):
        lines.append(f"| {title} | {collection.get('by_arm',{}).get('A',{}).get(field,0)} | {collection.get('by_arm',{}).get('B',{}).get(field,0)} |")
    for field, label in (("input_tokens", "已报告输入 token 小计"), ("output_tokens", "已报告输出 token 小计"), ("cache_read_input_tokens", "已报告 cache 读取 token 小计")):
        cells = []
        for arm in ("A", "B"):
            usage = collection.get("by_arm", {}).get(arm, {}).get("reported_usage", {}).get(field, {})
            cells.append(f"{usage.get('reported_subtotal') if usage.get('reported_subtotal') is not None else '未知'}（未报告 {usage.get('missing_calls',0)} 次）")
        lines.append(f"| {label} | {cells[0]} | {cells[1]} |")
    chars = [collection.get('by_arm',{}).get(a,{}).get('initial_knowledge_chars',{}).get('mean') for a in ('A','B')]
    lines += [f"| 初始实际注入字符均值 | {num(chars[0])} | {num(chars[1])} |"]
    for field, label in (("knowledge_chars_consumed", "累计实际知识字符均值"), ("followup_knowledge_chars", "后续补读/搜索字符均值")):
        numbers = [exposure[a][field]["mean"] for a in ("A", "B")]
        lines.append(f"| {label} | {num(numbers[0])} | {num(numbers[1])} |")
    for field, label in (("affected_reviews_observed", "观测到 429 的评审数"), ("provider_429_notifications_observed", "去重后的 429 通知"),
                         ("internal_retry_schedules_observed", "原生 CLI 内部退避记录")):
        numbers = [diagnostics.get("by_arm",{}).get(a,{}).get("rate_limits",{}).get(field) for a in ("A","B")]
        lines.append(f"| {label} | {numbers[0] if numbers[0] is not None else '未知'} | {numbers[1] if numbers[1] is not None else '未知'} |")
    b = exposure["B"]
    lines += ["",
              f"当前知识组初始每次完整注入的维度均值为 {num(b['initial_intact_facets']['mean'])}，片段维度均值为 {num(b['initial_partial_facets']['mean'])}；所选页面可用维度均值为 {num(b['available_facets_on_selected_pages']['mean'])}。只按实际正文匹配计算完整注入，库存 552 项并非全部进入模型。原作者页没有 kb:depth 标记，不能把其标记数为零解释为没有知识。",
              "速度表列出有效评审；失败、超时和额外尝试保留在完成率及配套 JSON 中，不删除较慢或失败样本。排期等待从 worker 开始计算，不包含尚未获得 worker 的排队。P90 使用线性插值。知识库存、初始实际注入及后续工具读取分别记录。",
              "6000 字符按知识正文和后续搜索片段累计；导航元数据、PR diff、源码工具输出及协议提示词另记输入 token。原生耗时是 CLI 执行时间，包含工具读写和服务内部退避，不等同于纯推理时间。",
              "订阅服务的 HTTP429 可触发 Zcode 内部请求退避，观测 maxAttempts 为 11；这是原生请求重试，与最多一次外层 CLI 传输重试分开。共享排期初始间隔 15 秒、限流冷却 90 秒，可放缓到 60 秒。请求的退避延迟不是测得的等待时间，排队延迟不能归因于检索质量。",
              f"实际 CLI 并发峰值为 {diagnostics.get('native_timing',{}).get('native_active_peak_completed_intervals','未知')}，完整区间数为 {diagnostics.get('native_timing',{}).get('completed_native_intervals','未知')}；缺失区间时仅为下界。全批次从首次原生启动到最后退出的时间为 {num(diagnostics.get('native_timing',{}).get('batch_native_span_seconds'))} 秒，不含准备与独立评分。",
              "冻结协议的失败归因另列在 JSON 中：目录尾斜杠兼容问题、未读完整输入、输出格式、真实边界拒绝和无法判断分别记录。`source_grep(path=\"tests/\")` 曾被误判为违规，该次属于工具格式失败，不计缺陷误报；未重新抽样或事后改写原生结果。",
              "收益判断以成对 PR 结果为准，不预设当前知识组一定更准或更快。只取短样本或只比较提取速度不能支持 PR 评审加速结论。", "",
              "### 逐 PR 结果", "", "| PR | 类型 | 确认缺陷数 | A 精确率 / 确认召回 | B 精确率 / 确认召回 | A/B 已评分重复 |", "| --- | --- | ---: | --- | --- | --- |"]
    per_pr = {r['pr']: r for r in scores.get('per_pr',[])}
    truth_rows = {r['pr']: r for r in truth.get('cases',[])}
    for case in campaign['cases']:
        row = per_pr.get(case['number'], {}).get('arms', {})
        a,b = row.get('A',{}),row.get('B',{})
        confirmed = truth_rows.get(case['number'],{}).get('confirmed_defects')
        lines.append(f"| [#{case['number']}]({case['url']}) | {'旧分叉探索' if case['target_base_diverged'] else '主样本'} | {confirmed if confirmed is not None else '未知'} | {pct(a.get('defect_precision'))} / {pct(a.get('confirmed_recall'))} | {pct(b.get('defect_precision'))} / {pct(b.get('confirmed_recall'))} | {a.get('scored_repeats',0)}/{b.get('scored_repeats',0)} |")
    lines += ["", "没有确认缺陷时，召回为不可计算；不将其视为 100%，也不据此认定 PR 无缺陷。新确认发现单列，不回填本轮基准。", "",
              "## 提取耗时、验收与复查", "",
              f"此前补齐 63 项的知识提取记录含 {timing.get('generator_calls','未知')} 次 GLM 调用、{timing.get('judge_calls','未知')} 次 Codex 调用。GLM 原生提取 P50 为 {num(timing.get('glm_native_seconds',{}).get('p50'))} 秒、P90 为 {num(timing.get('glm_native_seconds',{}).get('p90'))} 秒；这些是知识提取耗时，不是上面的 PR 评审速度。",
              "实际账单金额未知。订阅验证通过不代表没有费用；缺失 token、cache 或费用字段不按零计算。",
              "首次附件式 Codex 审计因主机 max_user_namespaces=0 无法读取输入，12 次基础设施失败均完整保存，未计作零缺陷。正式版本改为封闭只读 MCP 输入，保留订阅 Codex 和原沙箱设置；旧运行及修复前运行版本保留用于复查。",
              f"完整输入、流式输出、工具事件、实际注入、配置、模型身份、失败及评分记录存于 Git 外归档 `{state.name}/`。下表路径相对于归档根；机器绝对路径只保留在原始记录中。Git 中仅保存紧凑结果、报告和运行工具，原始大文件没有重复提交。", "",
              "| 复查输入 | 逻辑路径 | SHA256 |", "| --- | --- | --- |"]
    for name, info in inputs.items(): lines.append(f"| {name} | `{public_paths(info['path'],state,project)}` | `{info['sha256']}` |")
    for arm, digest in value["snapshot_sha256"].items(): lines.append(f"| {arm} 组文档快照 | 见 inventory | `{digest}` |")
    checks = validation.get("full_pytest", {})
    lines += ["", f"本地验证：{validation.get('status','未知')}；全量 pytest {checks.get('passed','未知')} 通过、{checks.get('skipped','未知')} 跳过；知识目录 {validation.get('knowledge_tree',{}).get('errors','未知')} 错误、{validation.get('knowledge_tree',{}).get('warnings','未知')} 提醒。CLI、doctor JSON、文档链接、引用、SPEC 和独立安装包检查的日志哈希保留在配套 JSON。GitHub CI：{validation.get('github_ci','未知')}。", "",
              "当前结论只适用于所选 PR、固定 GLM 配置和相同检索预算。扩大样本、增加人工确认基准、改善未注入维度的检索，是后续评估方向；不能把知识认可率当作缺陷识别准确率。", ""]
    output.mkdir(parents=True, exist_ok=True)
    value = public_paths(value, state, project)
    basename = "jiuwenswarm-original-docs-comparison-cn-20261003"
    (output / (basename + ".json")).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    (output / (basename + ".md")).write_text("\n".join(lines), encoding="utf-8")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--study", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--refresh-upstream", action="store_true", help="observe develop without moving frozen sources")
    args = parser.parse_args()
    if args.refresh_upstream: refresh_upstream(args.state)
    result = build(args.state, args.output_dir, args.study)
    print(json.dumps({"status": result["status"], "terminal": result["experiment"]["terminal_results"],
                      "scored": result["experiment"]["scored_reviews"]}))
