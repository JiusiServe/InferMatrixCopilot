"""Offline, real-protocol acceptance exercise; never mutates serving policy.

This proves SDK protocol behavior in isolated directories. Production consumer
ACKs are a separate mandatory barrier, not implied by this drill.
"""
from __future__ import annotations

import json
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

from ..knowledge_service.containment import (
    ContainmentError, _issue_usage, atomic_json, configured, digest,
    knowledge_availability_check, knowledge_policy_install, knowledge_publication_guard,
    knowledge_usage_record, load_policy, text_hash,
)
from ..knowledge_service.signing import public_key_text, sign, verify

PURPOSE = "kb-maintenance-drill"
SCENARIOS = {"issued_provenance", "old_context_denied", "raw_reads_denied", "stale_denied",
             "signature_denied", "replay_denied", "corrected_bytes_allowed", "old_bad_hash_denied",
             "publication_fenced", "strict_scope_denied", "cached_context_denied", "shadow_inert"}


def _denied(operation):
    try:
        operation()
        return False
    except (ContainmentError, ValueError, OSError):
        return True


def _exercise(rt, root):
    from ..knowledge_context import KnowledgeContextService
    from ..knowledge_docs import KnowledgeDocs
    from ..knowledge_view import KnowledgeView
    from .containment import record_hold
    from .maintenance_units import page_units
    key = rt.outbox._key
    consumer = "isolated-acceptance"
    cfg = {"enabled": True, "consumer_id": consumer, "public_keys": [public_key_text(key.public_key())],
           "policy_path": str(root / "policy.json"), "state_dir": str(root / "consumer")}
    page = "repos/drill/contract/rules.md"
    tree = root / "knowledge"
    path = tree / page
    path.parent.mkdir(parents=True)
    original = "## DRILL-1a — contract\n\nPreserve the original value.\n"
    corrected = "## DRILL-1a — contract\n\nReject the original value.\n"
    path.write_text(original)
    view = KnowledgeView(tree, "packaged")
    unit = page_units(page, original, "drill", "packaged")[0]
    def envelope(generation, decisions=(), **times):
        now = time.time()
        return sign("kb-containment-policy", {"schema_version":1,"generation":generation,
                    "consumers":[consumer],"decisions":list(decisions),
                    "issued_at":times.get("issued_at",now),"expires_at":times.get("expires_at",now+600)}, key)
    clean = envelope(1)
    knowledge_policy_install(clean, config=cfg, release_id="isolated-sdk")
    context = {"documents":[{"document_id":page,"excerpt":original}],"knowledge_snapshot":"packaged"}
    usage = _issue_usage(context, view=view, config=cfg)
    injected = knowledge_usage_record(context, injected=True, config=cfg)
    results = {"issued_provenance":knowledge_availability_check(injected,config=cfg)["allowed"] and
               _denied(lambda:knowledge_usage_record({**context,"invented":True},config=cfg))}
    strict = _issue_usage({"scope":"snapshot","repository":"drill"}, mode="strict",view=view,config=cfg)
    resolver = lambda *_: {"repo_id":"drill","knowledge_slice":"repos/drill","source_pin":"a"*40,
                            "catalog_hash":"b"*64,"policy_hash":"c"*64}
    service = KnowledgeContextService(view, root / "cache.sqlite", resolver=resolver, knowledge_maintenance=cfg)
    session = service.open_session("drill", source_pin="a"*40, review_id="acceptance")["session_id"]
    service.read(session, page)
    held = {"unit_id":unit["unit_id"],"repo":"drill","page":page,"block_id":unit["block_id"],"kind":unit["kind"],
            "state":"held","denied_hashes":[unit["content_sha256"]],"approved_hashes":[],"approved_page_hashes":[]}
    hold_envelope = envelope(2,[held])
    started, finished = threading.Event(), threading.Event()
    errors = []
    def install_hold():
        started.set()
        try:
            knowledge_policy_install(hold_envelope,config=cfg,release_id="isolated-sdk")
        except Exception as exc:
            errors.append(type(exc).__name__)
        finally:
            finished.set()
    with knowledge_publication_guard(config=cfg):
        worker = threading.Thread(target=install_hold,daemon=True)
        worker.start()
        started.wait(2)
        # An installer must wait for the actual cross-process publication lock.
        results["publication_fenced"] = not finished.wait(0.05)
    worker.join(5)
    results["publication_fenced"] &= finished.is_set() and not errors
    results["old_context_denied"] = not knowledge_availability_check(usage,config=cfg)["allowed"]
    results["strict_scope_denied"] = not knowledge_availability_check(strict,config=cfg)["allowed"]
    with configured(cfg):
        results["raw_reads_denied"] = _denied(lambda:KnowledgeDocs(tree,"repos/drill").read(page))
    results["cached_context_denied"] = _denied(lambda:service.read(session,page))
    results["replay_denied"] = _denied(lambda:knowledge_policy_install(clean,config=cfg,release_id="rollback"))
    stale = envelope(3,[held],issued_at=time.time()-601,expires_at=time.time()-1)
    results["stale_denied"] = _denied(lambda:knowledge_policy_install(stale,config=cfg,release_id="stale"))
    wrong = sign("kb-containment-decision",hold_envelope["payload"],key)
    results["signature_denied"] = _denied(lambda:knowledge_policy_install(wrong,config=cfg,release_id="forged"))
    path.write_text(corrected)
    new_unit = page_units(page,corrected,"drill","packaged")[0]
    restored = {**held,"state":"corrected","approved_hashes":[new_unit["content_sha256"]],
                "approved_page_hashes":[text_hash(corrected)]}
    knowledge_policy_install(envelope(3,[restored]),config=cfg,release_id="corrected-sdk")
    fresh = _issue_usage({**context,"documents":[{"document_id":page,"excerpt":corrected}],"review_id":"corrected"},view=view,config=cfg)
    results["corrected_bytes_allowed"] = knowledge_availability_check(fresh,config=cfg)["allowed"]
    path.write_text(original)
    with configured(cfg):
        results["old_bad_hash_denied"] = _denied(lambda:view.path(page))
    shadow_rt = SimpleNamespace(containment_enforce=False)
    before = Path(cfg["policy_path"]).read_bytes()
    finding = {"outcome":"contradicted","reason":"Synthetic drill contradiction","reviewer":"independent:fixture",
               "evidence":[{"repository":"drill/source","sha":"a"*40,"path":"source.py","start_line":1,
                            "end_line":1,"content_sha256":text_hash("pass\n"),"excerpt":"pass\n"}]}
    results["shadow_inert"] = record_hold(shadow_rt,unit,finding,enforce=False)["status"] == "would_hold" and Path(cfg["policy_path"]).read_bytes()==before
    return results


