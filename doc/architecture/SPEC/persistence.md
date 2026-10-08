# persistence.py — durable bytes

<!-- verified-against: 2026-10-08 -->

`atomic_write_bytes` writes an exclusive temporary file, flushes and fsyncs,
replaces the target and fsyncs its directory. With no explicit mode, existing
regular-file permissions are preserved. A symlink is replaced, not followed.
`immutable_write_bytes` publishes by exclusive hardlink; an explicitly allowed
retry succeeds only for an identical regular file. Temporary files are cleaned
on failure. Real storage failures propagate.

Callers own serialization, parent creation, authorization and locks. An
optional directory-fsync callback preserves a caller's existing platform
policy; the shared default is strict where directory fsync is available.
