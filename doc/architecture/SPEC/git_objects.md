# git_objects.py — Git object decoding

<!-- verified-against: 2026-10-08 -->

`tree_entries`, `batch_blobs` and `raw_changes` decode NUL-delimited tree/raw
diff records and exact-size batch blobs. Object IDs support SHA-1 and SHA-256.
File modes and raw path bytes remain explicit; malformed objects fail rather
than produce partial successful evidence.

`tree_texts` shares the bounded regular-file, UTF-8 tree read. `checked_read`
converts decoding failures into the adapter's own exception. Repository
adapters retain their fetch, permissions, upstream identity, missing-object
semantics and independent reads. Historical evidence hashes are not recomputed.
