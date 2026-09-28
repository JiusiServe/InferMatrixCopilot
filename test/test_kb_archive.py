"""Weekly trace archives: made on the bot host, pulled and verified by the publisher."""

from __future__ import annotations

import io
import tarfile
import time

from infermatrix_copilot.kb_service.archive import make_archive, verify_archive
from infermatrix_copilot.trace_store import TraceStore
from test_kb_flow import _flow_runtime


def _runtime(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    rt.clock = lambda: time.time() + 5                    # files written "now" are before the archive time
    rt.traces = TraceStore(rt.state_dir / "traces", environ={})
    return rt


def test_an_archive_holds_new_records_and_blobs_and_restores_the_store(tmp_path):
    rt = _runtime(tmp_path)
    record = rt.traces.append("decision", inputs={"prompt": "why"}, result={"status": "pass"})
    path = make_archive(rt)
    assert path is not None and (path.parent / f"{path.name}.sha256").exists()
    manifest = (path.parent / f"{path.name}.sha256").read_text()
    assert verify_archive(path.read_bytes(), manifest, path.name)
    with tarfile.open(fileobj=io.BytesIO(path.read_bytes())) as tar:
        names = tar.getnames()
        assert "index.db" not in names and any(n.startswith("records/") for n in names)
        restored = tmp_path / "restored"
        tar.extractall(restored, filter="data")
    store = TraceStore(restored)
    assert store.rebuild_index() == 1 and store.get(record["id"]) == record
    assert store.blob(record["inputs"]["prompt"]) == "why"


def test_archives_are_incremental_and_never_reuse_a_name(tmp_path):
    rt = _runtime(tmp_path)
    rt.clock = lambda: 1790000000.0                       # every archive in the same second
    rt.traces.append("decision", inputs={"prompt": "first"}, result={"status": "pass"})
    first = make_archive(rt)
    assert make_archive(rt) is None                       # nothing new since
    rt.traces.append("decision", inputs={"prompt": "second"}, result={"status": "fail"})
    second = make_archive(rt)
    assert second is not None and second.name != first.name and first.exists()
    with tarfile.open(fileobj=io.BytesIO(second.read_bytes())) as tar:
        names = tar.getnames()
    assert len([n for n in names if n.startswith("blobs/")]) == 1   # only the new blob
    assert any(n.startswith("records/") for n in names)              # the grown record file again


def test_a_blob_that_lands_during_archiving_is_in_the_next_archive(tmp_path):
    import os

    rt = _runtime(tmp_path)
    rt.traces.append("decision", inputs={"prompt": "early"}, result={"status": "pass"})
    blobs = rt.state_dir / "traces" / "blobs" / "ab"
    blobs.mkdir(parents=True, exist_ok=True)
    pending = blobs / ".late.tmp"                          # put_blob's temp file, mid-write
    pending.write_bytes(b"late")
    os.utime(pending, (1, 1))                              # an old mtime survives the rename
    first = make_archive(rt)
    pending.replace(blobs / ("ab" + "0" * 62 + ".gz"))     # renamed after the scan
    second = make_archive(rt)
    assert second is not None
    with tarfile.open(fileobj=io.BytesIO(second.read_bytes())) as tar:
        assert tar.getnames() == ["blobs/ab/ab" + "0" * 62 + ".gz"]
    assert first.name != second.name


def test_the_publisher_pulls_verified_archives_once_and_rejects_tampered_ones(tmp_path):
    from test_kb_publisher import _setup

    rt, lifecycle, _changeset_id, pub, _gh = _setup(tmp_path)
    rt.clock = lambda: time.time() + 5
    rt.traces = TraceStore(rt.state_dir / "traces", environ={})
    rt.traces.append("decision", result={"status": "pass"})
    path = make_archive(rt)
    assert pub.sync_archives() == {"pulled": 1, "rejected": 0}
    assert (tmp_path / "publisher" / "archive" / path.name).read_bytes() == path.read_bytes()
    assert pub.sync_archives() == {"pulled": 0, "rejected": 0}          # once
    other = path.parent / "traces-999999-20000101-000000.tar.gz"
    other.write_bytes(b"not what the manifest says")
    (path.parent / f"{other.name}.sha256").write_text(f"{'0' * 64}  {other.name}\n")
    assert pub.sync_archives() == {"pulled": 0, "rejected": 1}
    assert not (tmp_path / "publisher" / "archive" / other.name).exists()


def test_restoring_in_name_order_survives_a_clock_moving_backwards(tmp_path):
    rt = _runtime(tmp_path)
    rt.clock = lambda: 1790000000.0
    first_record = rt.traces.append("decision", result={"status": "pass"})
    first = make_archive(rt)
    rt.clock = lambda: 1780000000.0                       # the clock jumped back
    second_record = rt.traces.append("decision", result={"status": "fail"})
    second = make_archive(rt)
    assert sorted([first.name, second.name]) == [first.name, second.name]
    restored = tmp_path / "restored"
    for archive in sorted((rt.state_dir / "archive").glob("traces-*.tar.gz")):
        with tarfile.open(archive) as tar:
            tar.extractall(restored, filter="data")
    store = TraceStore(restored)
    store.rebuild_index()
    assert store.get(first_record["id"]) and store.get(second_record["id"])
