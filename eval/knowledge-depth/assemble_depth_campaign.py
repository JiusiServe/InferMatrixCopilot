"""Assemble durable source-verified campaign pages; native archive audit is separate.

The default is read-only. --apply writes only accepted depth additions and their
missing owner index links, after every checkpoint has passed the same checks.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import posixpath
import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

import yaml

from infermatrix_copilot.kb_service.gate import DIMENSIONS
from infermatrix_copilot.kb_service.init_stages import _one_line
from infermatrix_copilot.kb_service.knowledge_coverage import feature_metadata, load_policy, policy_path
from infermatrix_copilot.kb_service.knowledge_depth import depth_page, digest, verified_blocks
from infermatrix_copilot.knowledge_service.lifecycle import DEPTH_BLOCK, DEPTH_FACETS, Page, safe_source_path


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def _baseline(root, sha, path):
    try:
        return _git(root, "show", sha + ":" + path).decode("utf-8")
    except subprocess.CalledProcessError:
        return None


def _body(text):
    page = Page.parse(text)
    return page.render()[len(page.frontmatter):]


def _outside_blocks(text):
    return [line for line in DEPTH_BLOCK.sub("", _body(text)).splitlines() if line.strip()]


def _append(text, addition):
    return text + ("" if text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n") + addition + "\n"


def _blocks(text, feature, source, pin, policy, pinned_files):
    # A clean checkout alone does not exclude ignored/untracked evidence paths.
    for match in DEPTH_BLOCK.finditer(text):
        proof = re.search(r"<!-- kb:depth-proof (.*?) -->", match.group(), re.S)
        if proof is None:
            raise ValueError("depth block has no proof")
        for item in json.loads(proof[1]).get("evidence", []):
            path = item.get("path")
            if not safe_source_path(path):
                raise ValueError("unsafe evidence path")
            if path not in pinned_files:
                try:
                    raw = _git(source, "show", pin + ":" + path)
                except subprocess.CalledProcessError as exc:
                    raise ValueError("evidence is outside the pinned source tree: " + path) from exc
                if (source / path).read_bytes() != raw:
                    raise ValueError("evidence file differs from source pin: " + path)
                pinned_files.add(path)
    blocks, problems = verified_blocks(text, feature, source, pin, policy=policy)
    if problems or text.count("<!-- kb:depth ") != len(blocks) or text.count("<!-- /kb:depth -->") != len(blocks):
        raise ValueError("invalid, foreign, duplicate or edited source proof: " + feature.id)
    return blocks


def _receipt(record, feature, facet, block):
    prior = record.get("verdicts", {}).get("depth:" + feature, {})
    result = prior.get("facets", {}).get(facet, {})
    dimensions = result.get("dimensions")
    if result.get("verdict") != "pass" or not isinstance(dimensions, dict) \
            or set(dimensions) != set(DIMENSIONS["prose"]) or any(v != "yes" for v in dimensions.values()) \
            or result.get("block_sha256") != digest(block) \
            or not isinstance(result.get("reason"), str) \
            or not isinstance(result.get("model"), str) or not result["model"] \
            or not isinstance(result.get("native_trace_id"), str) or not result["native_trace_id"] \
            or not re.fullmatch(r"[0-9a-f]{64}", str(result.get("native_reply_sha256", ""))):
        raise ValueError("new facet lacks an exact successful receipt: " + feature + "/" + facet)
    if not any(isinstance(call, dict) and all(call.get(key) == result.get(key)
               for key in ("model", "native_trace_id", "native_reply_sha256"))
               and call.get("facets", {}).get(facet) == {k: v for k, v in result.items()
                    if k not in {"model", "native_trace_id", "native_reply_sha256", "block_sha256"}}
               for call in prior.get("calls", [])):
        raise ValueError("facet receipt does not bind a durable successful review call: " + feature + "/" + facet)
    return {"feature": feature, "facet": facet, "block_sha256": result["block_sha256"],
            "dimensions": dimensions, "model": result["model"],
            "native_trace_id": result["native_trace_id"], "native_reply_sha256": result["native_reply_sha256"]}


def assemble(root: Path, state: Path, source: Path):
    """Return metadata and validated writes without modifying any input."""
    root, state, source = root.resolve(), state.resolve(), source.resolve()
    metadata_raw = (state / "campaign.json").read_bytes()
    campaign = json.loads(metadata_raw)
    repo, baseline, pin = (campaign.get(key) for key in ("repo", "baseline", "pin"))
    if not isinstance(repo, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", repo) \
            or not all(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) for sha in (baseline, pin)):
        raise ValueError("campaign needs a safe repo and immutable source/knowledge SHAs")
    if _git(root, "rev-parse", baseline + "^{commit}").decode().strip() != baseline \
            or _git(source, "rev-parse", "HEAD").decode().strip() != pin \
            or _git(source, "status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("campaign base or clean source checkout differs from its immutable pin")
    manifest = _baseline(root, baseline, f"adapters/{repo}/manifest.yaml")
    policy_text = _baseline(root, baseline, policy_path(repo))
    if manifest is None or policy_text is None:
        raise ValueError("campaign baseline lacks its adapter and coverage policy")
    repo_dir = yaml.safe_load(manifest)["knowledge"]["repo_subdir"]
    if (root / policy_path(repo)).read_text(encoding="utf-8") != policy_text \
            or yaml.safe_load((root / f"adapters/{repo}/manifest.yaml").read_text())["knowledge"]["repo_subdir"] != repo_dir:
        raise ValueError("target coverage policy or knowledge root differs from the campaign baseline")
    policy = load_policy(policy_text, repo_dir)
    features = {feature.id: feature for feature in policy.features}
    partitions = campaign.get("partitions")
    workers = campaign.get("workers")
    if type(workers) is not int or not 1 <= workers <= 4 or not isinstance(partitions, dict) \
            or set(partitions) != {str(n) for n in range(workers)} \
            or any(not isinstance(group, list) or any(not isinstance(f, str) for f in group) for group in partitions.values()):
        raise ValueError("invalid campaign worker partitions")
    ownership = [feature for group in partitions.values() for feature in group]
    if len(ownership) != len(set(ownership)) or set(ownership) != set(features) \
            or campaign.get("features") != len(features) or campaign.get("denominator") != len(features) * len(DEPTH_FACETS):
        raise ValueError("partitions must own every policy feature exactly once without reducing the denominator")
    by_page = {depth_page(feature): feature for feature in features.values()}
    pinned_files, baseline_pages, old_blocks = set(), {}, {}
    for page, feature in by_page.items():
        text = _baseline(root, baseline, "knowledge/" + page)
        if text is not None:
            baseline_pages[page] = text
            old_blocks[page] = _blocks(text, feature, source, pin, policy, pinned_files)
    proposals, changes, receipts, checkpoints = {}, [], [], []
    counts = {facet: sum(facet in blocks for blocks in old_blocks.values()) for facet in DEPTH_FACETS}
    recognized_features = {by_page[page].id for page, blocks in old_blocks.items() if blocks}
    for worker, owned in partitions.items():
        path = state / f"worker-{worker}/init/{repo}/knowledge-deepen.json"
        raw = path.read_bytes()
        record = json.loads(raw)
        if any(record.get(key) != value for key, value in
               (("stage", "knowledge-deepen"), ("repo", repo), ("pin", pin), ("kb_base_sha", baseline))):
            raise ValueError("worker checkpoint identity differs from campaign: " + worker)
        depth = record.get("depth", {})
        entries, accepted = depth.get("features", {}), depth.get("accepted", {})
        if not isinstance(entries, dict) or not isinstance(accepted, dict) or set(entries) - set(features):
            raise ValueError("worker checkpoint has invalid feature state: " + worker)
        if any(fid not in owned and entry.get("attempts", 0) for fid, entry in entries.items()) \
                or any(key.startswith("depth:") and key[6:] not in owned for key in record.get("verdicts", {})):
            raise ValueError("worker executed another partition's feature: " + worker)
        checkpoints.append({"worker": worker, "sha256": hashlib.sha256(raw).hexdigest(),
                            "status": record.get("status"), "accepted_pages": len(accepted)})
        for page, candidate in accepted.items():
            feature = by_page.get(page)
            if feature is None or feature.id not in owned or page in proposals or not isinstance(candidate, str):
                raise ValueError("accepted page is outside unique worker ownership: " + str(page))
            entry = entries.get(feature.id, {})
            accepted_sha = digest(candidate)
            if entry.get("accepted_sha256") != accepted_sha:
                raise ValueError("durable accepted page hash differs: " + feature.id)
            blocks = _blocks(candidate, feature, source, pin, policy, pinned_files)
            prior = old_blocks.get(page, {})
            if not blocks or any(blocks.get(facet) != block for facet, block in prior.items()):
                raise ValueError("accepted page edits or omits an existing depth block: " + feature.id)
            recognized_features.add(feature.id)
            old = baseline_pages.get(page)
            related = f"[功能概览]({PurePosixPath(feature.page).name}) · [owner 入口](_index.md)"
            expected_body = _outside_blocks(old) if old is not None else ["# " + _one_line(feature.title) + "：实现深读", related]
            if _outside_blocks(candidate) != expected_body:
                raise ValueError("accepted page alters prose outside approved blocks: " + feature.id)
            added = [facet for facet in DEPTH_FACETS if facet in blocks and facet not in prior]
            for facet in added:
                receipts.append({**_receipt(record, feature.id, facet, blocks[facet]), "page": page, "worker": worker})
                counts[facet] += 1
            if old is None:
                proposed = feature_metadata(candidate, feature)
            elif added:
                proposed = Page.parse(old).with_sources(list(dict.fromkeys(
                    Page.parse(old).sources() + Page.parse(candidate).sources()))).render()
                proposed = _append(proposed, "\n\n".join(blocks[facet] for facet in added))
            else:
                proposed = old
            proposals[page] = proposed
            changes.append({"page": page, "feature": feature.id, "worker": worker,
                            "checkpoint_accepted_sha256": accepted_sha, "assembled_sha256": digest(proposed),
                            "baseline_sha256": digest(old) if old is not None else None, "new_facets": added})
    # Add only missing depth-page routes; never copy regenerated worker indexes.
    indexes, new_links = {}, []
    for page in proposals:
        if page in baseline_pages:
            continue
        feature = by_page[page]
        directory = PurePosixPath(page).parent
        index = str(directory / "_index.md")
        old = indexes.get(index, _baseline(root, baseline, "knowledge/" + index))
        if old is None:
            raise ValueError("new depth page has no existing owner index: " + page)
        target = PurePosixPath(page).name
        routes = re.findall(r"\[[^\n]*?\]\(([^\s)]+)\)", old)
        links = sum(posixpath.normpath(route.split("#", 1)[0]) == target for route in routes)
        if links > 1:
            raise ValueError("duplicate owner index route: " + page)
        if not links:
            title = " ".join(feature.title.split()).replace("[", "\\[").replace("]", "\\]") + "：实现深读"
            indexes[index] = _append(old, f"- [{title}]({target})")
            new_links.append({"index": index, "page": page})
    proposals.update(indexes)
    writes = {}
    for page, text in proposals.items():
        target = root / "knowledge" / page
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError("target knowledge path contains a symlink")
        prior = _baseline(root, baseline, "knowledge/" + page)
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current not in (prior, text):
            raise ValueError("target page has unrelated changes: " + page)
        if current != text:
            writes[page] = text
    threshold = policy.semantic_depth_per_facet_gt
    report = {"repo": repo, "baseline": baseline, "pin": pin, "workers": workers,
              "features": len(features), "denominator": len(features) * len(DEPTH_FACETS),
              "campaign_sha256": hashlib.sha256(metadata_raw).hexdigest(), "policy_sha256": digest(policy_text),
              "checkpoints": checkpoints, "baseline_facets": sum(map(len, old_blocks.values())),
              "new_receipt_bound_facets": len(receipts), "source_verified_facets": sum(counts.values()),
              "recognized_feature_count": len(recognized_features),
              "all_features_recognized": len(recognized_features) == len(features),
              "facet_counts": counts, "source_target_met": len(recognized_features) == len(features) and threshold is not None
                  and all(count / len(features) > threshold for count in counts.values()),
              "pages": changes, "index_links": new_links, "planned_files": sorted(writes),
              "receipts": receipts, "native_archive_audit_required": True, "problems": []}
    return report, writes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--source-tree", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.report and args.report.resolve().is_relative_to((args.root / "knowledge").resolve()):
        parser.error("assembly report must stay outside the knowledge tree")
    try:
        with ExitStack() as stack:
            if args.apply:
                campaign = json.loads((args.state / "campaign.json").read_text())
                for lock in [args.state / ".campaign.lock", *(args.state / f"worker-{n}/.worker.lock"
                             for n in range(campaign["workers"]))]:
                    handle = stack.enter_context(lock.open("r"))
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            report, writes = assemble(args.root, args.state, args.source_tree)
            report["applied"] = args.apply
            if args.apply:
                for page, text in writes.items():
                    target = args.root / "knowledge" / page
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                                     prefix=".assembly-", suffix=".tmp", delete=False) as handle:
                        temporary = Path(handle.name)
                        handle.write(text)
                    try:
                        temporary.replace(target)
                    finally:
                        temporary.unlink(missing_ok=True)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("repo", "baseline_facets", "new_receipt_bound_facets",
          "source_verified_facets", "recognized_feature_count", "source_target_met", "facet_counts",
          "planned_files", "applied", "native_archive_audit_required")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
