---
title: Native packaging and validation entry
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
- ci
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:setup.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:pyproject.toml
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/Cargo.toml
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:tests/packaging/test_install_metadata.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:.github/workflows/pre-commit.yml
---

# Native packaging and validation

## When to use this entry

Platform-dependent installation metadata, Rust builds, native artifact inclusion and the repository validation entrypoints.

Source scopes: `setup.py`, `pyproject.toml`, `MANIFEST.in`, `requirements/`, `rust/Cargo.`, `.github/workflows/`, `.pre-commit-config.yaml`, `tools/pre_commit/`, `tests/packaging/`.

## Outside this owner

Other source owners are listed in the [component map](../_index.md); repository identity and version constraints belong to the [repository entry](../../_index.md).

## Contents

| Task | Entry | Purpose |
|---|---|---|
| Trace source, data flow and validation | [Architecture](architecture.md) | Pinned source map and compact Direct review map |

Focused tests: `tests/packaging/test_install_metadata.py`.
