---
name: benchmark-datasets-module-restructured
description: Upstream moved vllm/benchmarks/datasets.py to vllm/benchmarks/datasets/datasets.py with re-exporting __init__.py
trigger: ImportError from vllm.benchmarks.datasets or missing SampleRequest/get_samples symbol
modules: [benchmarks]
status: active
created_at: 2026-06-13
last_used_at: 2026-07-11
run_count: 15
---

## Diagnose
Check if `from vllm.benchmarks.datasets import SampleRequest, get_samples` fails. The upstream moved the module from `vllm/benchmarks/datasets.py` to `vllm/benchmarks/datasets/datasets.py`. A re-exporting `__init__.py` was added to `vllm/benchmarks/datasets/__init__.py`.

## Fix
If the `__init__.py` re-exports are present, no fix is needed — the old import path still works. If the `__init__.py` is missing some symbols, add them. The re-exports include:
- SampleRequest
- get_samples
- add_dataset_parser
- BenchmarkDataset
- RandomDataset, RandomMultiModalDataset, ShareGPTDataset, SonnetDataset, HuggingFaceDataset, CustomDataset, etc.
- process_image, process_audio, process_video

Check `/rebase/vllm/vllm/benchmarks/datasets/__init__.py` for the full list.