def run_revocation_drill(rt, policy_sha256):
    from .containment import _consumers, _key
    if not isinstance(policy_sha256,str) or len(policy_sha256)!=64:
        raise ContainmentError("drill must bind the current maintenance policy")
    with tempfile.TemporaryDirectory(prefix="kb-containment-drill-") as temporary:
        results = _exercise(rt,Path(temporary))
    artifact = {"protocol":1,"policy_sha256":policy_sha256,"consumers":_consumers(rt),
                "checked_at":rt.clock(),"scenarios":results,"scope":"isolated-sdk-protocol"}
    body = {**artifact,"artifact_sha256":digest(artifact),"passed":set(results)==SCENARIOS and all(results.values())}
    folder = Path(rt.state_dir)/"maintenance"
    folder.mkdir(parents=True,exist_ok=True)
    atomic_json(folder/"revocation-drill.json",sign(PURPOSE,body,_key(rt)))
    return body


def acceptance_current(rt, policy_sha256):
    from .containment import _consumers, _key
    try:
        path = Path(rt.state_dir)/"maintenance/revocation-drill.json"
        if path.is_symlink():
            return False
        body = verify(PURPOSE,json.loads(path.read_text()),_key(rt).public_key())
        artifact = {k:v for k,v in body.items() if k not in {"artifact_sha256","passed"}}
        return body.get("protocol")==1 and body.get("scope")=="isolated-sdk-protocol" \
            and body.get("policy_sha256")==policy_sha256 and body.get("consumers")==_consumers(rt) \
            and bool(body["consumers"]) and body.get("passed") is True \
            and body.get("artifact_sha256")==digest(artifact) \
            and set(body.get("scenarios",{}))==SCENARIOS and all(v is True for v in body["scenarios"].values())
    except (ValueError,OSError,KeyError,TypeError,RuntimeError):
        return False
