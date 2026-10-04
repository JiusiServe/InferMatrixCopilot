"""Trusted launcher mounted separately from candidate code. JSON-lines broker protocol."""
from __future__ import annotations
import contextlib
import json
from pathlib import Path
import sys

def main():
    payload = json.loads(Path("/input.json").read_text())
    sys.path.insert(0, "/candidate/src")
    import infermatrix_copilot
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.llm import Block, LLM, Reply
    wire = sys.stdout
    import threading
    broker_lock = threading.Lock()

    def create(self, **request):
        request.pop("on_text", None)
        request["model"] = request.get("model") or self.settings.tier_target("eco").model
        request["max_tokens"] = request.get("max_tokens") or self.settings.llm_max_tokens
        with broker_lock:
            wire.write(json.dumps({"type": "model_call", "request": request}) + "\n"); wire.flush()
            data = json.loads(sys.stdin.readline())
        data["blocks"] = [Block(**b) for b in data["blocks"]]
        return Reply(**data)

    def init(self, settings):
        self.settings, self._client, self._default_model = settings, object(), ""
        self._provider = "broker"

    def for_target(self, target):
        clone = object.__new__(LLM)
        init(clone, self.settings)
        clone._default_model = target.model
        return clone
    LLM.__init__, LLM.create, LLM.for_target = init, create, for_target
    settings = Settings(_env_file=None, **payload.get("settings", {}))
    result = {}
    # Ordinary application output cannot corrupt the broker framing.
    with contextlib.redirect_stdout(sys.stderr):
        if payload["mode"] == "tests":
            import pytest
            result["rc"] = pytest.main(["-q", "-p", "no:cacheprovider", "--confcutdir=/tests", *["/tests/" + p.removeprefix("test/") for p in payload["tests"]]])
        else:
            try:
                if payload.get("driver", "").startswith("objective-"):
                    from infermatrix_copilot.improve.objectives import worker
                    result = worker(payload, settings, LLM(settings))
                else:
                    from infermatrix_copilot.improve.drivers import worker_run
                    result = worker_run(payload, settings, LLM(settings))
            except Exception as exc:
                if not payload.get("capture_errors"):
                    raise
                result = {"execution_error": f"{type(exc).__name__}: {str(exc)[:500]}"}
    result.update(source_sha=payload["source_sha"], package_path=str(infermatrix_copilot.__file__))
    wire.write(json.dumps({"type": "result", "result": result}, ensure_ascii=False) + "\n"); wire.flush()

if __name__ == "__main__":
    main()
