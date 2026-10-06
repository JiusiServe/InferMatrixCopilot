---
title: "MRv2 settled row preprocess 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components]
sources: ["PR #8477"]
---

# MRv2 settled row preprocess 规则

## EXEC-SETTLED-1a — Vectorized settled rows 必须保留 scalar predicate 和 replay fallback

- 触发：修改MRv2run_preprocess、_split_settled_rows、eagerMTPmetadata或preemptedstreamrestore。
- 强制：settled仅当本步scheduledtokens=1且slotowner恰等当前requestID；返回settled与remaining两组保持roworder/queryoffset。当identitydecode另有skip或pendingpreemptionreplay时保留原rowloop，buffer/slot清理同步清settledowner。eagerMTPtuple一次transpose仍按原row/request/prefill/firstaudio/position字段布局，ready更新保留slot→ID；只有待restore状态非空才扫描，CPU保存history恢复到当前workerdevice后再执行。
- 禁止：只靠slot命中旧request；把preemptionreplay当普通settledskip；转置时重排firstaudio/prefill flags；以CPU/GPU驻留判断扩展为任意device迁移保证。
- 验收：随机slotpermutation、staleID、mixedtokencount、pendingreplay、queryoffset与scalarpredicate对照；暂停/恢复streamdecoder和非emptyrestore保留原PCM，热路径改写不改变requeststate。 ^[PR #8477]
