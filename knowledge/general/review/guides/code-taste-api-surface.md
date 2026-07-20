---
title: "Code Taste · API Surface"
created: 2026-07-10
updated: 2026-07-20
type: guide
tags: [general, review]
sources: ["PR #4980", "PR #5037", "PR #5084"]
---

# Code Taste · API Surface

Use this before adding any public or semi-public knob, request field, internal optional fast path, or shared schema field.

## New knobs default to no

Before adding a CLI arg / API field / config / `extra_args` key, answer:

- Can it be derived from existing parameters?
- Will its default fight another path's default?
- Does the user really need direct control?
- Does downstream already have a more stable raw expression?
- Can it ever be removed?

If the answer is vague, do not add the knob.

## Contract matrix

For request parameters, `extra_body`, `extra_args`, `mm_processor_kwargs`, multimodal keys, and AR-to-DiT bridge fields, write:

- **ingress:** top-level, nested `extra_args`, CLI/example, legacy caller;
- **value shape:** bool, string bool, `None`, 0/1, sentinel, missing;
- **owner:** serving/protocol, bridge, pipeline, processor, or model config;
- **consumer:** actual downstream key/field, legacy compatibility, unsupported path behavior;
- **consumer-specific default:** whether tokenizer, system prompt, scheduler, cache, backend need separate variables;
- **no-op:** condition image absent, feature disabled, empty image list;
- **docs/tests:** docs, bad-path, string-bool, legacy-key, multimodal-key tests.

Prefer passing raw facts, such as `(height, width)`, over premature internal concepts like `target_ratio_idx`.

## Internal optional parameters

Adding a function parameter or optional fast path is still API surface. The docstring and guards must cover:

- ownership: who creates and consumes it;
- tensor invariants: device, dtype, contiguous, shape/layout, length;
- execution context: rank, stage, mode, stream, cache enabled state;
- `None` meaning: old path, disabled path, or default inference;
- failure point for a wrong caller.

Data contract is checked by the data owner. Execution-context contract is checked by the caller owner that knows rank/stage/mode.

## Shared state/schema

Changing `NamedTuple`, dataclass, `TypedDict`, msgspec Struct, or request/response schema is a shared ABI change:

```bash
rg "<TypeName>\\("
rg "<state_name>|<field_name>"
```

Check constructors, positional calls, unpack sites, handoff points, and cross-runner consumers. New fields go at the end with defaults, or all constructors become keyword calls. If only one path needs the field, prefer a path-specific state.

`py_compile` and `ruff` do not prove runtime arity compatibility. Execute at least one constructor smoke.

## Multimodal key changes

Before changing shared serving/chat multimodal keys:

```bash
rg '"img2img"|"image"|"images"' vllm_omni/model_executor vllm_omni/diffusion tests
```

Explain each affected model as keep, convert, or not applicable. Do not turn one model's correct key into the repository-wide correct key.

Common consumers:

| Key | Typical consumer | Shared path rule |
| --- | --- | --- |
| `image` | HunyuanImage3 / GLM / many image understanding or DiT bridge paths | Use only in the owner path |
| `img2img` | Bagel / Flux Kontext and img2img parsers | Preserve in shared chat path unless every consumer has compatibility |
| `images` | Diffusion pipeline batch / multi-image inputs | Convert only by explicit pipeline consumer contract |

## Moving a public symbol is an API migration

When a refactor moves a class or helper between modules, search repository docs,
examples, tests, and import sites before deleting the old path. A compatibility
shim must re-export the canonical definition; emitting a warning without the
symbol still breaks imports. Never leave separate old/new class definitions:
different class identities break `isinstance`, registries, serialization, and
dispatch even when their source text is identical. ^[PR #4980]

Preserve behavior as well as the import path. For an accumulator, formatter, or
output container, inventory metadata relocation, empty-input behavior, mutation
semantics, and return-value ownership. An API that sometimes mutates `self` and
sometimes returns `incoming` is not safely "in-place"; give it an explicit
merge-style name and require callers to store the return value. ^[PR #4980]

Minimum migration evidence:

1. old and new imports resolve to the same object identity;
2. existing metadata and empty/non-empty cases retain their behavior;
3. every caller follows the same return-value contract;
4. the deprecated path has a focused regression test.

## Claims, registries, schemas, and generated files move together

A documented alias is public API only if the live registry/parser accepts it.
A hardware support row must match the runtime platform gate and minimum
capability; `unsupported` must not be softened into `untested`. Schema names in
docs and fixtures must match the parser exactly (`mark` and `marks` are different
contracts). ^[PR #5037] ^[PR #5084]

When many JSON/YAML cases repeat the same hardware or marker metadata, keep the
canonical value in one generator, fixture, or patch function and regenerate the
cases. Review both the source-of-truth code and rendered examples so a docs-only
rename cannot drift from execution. Related repository-specific routing lives in
[vLLM-Omni Config rules](../../../repos/vllm-omni/components/config/rules.md) and
[CI guidance](../../../repos/vllm-omni/ci/guides/ci-environment-gotchas.md).

## PR #3626 example

`infer_align_image_size` was not a local pipeline bool. It was simultaneously an OpenAI-compatible request field, `extra_args` field, `mm_processor_kwargs`, DiT extra arg, and processor switch. Top-level bool parsing did not cover nested `extra_args`; `"false"` could become true. T2I had no condition image, yet prompt-side `mm_processor_kwargs` could force a pure text request into multimodal preprocessing. This kind of change requires the full matrix before editing.
