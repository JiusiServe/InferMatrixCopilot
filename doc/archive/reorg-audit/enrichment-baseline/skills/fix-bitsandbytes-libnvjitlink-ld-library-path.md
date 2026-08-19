---
name: fix-bitsandbytes-libnvjitlink-ld-library-path
description: Fix libnvJitLink.so.13 dlopen failure on CUDA-13 (v0.24.0+) by registering the pip-provided nvidia-nvjitlink lib dir with ldconfig in Dockerfile.ci
trigger: CI logs show 'libnvJitLink.so.13 cannot open shared object file' / 'OSError libnvJitLink.so.13' with worker subprocess crashes, OR the docker image build itself fails with 'nvidia-cuda-nvjitlink-cu13 was not found in the package registry'. Single-device tests pass but multi-device tests fail.
modules: [worker_runner, model_executor]
status: active
created_at: 2026-06-09
last_used_at: 2026-07-11
run_count: 62
---

## Diagnose
1. Runtime symptom: CI logs show `libnvJitLink.so.13: cannot open shared object file` / `OSError: libnvJitLink.so.13`, followed by `Diffusion worker(s) died unexpectedly`. Single-device tests pass; multi-device (spawned workers) fail.
2. Build-time symptom (v0.24.0+ / CUDA 13): the docker image build fails at the nvjitlink step with `No solution found ... Because nvidia-cuda-nvjitlink-cu13 was not found in the package registry` — that package name does not exist.
3. Confirm the base image toolkit CUDA major vs the wheels: `v0.24.0` base ships `/usr/local/cuda` = CUDA **12**, but the cu130 torch/vllm wheels need `libnvJitLink.so.13`. So the `.so.13` is NOT under `/usr/local/cuda/...` — it is only in the `nvidia-nvjitlink` pip package.
4. The cu130 `torch` force-reinstall pulls `nvidia-nvjitlink==13.0.88` into site-packages already (check the build log's torch step for `+ nvidia-nvjitlink==13.0.88`), so the lib is present — it is just not on the dynamic-loader path.

## Fix
In `docker/Dockerfile.ci`, AFTER the cu130 torch force-reinstall, locate the already-installed lib and register its dir with ldconfig (do NOT hard-install a package):
```dockerfile
RUN NVJITLINK_LIB="$(find / -name 'libnvJitLink.so.13*' 2>/dev/null | head -1)" && \
    if [ -z "$NVJITLINK_LIB" ]; then \
        uv pip install --system "nvidia-nvjitlink-cu13" && \
        NVJITLINK_LIB="$(find / -name 'libnvJitLink.so.13*' 2>/dev/null | head -1)"; \
    fi && \
    test -n "$NVJITLINK_LIB" && \
    dirname "$NVJITLINK_LIB" > /etc/ld.so.conf.d/nvjitlink-cu13.conf && \
    ldconfig && \
    echo "Registered ${NVJITLINK_LIB} with ldconfig"
```
ldconfig is system-wide and survives subprocess env resets (spawn workers), so it is more robust than LD_LIBRARY_PATH. For a future CUDA-14 base, bump `.so.13` → `.so.14` and `nvidia-nvjitlink-cu13` → `-cu14`.

## Verification
`docker build -f docker/Dockerfile.ci .` reaches the nvjitlink step and prints `Registered /.../libnvJitLink.so.13 with ldconfig` (no "not found in the package registry"). At runtime, multi-device diffusion tests no longer crash with the OSError.

## Anti-patterns
- Do NOT `uv pip install "nvidia-cuda-nvjitlink-cu13"` — that package name does not exist (has an extra `cuda-`); the real wheel is `nvidia-nvjitlink-cu13`. And an unconditional install is redundant because torch's deps already provide the lib.
- Do NOT rely on `ENV LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib` when the base-image toolkit CUDA major != the wheels' CUDA major (the v0.24.0/CUDA-12 base does not contain `.so.13` at all, so this silently fails). This LD_LIBRARY_PATH approach only works when the base toolkit already ships the needed `.so.N`.
