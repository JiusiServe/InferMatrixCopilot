---
name: fix-accuracy-golden-hardware-mismatch
description: Strict image-accuracy test (SSIM>=0.97/PSNR>=30 vs committed golden) fails deterministically after a rebase even though the image renders correctly — the golden must be regenerated FROM THE CI RUNNERS' OWN HARDWARE via build artifacts; locally-generated goldens (H200) never match H100 CI numerics.
trigger: Accuracy test fails with SSIM ~0.94-0.97 below threshold, identical value on every run (and identical for online/offline variants); mean/p99 pixel-diff checks still pass; typically after a vLLM/kernel version bump. Example, HunyuanImage3-DIT Accuracy Test.
modules: [model_executor, benchmarks]
status: active
created_at: 2026-07-12
last_used_at: 2026-07-12
run_count: 1
---

## Diagnose
1. The measured SSIM/PSNR is IDENTICAL across runs and across the online/offline
   test variants (e.g. 0.964118/28.2469 in builds 2674 and 2683) → the model
   output is deterministic; this is numerics drift vs the golden, not flakiness.
2. mean/p99 pixel-diff gates pass while SSIM/PSNR fail → the image is correct,
   the golden is from different kernels/hardware.
3. Confirm what changed: vLLM version bump (kernel numerics), or the golden was
   regenerated on non-CI hardware. H100 vs H200 produce STABLE, DIFFERENT
   outputs on the same SM90 kernels (measured SSIM 0.9641 apart for
   HunyuanImage3). NEVER conclude two images are equal because they sit at the
   same SSIM distance from a third image.

## Fix
Harvest the golden from the CI runners themselves:
1. Make the CI job upload its generated images pass-or-fail (pattern in
   `.buildkite/test-nightly.yml`, HunyuanImage3 job):
   ```yaml
   - |
     set +e
     pytest -s -v <test> -m full_model --run-level full_model
     EXIT=$$?
     buildkite-agent artifact upload "tests/e2e/accuracy/artifacts/**/*.png"
     exit $$EXIT
   ```
2. Let a nightly (or API build with `"env":{"NIGHTLY":"1"}` — required for the
   nightly tier; note scheduled nightlies cancel in-flight API builds on the
   same branch) run the job; download the artifact via
   `GET builds/<n>/jobs/<id>/artifacts` + `/artifacts/<id>/download`.
3. Verify provenance BEFORE committing: sha1 of online == offline == raw
   output, and SSIM(artifact, current golden) reproduces the exact value CI
   logged (e.g. 0.964118).
4. Commit the artifact as the golden. CI then compares its own deterministic
   output to itself → SSIM 1.0 / PSNR inf; strict thresholds hold.

## Verification
Next nightly's accuracy job passes with SSIM=1.000000 / PSNR=inf against the
harvested golden (HunyuanImage3 reference harvest: build 2683 artifact
sha1 ed597a3b — H100 pool deterministic across builds 2674/2683).

## Owner policy (2026-07-12)
The rebase branch must keep golden baselines BYTE-IDENTICAL to main — no
binary asset swaps inside a rebase PR (owner reverted both golden commits,
363f636d). When this failure appears during a rebase, classify it as a
KNOWN deterministic numerics failure, do NOT dispatch a debug agent or swap
the golden on the align branch; note it for a dedicated re-baseline PR after
the rebase merges, using the harvested CI artifact.

## Anti-patterns
- Relaxing SSIM/PSNR thresholds to absorb the drift (rejected in review of
  PR #5042) — it permanently weakens the quality gate.
- Regenerating the golden on local hardware that differs from the CI pool
  (H200 vs H100) — deterministic locally, still ~0.964 vs CI.
- Inferring image equality from equal SSIM against a third image (the
  0.94899 ≈ 0.9490 fallacy — cost one wasted golden commit d6353b24).
- Bypassing with FLASHINFER_DISABLE_VERSION_CHECK or other kernel-selection
  overrides to "make numerics match" — see
  [[fix-flashinfer-jit-cache-version-mismatch]].
