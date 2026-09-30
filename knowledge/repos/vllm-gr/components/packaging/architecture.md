---
title: Native packaging and validation architecture
created: '2026-09-30'
updated: '2026-09-30'
type: architecture
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

# Native packaging and validation architecture

## Responsibilities and boundary

Platform-dependent installation metadata, Rust builds, native artifact inclusion and the repository validation entrypoints.

## Source and entrypoints

- `setup.py`
- `pyproject.toml`
- `rust/Cargo.toml`
- `tests/packaging/test_install_metadata.py`
- `.github/workflows/pre-commit.yml`

## Data flow

Setup selects platform requirements and builds the Rust executable for source/editable installation. Package metadata declares included native artifacts. CI workflows and pre-commit helpers define their own test selectors; verify the final wheel contents and imported runtime independently of source-tree fallbacks.

## Direct review map

Read `setup.py`, `pyproject.toml`, `MANIFEST.in`, platform `requirements/`, and `rust/Cargo.toml` together. Trace each native artifact from its build command to wheel inclusion and the runtime loader. Read `.github/workflows/pre-commit.yml` and `tools/pre_commit/` for actual selectors. Use an isolated installed-wheel smoke check when native loading or artifact layout changes.

Focused tests: `tests/packaging/test_install_metadata.py`.

## Validation

Use the target head's declared dependency versions and test selectors. Bind evidence to that head; a missing native build or incompatible environment is a validation gap.

See the [owner entry](_index.md) and [component map](../_index.md) for neighboring boundaries.
