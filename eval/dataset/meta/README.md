# The frozen meta-benchmark (meta-improvement engine, design §11.2)

What the engine is measured against and may only READ. Changed by human pull
requests only; a self-experiment whose fingerprint diff touches this directory
is refused at registration.

- `cases/<case>/` — one historical forensics case: `records.jsonl` (the unit's
  trace/1 records), `blobs/` (the blobs they reference), `gold.json` (the
  curated gold for the item), `case.json` (`item`, `workflow`, `unit_id`, and
  `labels`: the HUMAN stage-of-loss label per missed gold entry, S0–S10).
  Created with `improve.meta.export_case` after a human labels the cell.
- `lints/<L##>/<name>.jsonl` — a unit that must trigger exactly that Tier 1
  lint (`infermatrix-copilot improve meta lint-check`).

The historical campaigns (T3, wave-2, wave-3) left narrative reports, not
per-cell labels; the cases here are labelled fresh against the traces (design
§6.1, P2). Labels are the benchmark, never the report text, so an investigator
cannot recite them.
