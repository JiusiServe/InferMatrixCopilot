# 2026-04-22 — TRANSFORMERS_CACHE 覆盖 HF_HOME

- 编号：`inc-2026-04-22-remote-ssh-slurm-container-02`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：TRANSFORMERS_CACHE 覆盖 HF_HOME
- 影响范围：framework/remote

**症状**：模型路径指向 `/models/huggingface/transformers/` 而非 `$HF_HOME/hub/`
**根因**：容器默认设了 `TRANSFORMERS_CACHE`，优先级高于 `HF_HOME`
**关键**：`TRANSFORMERS_CACHE=`（空字符串）≠ `unset`
**解法**：`unset TRANSFORMERS_CACHE`
