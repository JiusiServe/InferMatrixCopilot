---
title: "Workspace Git Diff Aggregation (get_git_diff)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/session/git_diff_watcher.py:L405-L444, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/utils/diff_service.py:L768-L777, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/server/test_diff_service.py:L570-L579, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/session/git_diff_status.py:L529-L544, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/session/git_diff_status.py:L1047-L1064, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/session/git_diff_status.py:L19-L20]
feature: "workspace-git-diff"
entry_points: ["jiuwenswarm/server/utils/diff_service.py"]
source_globs: ["jiuwenswarm/server/utils/diff_service.py", "jiuwenswarm/server/runtime/session/git_diff_watcher.py", "jiuwenswarm/server/runtime/session/git_diff_status.py"]
---

# Workspace Git Diff Aggregation (get_git_diff)：实现深读

[功能概览](feature-workspace-git-diff.md) · [owner 入口](_index.md)

<!-- kb:depth feature=workspace-git-diff facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=388f3edcd10bd7183f693f6274b6e8169cf19ea904adcd67d7b7fc0b8bcdaa10 -->
**build_turn_summary_entry returns None for falsy last_turn, else a dict with files fixed to {}**
Given a falsy last_turn the function returns None locally; otherwise it builds a dict copying kind/change_set_id/turn_index/status/stats with defaults (kind "conversation_turn", status "completed", empty ids) and "files" always {}.

来源：[jiuwenswarm/server/runtime/session/git_diff_status.py:L1047–L1064](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/git_diff_status.py#L1047-L1064)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1064,"path":"jiuwenswarm/server/runtime/session/git_diff_status.py","sha256":"c9f7d0272dc48c75c1d1ac38cee0f6d738ac26cb6e392f93368193322173f9a4","start":1047}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=workspace-git-diff facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9c3e7980dadbe991918a796a9ca27d637317441be915c6ca6c7112f68378af7 -->
**update_files_with_restore：快照-更新-on_snapshot 回调，回调抛错自动回滚并重抛**
调用方传入 async on_snapshot(watch) 计算首次快照并下发响应；回调抛出任何 Exception 且 previous_state 非空时执行 restore_files_state 后重新 raise。update_files 返回 None 或未传回调时直接返回。

来源：[jiuwenswarm/server/runtime/session/git_diff_watcher.py:L405–L444](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/git_diff_watcher.py#L405-L444)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":444,"path":"jiuwenswarm/server/runtime/session/git_diff_watcher.py","sha256":"4659d38fb3562340a5f2ed7e12d35273d96f4d880c75183f8eddd1d6eab77540","start":405}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=workspace-git-diff facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=495c5622f27270b7ee041ef85b66d7a5e99982ccb4702318307262cca0f00892 -->
**项目目录解析顺序：channel_metadata.cwd → delivery_context.route_metadata.cwd → 顶层 project_dir**
_get_project_dir_from_metadata 按 docstring 声明的三步顺序任一命中即返回；测试证实仅顶层 project_dir 存在时返回该值，全部缺失时返回 None 而非抛错。

来源：[jiuwenswarm/server/utils/diff_service.py:L768–L777](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/utils/diff_service.py#L768-L777), [tests/unit_tests/server/test_diff_service.py:L570–L579](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/server/test_diff_service.py#L570-L579)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":777,"path":"jiuwenswarm/server/utils/diff_service.py","sha256":"ee689a08e75c270bcbf86cdfba996d086b33f8c7c48b3de508b0ddaf30293565","start":768},{"end":579,"path":"tests/unit_tests/server/test_diff_service.py","sha256":"d036caf4500f256e13db3a8919379159837b6fc99d83e246062db79baf1ffc21","start":570}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=workspace-git-diff facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8bc4b22840ed0155e7e9288f46457eeb68efb785a7acc300aeca1a50bfc9d268 -->
**git_diff_status imports get_diff_service from server.utils.diff_service**
git_diff_status.py imports GitError/GitOperationError from project_git and get_diff_service from diff_service at module top; the shown span establishes only this import coupling, not call behavior.

来源：[jiuwenswarm/server/runtime/session/git_diff_status.py:L19–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/git_diff_status.py#L19-L20)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":20,"path":"jiuwenswarm/server/runtime/session/git_diff_status.py","sha256":"ceaaf165e9913e2fc4ff54174a4a52a374f64d4682ecf3c7e9ffccd3d30ae4be","start":19}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=workspace-git-diff facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=105e1359b0faf322ddfd3b198ed4880fb5ae407717a48011f23637e5a11ad3ea -->
**repo_is_dirty 兜底：以 git status 口径覆盖 diff 服务缺漏，代价是丢失 stats 明细**
设计推断（非作者历史意图）：

raw_diff 为空或非 dict 时返回 DiffSummary(is_dirty=repo_is_dirty, stats=DiffStats(), files={})：dirty 判定更权威（含 untracked），但该分支下统计与文件列表恒为空。（推断）

来源：[jiuwenswarm/server/runtime/session/git_diff_status.py:L529–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/git_diff_status.py#L529-L544)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":544,"path":"jiuwenswarm/server/runtime/session/git_diff_status.py","sha256":"2b18fd6e4ec2d331354db149ce2e4c9d30c9f07f66d92ff3b2fcfa1ddc73c9df","start":529}],"trace":[]} -->
<!-- /kb:depth -->
