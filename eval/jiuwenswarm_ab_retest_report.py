"""Read-only, compact Chinese comparison of the original and repaired A/B runs."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from eval.jiuwenswarm_ab_judge import aggregate, bound_reviews, review_metrics
from eval.jiuwenswarm_ab_report import (binding, distribution, knowledge_exposure, load,
    matching_diagnostics, num, paired_quality, paired_speed, pct, public_paths,
    subgroup_operational, validate_evaluation)

PRS = (7639, 7641, 7642, 7645, 7647, 7649, 7650, 7651, 7654, 7655, 7656, 7675)
PRIMARY = (7641, 7642, 7645, 7647, 7649, 7650, 7651, 7675)
EXPLORATORY = (7639, 7654, 7655, 7656)
NAME = "jiuwenswarm-ab-retest-cn-20261003"


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _check_binding(value):
    if not isinstance(value, dict) or binding(value["path"])["sha256"] != value.get("sha256"):
        raise ValueError("provenance artifact bytes changed")


def _verify_files(root, manifest, cache):
    root = Path(root).resolve()
    for relative, expected in manifest.items():
        parts = relative.replace("\\", "/").split("/")
        if relative.startswith("/") or any(p in ("", ".", "..", ".git") for p in parts):
            raise ValueError("frozen input manifest path escapes scope")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("frozen input is unreadable or escapes scope")
        key = str(path), expected
        if key not in cache:
            if binding(path)["sha256"] != expected:
                raise ValueError("frozen source/document bytes changed")
            cache.add(key)


def actual_source_calls(row, limit=60):
    """Count requests in bound bridge events, including denied/failed requests."""
    total = early = 0
    for attempt in row.get("attempts", []):
        root = Path(attempt["attempt_root"])
        state_path, events_path = root / "tool-state.json", root / "bridge-events.jsonl"
        artifacts = attempt.get("artifacts", {})
        if not state_path.is_file() or binding(state_path)["sha256"] != artifacts.get("tool-state.json"):
            raise ValueError("source call audit state bytes changed or missing")
        state = load(state_path)
        if not events_path.exists() and state.get("events") == 0:
            continue
        if not events_path.is_file() or binding(events_path)["sha256"] != artifacts.get("bridge-events.jsonl"):
            raise ValueError("source call audit event bytes changed")
        events = [json.loads(line) for line in events_path.read_text().splitlines()]
        if len(events) != state.get("events"):
            raise ValueError("source call audit event/state counts differ")
        requests = [e for e in events if e.get("tool") in {"source_read", "source_list", "source_grep", "file_at_base", "calc"}]
        total += len(requests)
        early += sum(str(e.get("error", "")).startswith("prompt_not_complete:") for e in requests)
    if total > limit:
        raise ValueError("actual source/compute call requests exceed frozen budget")
    return {"pr": row["number"], "arm": row["arm"], "repeat": row["repetition"] - 1,
            "actual_requests": total, "early_prompt_gate_denied": early,
            "stored_counter": row.get("source_calls_cumulative"), "budget": limit}


def read_study(study, cache=None):
    """Check persisted receipts; never invoke a model, collector or source command."""
    study = Path(study).resolve()
    campaign = load(study / "campaign.json")
    identity = load(study / "identity.json", {})
    collection = load(study / "collection.json", {})
    truth = load(study / "private-codex/truth-manifest.json", {})
    scores = load(study / "private-codex/results.json", {})
    if not campaign or not identity or not truth or truth.get("frozen") is not True:
        raise ValueError("campaign, frozen runtime and frozen truth are required")
    validate_evaluation(study, campaign, collection, truth, scores)
    if Path(campaign["run_root"]).resolve() != study:
        raise ValueError("campaign run_root differs from requested study")
    if sorted(c["number"] for c in campaign["cases"]) != list(PRS):
        raise ValueError("the twelve fixed PRs must remain unchanged")
    if campaign.get("analysis_groups") != {"primary_prospective": list(PRIMARY), "older_fork_exploratory": list(EXPLORATORY)}:
        raise ValueError("analysis groups changed")
    cache = cache if cache is not None else set()
    runtime_cases = {c["number"]: c for c in identity["cases"]}
    if set(runtime_cases) != set(PRS):
        raise ValueError("runtime source inventory differs")
    for case in campaign["cases"]:
        runtime = runtime_cases[case["number"]]
        if any(runtime.get(k) != case.get(k) for k in ("target", "base", "head", "context_sha256", "diff_sha256")):
            raise ValueError("runtime PR inputs differ from campaign")
        _verify_files(runtime["source_root"], runtime["sources"], cache)
    for arm in "AB":
        docs = identity["arms"][arm]
        if Path(docs["doc_root"]).resolve() != Path(campaign["arms"][arm]["doc_root"]).resolve():
            raise ValueError("runtime document root differs")
        _verify_files(docs["doc_root"], docs["documents"], cache)
        actual = {p.relative_to(Path(docs["doc_root"])).as_posix() for p in Path(docs["doc_root"]).rglob("*.md")}
        if actual != set(docs["documents"]):
            raise ValueError("document snapshot inventory changed")
    if identity["native"].get("model") != "GLM-5.3" or "coding-plan" not in identity["native"].get("provider_id", ""):
        raise ValueError("retained model must be subscribed GLM-5.3")
    rows = [r for r in collection.get("results", []) if not r.get("preflight")]
    call_audits = []
    for row in rows:
        path = study / "items" / row["item"] / "result.json"
        if not path.resolve().is_relative_to(study / "items") or load(path) != row:
            raise ValueError("collection differs from persisted native result")
        if row["status"] == "valid" and row.get("served_model") != "GLM-5.3":
            raise ValueError("valid trial has mismatched served model")
        call_audits.append(actual_source_calls(row, campaign.get("budget", {}).get("source_calls", 60)))
    if len(rows) == 72:
        prepared, _ = bound_reviews(campaign, binding(study / "campaign.json")["sha256"], load(study / "reviews-manifest.json", {}))
        native = {(r["number"], r["arm"], r["repetition"] - 1): r for r in rows}
        for row in prepared:
            if row["native_status"] != native[row["pr"], row["arm"], row["repeat"]]["status"]:
                raise ValueError("collection and manifest statuses differ")
    truths = {r["pr"]: load(r["path"]) for r in truth["cases"]}
    return {"study": study, "campaign": campaign, "identity": identity, "collection": collection,
            "truth": truth, "truth_records": truths, "scores": scores, "rows": rows, "source_call_audits": call_audits}


def verify_comparable(previous, current, provenance):
    """Only campaign/harness metadata may change; source, docs and truth stay fixed."""
    for key in ("budget", "native", "baseline_source_sha", "knowledge_checkout_sha", "analysis_groups"):
        if previous["campaign"].get(key) != current["campaign"].get(key):
            raise ValueError(f"retest changed comparable configuration: {key}")
    for pr in PRS:
        for source in ("campaign", "identity"):
            left = next(c for c in previous[source]["cases"] if c["number"] == pr)
            right = next(c for c in current[source]["cases"] if c["number"] == pr)
            fields = ("target", "base", "head", "context_sha256", "diff_sha256") + (("sources",) if source == "identity" else ())
            if any(left.get(k) != right.get(k) for k in fields):
                raise ValueError("retest PR inputs changed")
        before, after = previous["truth_records"][pr], current["truth_records"][pr]
        clean = lambda r: {k: v for k, v in r.items() if k not in ("campaign_sha256", "retest_origin")}
        if clean(before) != clean(after):
            raise ValueError("retest must preserve every frozen truth field, including unknown")
    for arm in "AB":
        if previous["identity"]["arms"][arm]["documents"] != current["identity"]["arms"][arm]["documents"]:
            raise ValueError("retest document content inventory changed")
    if provenance.get("schema") != "jiuwenswarm-protocol-retest-v1" or provenance.get("original_archive_mutated") is not False:
        raise ValueError("retest provenance is required")
    for value in [provenance["campaign"], *provenance["origin"].values(), provenance["reference_report"],
                  provenance["protocol"]["retest_harness"], provenance["truth_manifest"]]:
        _check_binding(value)
    targets = [(provenance["campaign"], current["study"] / "campaign.json"),
               (provenance["origin"]["campaign"], previous["study"] / "campaign.json"),
               (provenance["origin"]["runtime_identity"], previous["study"] / "identity.json"),
               (provenance["origin"]["truth"], previous["study"] / "private-codex/truth-manifest.json"),
               (provenance["truth_manifest"], current["study"] / "private-codex/truth-manifest.json")]
    if any(binding(path)["sha256"] != value["sha256"] for value, path in targets):
        raise ValueError("retest provenance belongs to different inputs")
    if provenance["protocol"]["previous_harness_sha256"] != previous["identity"]["harness_sha256"] or \
       provenance["protocol"]["retest_harness"]["sha256"] != current["identity"]["harness_sha256"]:
        raise ValueError("retest harness identity differs from provenance")
    records = provenance.get("truth_records", [])
    if len(records) != 12 or {r["pr"] for r in records} != set(PRS):
        raise ValueError("retest provenance must bind twelve truth records")
    old_paths = {r["pr"]: r for r in previous["truth"]["cases"]}
    new_paths = {r["pr"]: r for r in current["truth"]["cases"]}
    for row in records:
        for name, expected in (("origin_record", old_paths[row["pr"]]), ("rebound_record", new_paths[row["pr"]])):
            _check_binding(row[name])
            if row[name]["sha256"] != expected["sha256"]:
                raise ValueError("retest truth provenance record differs")
        preserved = {k: v for k, v in previous["truth_records"][row["pr"]].items() if k != "campaign_sha256"}
        expected = hashlib.sha256(json.dumps(preserved, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        if row.get("preserved_payload_sha256") != expected or row.get("status") != preserved["status"]:
            raise ValueError("retest truth preserved payload digest differs")


def verify_scores(value):
    """Recompute public sample metrics from bound blind records, rather than counters."""
    samples = value["scores"].get("samples", [])
    native = {(r["number"], r["arm"], r["repetition"] - 1): r for r in value["rows"]}
    for sample in samples:
        key = sample["pr"], sample["arm"], sample["repeat"]
        valid = native[key]["status"] == "valid"
        if sample.get("review_status") != ("complete" if valid else "failed"):
            raise ValueError("score/native completion status differs")
        if not valid:
            if sample["status"] != "failed" or "metrics" in sample:
                raise ValueError("failed native trial cannot receive valid metrics")
            continue
        if sample["status"] != "complete":
            continue
        record = load(value["study"] / f"private-codex/scores/pr-{sample['pr']}.json", {})
        if record.get("status") != "complete" or record.get("truth_manifest_sha256") != binding(value["study"] / "private-codex/truth-manifest.json")["sha256"]:
            raise ValueError("sample lacks bound completed blind score")
        labels = [label for label, row in record.get("blind_mapping", {}).items() if (row["pr"], row["arm"], row["repeat"]) == key]
        if len(labels) != 1:
            raise ValueError("blind score slot is missing or duplicated")
        bound = record["blind_mapping"][labels[0]]
        result_path = value["study"] / "items" / native[key]["item"] / "result.json"
        if bound.get("run_result_sha256") != binding(result_path)["sha256"] or \
           bound.get("normalized_output_sha256") != native[key].get("normalized_output_sha256"):
            raise ValueError("blind score bound review changed")
        truth = value["truth_records"][sample["pr"]]
        issues = truth["data"]["issues"] if truth["status"] == "complete" else None
        expected = review_metrics(record["data"]["reviews"][labels[0]]["comments"], issues)
        if expected != sample.get("metrics"):
            raise ValueError("score metrics differ from blind classified comments")


def completion(value):
    samples = {(r["pr"], r["arm"], r["repeat"]): r for r in value["scores"].get("samples", [])}
    expected = {(pr, arm, rep) for pr in PRS for arm in "AB" for rep in range(3)}
    native = {(r["number"], r["arm"], r["repetition"] - 1): r for r in value["rows"]}
    done = len(value["rows"]) == len(value["scores"].get("samples", [])) == 72 and set(native) == set(samples) == expected and all(
        s["status"] == "complete" if native[k]["status"] == "valid" else s["status"] == "failed" for k, s in samples.items())
    return ("completed" if all(r["status"] == "valid" for r in native.values()) else "completed_with_failures") if done else "incomplete"


def summarize(value, diagnostics):
    samples, rows = value["scores"].get("samples", []), value["rows"]
    groups = {}
    for name, prs in (("all", PRS), ("primary_prospective", PRIMARY), ("older_fork_exploratory", EXPLORATORY)):
        selected = [r for r in samples if r["pr"] in prs]
        quality = aggregate(selected, prs)
        quality["review_completion"]["expected"] = quality["scoring_completion"]["expected"] = len(prs) * 6
        groups[name] = {"operational": subgroup_operational(rows, selected, prs), "paired_quality": paired_quality(quality["per_pr"]),
                        "paired_speed": paired_speed(rows, prs), "macro": quality["macro"]}
    per_pr = aggregate(samples, PRS)["per_pr"]
    for item in per_pr:
        for arm in "AB":
            selected = [r for r in rows if r["number"] == item["pr"] and r["arm"] == arm]
            item["arms"][arm].update(expected=3, valid=sum(r["status"] == "valid" for r in selected), terminal=len(selected))
    scorer = [load(p) for p in sorted((value["study"] / "private-codex/scores").glob("pr-*.json"))]
    return {"status": completion(value), "terminal": len(rows), "valid": sum(r["status"] == "valid" for r in rows),
            "scored_valid": sum(r["status"] == "complete" for r in samples), "groups": groups, "per_pr": per_pr,
            "diagnostics": {k: diagnostics[k] for k in ("by_arm", "native_timing", "limitations") if k in diagnostics},
            "usage": {arm: value["collection"].get("by_arm", {}).get(arm, {}).get("reported_usage", {}) for arm in "AB"},
            "knowledge_exposure": knowledge_exposure(rows, value["campaign"]),
            "actual_source_calls": {arm: {"requests": distribution([r["actual_requests"] for r in value.get("source_call_audits", []) if r["arm"] == arm]),
                                          "maximum": max((r["actual_requests"] for r in value.get("source_call_audits", []) if r["arm"] == arm), default=None),
                                          "early_prompt_gate_denied": sum(r["early_prompt_gate_denied"] for r in value.get("source_call_audits", []) if r["arm"] == arm),
                                          "stored_counter": distribution([r["stored_counter"] for r in value.get("source_call_audits", []) if r["arm"] == arm])} for arm in "AB"},
            "scorer": {"requested_models": sorted({r.get("requested_model") for r in scorer if r.get("requested_model")}),
                       "served_models": sorted({r["served_model"] for r in scorer if r.get("served_model")}),
                       "served_model_unknown_calls": sum(not r.get("served_model") for r in scorer),
                       "native_seconds": distribution([r.get("seconds") for r in scorer])}, "actual_invoice_cost": "unknown"}


def previous_failure_audit(value):
    """Explain old failures from bound reply/state bytes; never recategorize success."""
    counts, slots = Counter(), []
    for row in value["rows"]:
        if row["status"] != "invalid_run":
            continue
        attempt = row["attempts"][-1]
        root = Path(attempt["attempt_root"])
        for name in ("reply.txt", "tool-state.json", "bridge-events.jsonl"):
            if binding(root / name)["sha256"] != attempt["artifacts"].get(name):
                raise ValueError("previous failure audit bytes changed")
        state = load(root / "tool-state.json")
        error = row["error"]
        if state.get("violations"):
            events = [json.loads(line) for line in (root / "bridge-events.jsonl").read_text().splitlines()]
            aliases = [e for e in events if e.get("error") == "path must be repository-relative without traversal" and
                       e["tool"] in ("source_list", "source_grep") and (e["args"].get("path") == "." or
                       (isinstance(e["args"].get("path"), str) and e["args"]["path"].endswith("/") and ".." not in e["args"]["path"].split("/")))]
            reason = "directory_syntax_false_rejection" if len(aliases) == len(state["violations"]) else "unclassified"
        elif error == "bridge violations or complete prompt was not read":
            reason = "incomplete_prompt"
        elif error == "model output does not satisfy successful review contract":
            reason = "malformed_json"
        elif error == "review comment has missing required fields":
            reason = "optional_anchor_contract_conflict"
        elif error == "review comment severity/disposition is invalid":
            reason = "duplicate_disposition_contract_conflict"
        else:
            reason = "unclassified"
        counts[reason] += 1
        slots.append({"pr": row["number"], "arm": row["arm"], "repeat": row["repetition"], "reason": reason})
    return {"counts": dict(counts), "slots": slots, "old_failures_remain_failures": True,
            "harness_conflict_or_directory_syntax": sum(counts[k] for k in ("directory_syntax_false_rejection", "optional_anchor_contract_conflict", "duplicate_disposition_contract_conflict"))}


def render(value):
    previous, current = value["previous"], value["current"]
    lines = ["# JiuwenSwarm GLM‑5.3 协议修复与复测", "", f"状态：`{value['status']}`；复测有效评审 {current['valid']}/72，已独立评分 {current['scored_valid']} 份。", "",
             "完成率指交付可评分结果的比例；全部调用结束不等于全部有效。失败继续计入原分母，旧结果保持原判定。", "",
             "| 样本 | 资料 | 修复前有效/计划 | 复测有效/计划 | 完成率变化 |", "| --- | --- | ---: | ---: | --- |"]
    for name, label in (("primary_prospective", "主样本"), ("all", "全部样本")):
        for arm, docs in (("A", "原作者资料"), ("B", "当前知识库")):
            a = previous["groups"][name]["operational"][arm]; b = current["groups"][name]["operational"][arm]
            lines.append(f"| {label} | {docs} | {a['valid']}/{a['expected']} | {b['valid']}/{b['expected']} | {pct(a['valid']/a['expected'])} → {pct(b['valid']/b['expected'])} |")
    lines += ["", "## 修复范围与解释边界", "", "旧17次失败中，14次涉及评估接口冲突或普通目录写法，2次为模型JSON语法错误，1次未完整读取大PR提示。共享评审提示允许省略锚点和使用 duplicate，却与旧验证器冲突。所有旧失败均保留；本次新建批次，不事后补算为成功。", "",
              "本轮源代码、作者资料、知识库、12个PR、三次重复和两个模型通道保持固定，修改评估协议与提示一致性。随机生成、共享排期、服务限流及提示变化也会影响结果，不能把修复前后的变化全部归因于知识库。", "",
              f"旧 harness SHA：`{value['protocol']['previous_harness_sha256']}`；新 harness SHA：`{value['protocol']['retest_harness']['sha256']}`。具体变更：{value['protocol'].get('change_scope','见归档')}", "",
              "路径逃逸、跨组文档、未完整输入、错误模型身份和未经授权工具仍属于失败；目录尾斜线与根目录 shorthand 只在受控目录检索中规范化。没有补写证据、模型切换或内容失败后重新采样。", "",
              "## 本次失败归因", "", "| 阶段 | 组别 | 原生状态/失败原因 | 次数 |", "| --- | --- | --- | ---: |"]
    for stage, run in (("修复前", previous), ("复测", current)):
        for arm in "AB":
            diag = run["diagnostics"].get("by_arm", {}).get(arm, {})
            for reason, count in diag.get("status_counts", {}).items():
                lines.append(f"| {stage} | {arm} | status:{reason} | {count} |")
            for reason, count in diag.get("invalid_run_reason_counts", {}).items():
                lines.append(f"| {stage} | {arm} | {reason} | {count} |")
    lines += ["", "同一无效评审可能有多项拒绝原因，原因计数不直接相加当作失败调用数；源码或协议信息不足的原因保持unknown。旧失败逐槽位人工归因与原始诊断分别保存在JSON。", "",
              "## 本次准确率与速度", "", "以下精确率只统计有效、已评分输出，并按两组均有可计算结果的同一PR取均值。unknown不计误报，非缺陷建议另计。召回只针对预先冻结的自动独立审计有限问题清单，新发现不回填分母；无确认问题的PR不可计算召回。", "",
              "| 分组 | 指标 | A 原作者资料 | B 当前知识库 | 同时可计算PR数 |", "| --- | --- | ---: | ---: | ---: |"]
    for name, label in (("primary_prospective", "主样本"), ("all", "全部"), ("older_fork_exploratory", "旧分叉探索")):
        for field, text in (("defect_precision", "缺陷评论精确率"), ("confirmed_recall", "已确认问题召回"), ("advice_validity", "建议有效性")):
            item = current["groups"][name]["paired_quality"][field]
            lines.append(f"| {label} | {text} | {pct(item['A'])} | {pct(item['B'])} | {item['applicable_prs']} |")
    lines += ["", "| 主样本速度（秒） | A | B |", "| --- | ---: | ---: |"]
    for field, title in (("native_seconds", "原生评审"), ("queue_seconds", "worker内排队"), ("end_to_end_seconds", "worker入口至结束")):
        for stat in ("p50", "p90_linear"):
            a, b = (current["groups"]["primary_prospective"]["operational"][arm]["timings_valid"][field][stat] for arm in "AB")
            lines.append(f"| {title} {stat} | {num(a)} | {num(b)} |")
    pair = current["groups"]["primary_prospective"]["paired_speed"]["native_seconds"]
    lines += ["", f"同一PR与重复序号均有效的成对原生时间：A {num(pair['A'])}秒、B {num(pair['B'])}秒，B−A {num(pair['B_minus_A_seconds'])}秒；{pair['paired_repeats']}组成对重复、{pair['applicable_prs']}个PR。属于描述性耗时，不能证明因果加速。", "",
              "排队与端到端从worker入口计时；线程池入队前等待未完整记录，完整任务提交到退出耗时保持未知。429请求级重试与原生CLI重试分开，请求延迟参数不冒称实际退避耗时。P50/P90仅有效输出，对不同完成集合的比较受选择偏差影响。", "",
              "## 逐PR完成情况", "", "| PR | A 修复前→复测 | B 修复前→复测 | 复测A精确率 | 复测B精确率 |", "| --- | --- | --- | ---: | ---: |"]
    old = {r["pr"]: r for r in previous["per_pr"]}
    for row in current["per_pr"]:
        cells = [f"{old[row['pr']]['arms'][a]['valid']}/3 → {row['arms'][a]['valid']}/3" for a in "AB"]
        lines.append(f"| #{row['pr']} | {cells[0]} | {cells[1]} | {pct(row['arms']['A']['defect_precision'])} | {pct(row['arms']['B']['defect_precision'])} |")
    lines += ["", "## 输入、用量与可追溯性", "", "累计知识预算6000字符、初始两页；实际注入内容与补读均归档，库存总量不代表模型收到的上下文。每次最多60次源码/计算工具调用，单次结果24000字符，原生超时1800秒，并发13。", "",
              "所有有效调用的GLM服务实际模型均核查为GLM‑5.3；失败调用保留记录中的身份或未知状态。独立评分请求Codex gpt-6-sol/medium；原生记录未报告served model时保持未知。用量为服务记录的累计步骤tokens，不等于新增计费tokens；实际费用未知。", "",
              "#7639、#7654、#7655、#7656仅为旧分叉探索样本，不能视为无时间泄漏的前瞻评审；#7656预冻结真值仍未知。主样本8个PR均为小型后端修复，不能推广到全项目、大型功能或前端。没有执行JiuwenSwarm运行时测试。", "",
              "完整输入、流、工具调用、注入文档、评分和配置保存在Git外归档，公开JSON只保存紧凑统计与哈希。复跑入口：`python -m eval.jiuwenswarm_ab_retest_report --previous-study OLD --study NEW --output-dir OUT`。", "",
              "| 复测用量与输入 | A | B |", "| --- | ---: | ---: |"]
    for field, title in (("input_tokens", "累计输入tokens"), ("output_tokens", "累计输出tokens")):
        vals = [current["usage"][a].get(field, {}).get("reported_subtotal") for a in "AB"]
        lines.append(f"| {title} | {vals[0] if vals[0] is not None else '未知'} | {vals[1] if vals[1] is not None else '未知'} |")
    for field, title in (("affected_reviews_observed", "发生429的评审"), ("provider_429_notifications_observed", "429通知")):
        vals = [current["diagnostics"].get("by_arm", {}).get(a, {}).get("rate_limits", {}).get(field) for a in "AB"]
        lines.append(f"| {title} | {vals[0] if vals[0] is not None else '未知'} | {vals[1] if vals[1] is not None else '未知'} |")
    vals = [current["knowledge_exposure"][a]["knowledge_chars_consumed"]["p50"] for a in "AB"]
    lines.append(f"| 实际累计知识字符P50 | {num(vals[0])} | {num(vals[1])} |")
    for field, title in (("maximum", "实际源码/计算请求最大值"), ("early_prompt_gate_denied", "提示未完成而被拒绝的请求")):
        vals = [current["actual_source_calls"][a][field] for a in "AB"]
        lines.append(f"| {title} | {vals[0] if vals[0] is not None else '未知'} | {vals[1] if vals[1] is not None else '未知'} |")
    lines += ["", "冻结协议的内部计数器未累加提示读完前被拒绝的源码/计算请求；因此交付审计从原始bridge事件重计所有请求（含错误和拒绝），跨传输尝试累计，任一正式评审超过60次即阻止报告发布。实际请求与内部计数分别记录，不修改已运行的harness。"]
    lines += ["", f"独立评分实际served model未报告的调用数：{current['scorer']['served_model_unknown_calls']}；费用保持未知。", "",
              "| 归档 | 逻辑路径 | SHA256 |", "| --- | --- | --- |"]
    for name, item in value["inputs"].items():
        lines.append(f"| {name} | `{item['path']}` | `{item['sha256']}` |")
    return "\n".join(lines) + "\n"


def build(previous_study, study, output_dir, extra_bindings=None):
    from eval.jiuwenswarm_ab_diagnostics import diagnose_run
    cache = set()
    old, new = read_study(previous_study, cache), read_study(study, cache)
    provenance = load(new["study"] / "retest-provenance.json", {})
    verify_comparable(old, new, provenance)
    summaries = []
    for value in (old, new):
        verify_scores(value)
        diagnostics = diagnose_run(value["study"])
        if value["collection"] and not matching_diagnostics(diagnostics, value["collection"], value["identity"]):
            raise ValueError("native diagnostic snapshot differs")
        if any(r["status"] == "valid" and (not r.get("result_manifest_binding_verified") or
               any(a.get("integrity") != "verified" for a in r["attempts"])) for r in diagnostics.get("reviews", [])):
            raise ValueError("valid native review trace integrity differs")
        summaries.append(summarize(value, diagnostics))
    inputs = {}
    for label, value in (("previous", old), ("current", new)):
        for name in ("campaign.json", "identity.json", "collection.json", "reviews-manifest.json", "truth-prerequisite.json", "private-codex/truth-manifest.json", "private-codex/results.json", "retest-provenance.json"):
            path = value["study"] / name
            if path.is_file(): inputs[f"{label}/{name}"] = binding(path)
    for label, path in (extra_bindings or {}).items():
        if label in inputs: raise ValueError("duplicate report artifact label")
        inputs[label] = binding(path)
    result = {"schema": "jiuwenswarm-protocol-retest-report-v1", "generated_at": datetime.now(timezone.utc).isoformat(),
              "status": summaries[1]["status"], "previous": summaries[0], "current": summaries[1],
              "protocol": provenance["protocol"], "previous_failure_audit": previous_failure_audit(old),
              "cases": [{k: c[k] for k in ("number", "target", "base", "head", "context_sha256", "diff_sha256")} for c in new["campaign"]["cases"]],
              "document_content_manifest_sha256": {a: sha(new["identity"]["arms"][a]["documents"]) for a in "AB"},
              "inputs": inputs, "actual_invoice_cost": "unknown"}
    project = Path(__file__).resolve().parents[1]
    def logical(value):
        if isinstance(value, dict): return {k: logical(v) for k, v in value.items()}
        if isinstance(value, list): return [logical(v) for v in value]
        if isinstance(value, str) and value.startswith("/"):
            for root in (old["study"].parent, new["study"].parent):
                if Path(value).is_relative_to(root): return public_paths(value, root, project)
            return public_paths(value, new["study"].parent, project)
        return value
    result = logical(result)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / (NAME + ".json")).write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    (output_dir / (NAME + ".md")).write_text(render(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-study", type=Path, required=True)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--binding", action="append", default=[], metavar="NAME=FILE")
    parser.add_argument("--raw-index", type=Path)
    parser.add_argument("--validation", type=Path)
    args = parser.parse_args(argv)
    bindings = {}
    if args.raw_index: bindings["raw_trace_index"] = args.raw_index
    if args.validation: bindings["validation"] = args.validation
    for value in args.binding:
        key, separator, path = value.partition("=")
        if not separator or not key or key in bindings: parser.error("binding must be a unique NAME=FILE")
        bindings[key] = Path(path)
    result = build(args.previous_study, args.study, args.output_dir, bindings)
    print(json.dumps({"status": result["status"], "terminal": result["current"]["terminal"], "valid": result["current"]["valid"]}))


if __name__ == "__main__":
    main()
