"""Owner SSH policy installation and bounded, signed consumer metadata return."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
from pathlib import Path

from ..knowledge_service.containment import ContainmentError, MAX_AGE, PROTOCOL, atomic_json, canonical_json, digest
from ..knowledge_service.signing import sign, verify

TRANSPORT_PURPOSE = "kb-containment-transport"
# Code is fixed by the publisher, never supplied in a policy/model reply. The
# owner-configured files bind the running instance and physical release.
_REMOTE = """import hashlib,json,sys,time
from datetime import datetime
from pathlib import Path
from infermatrix_copilot.knowledge_service.containment import knowledge_policy_install,knowledge_usage_export,knowledge_usage_export_ack
p=json.load(sys.stdin)
c=json.loads(Path(p['config_file']).read_text())
r=Path(p['release_file']).read_bytes()
if c.get('consumer_id') != p['consumer_id']: raise RuntimeError('consumer identity mismatch')
if p['operation']=='install':
 a=knowledge_policy_install(p['envelope'],config=c,release_id='sha256:'+hashlib.sha256(r).hexdigest())
 a['ready']=False
 try:
  h=json.loads((Path(c['state_dir'])/'heartbeat.json').read_text())
  t=h['checked_at']
  t=datetime.fromisoformat(t.replace('Z','+00:00')).timestamp() if isinstance(t,str) else float(t)
  d=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
  good=(h.get('protocol_version')==1 and h.get('ready') is True and h.get('consumer_id')==p['consumer_id'] and h.get('release_id')==a['release_id'] and h.get('generation')==a['generation'] and h.get('policy_digest')==a['policy_digest'] and h.get('config_sha256')==d and 0<=time.time()-t<180)
  a.update(ready=good,runtime_ready=good,runtime_checked_at=t,runtime_config_sha256=d)
 except (OSError,ValueError,KeyError,TypeError): pass
 print(json.dumps({'ack':a,'usage':knowledge_usage_export(config=c,limit=25)}))
else:
 print(json.dumps(knowledge_usage_export_ack(p['receipts'],config=c)))
"""


def targets(publisher):
    value = publisher.containment_targets
    if value is None:
        value = json.loads(os.environ.get("KB_CONTAINMENT_TARGETS_JSON", "{}"))
    if not isinstance(value, dict):
        raise ContainmentError("containment SSH targets must be an owner-configured mapping")
    for consumer, target in value.items():
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", consumer) or not isinstance(target, dict) \
                or set(target) != {"host", "python", "config_file", "release_file"}:
            raise ContainmentError("containment SSH target schema is invalid")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]{0,199}", target["host"]):
            raise ContainmentError("containment SSH host is invalid")
        if any(not isinstance(target[k], str) or not Path(target[k]).is_absolute() for k in ("python", "config_file", "release_file")):
            raise ContainmentError("containment SSH target paths must be absolute")
    return value


def invoke(publisher, consumer, target, **payload):
    payload = {**payload, "consumer_id": consumer, "config_file": target["config_file"], "release_file": target["release_file"]}
    command = shlex.join([target["python"], "-c", _REMOTE])
    proc = publisher.containment_run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target["host"], command],
                                     input=canonical_json(payload), stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, check=False, timeout=20)
    if proc.returncode != 0 or len(proc.stdout) > 8 * 1024 * 1024:
        raise ContainmentError("authenticated consumer installation/export failed")
    return json.loads(proc.stdout)


def sync(publisher):
    configured_targets = targets(publisher)
    if not configured_targets:
        return {"containment_synced": 0, "containment_failed": 0}
    # A separate lock prevents the heartbeat and --once path racing. A failed
    # target never permits an ACK and cannot stop other consumers refreshing.
    from ..knowledge_service.containment import state_lock
    counts = {"containment_synced": 0, "containment_failed": 0}
    with state_lock(publisher.state_dir / "containment-sync"):
        envelope = json.loads(publisher.transport.read("outbox/containment-policy.json"))
        policy = verify("kb-containment-policy", envelope, publisher.service_public_key)
        if policy.get("schema_version") != PROTOCOL or not 0 <= publisher.clock() - policy["issued_at"] < MAX_AGE \
                or not publisher.clock() < policy["expires_at"]:
            raise ContainmentError("service containment policy is not fresh")
        def transfer(entry):
            consumer, target = entry
            if consumer not in policy["consumers"]:
                return False
            try:
                result = invoke(publisher, consumer, target, operation="install", envelope=envelope)
                ack, usage = result["ack"], result["usage"]
                if ack.get("consumer_id") != consumer or usage.get("consumer_id") != consumer:
                    raise ContainmentError("consumer transport returned a different identity")
                payload = {"schema_version": PROTOCOL, "consumer_id": consumer,
                           "received_at": publisher.clock(), "ack": ack, "usage": usage}
                signed = sign(TRANSPORT_PURPOSE, payload, publisher.publisher_key)
                publisher.transport.write_containment(digest(signed), canonical_json(signed))
                # Durable source inbox is now responsible for retry/import.
                invoke(publisher, consumer, target, operation="ack_usage", receipts=usage["receipts"])
                return True
            except (ContainmentError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
                return False
        # Two remote instances refresh concurrently; slow GitHub/model work is
        # on another thread and a stopped consumer cannot delay its siblings.
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8,len(configured_targets))) as pool:
            for ok in pool.map(transfer,configured_targets.items()):
                counts["containment_synced" if ok else "containment_failed"] += 1
    return counts
