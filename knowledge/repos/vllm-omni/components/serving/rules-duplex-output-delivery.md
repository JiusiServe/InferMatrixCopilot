---
title: "Duplex output delivery 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components]
sources: ["PR #7644"]
---

# Duplex output delivery 规则

## SERV-DUPLEX-OUT-1a — Per-session output 必须有界且不能阻塞其他 session

- 触发：修改 DuplexOutputBuffer、manager/handle shared outbox、overflow、open rollback 或 closure。
- 强制：同进程engine/caller共享每session一个buffer，producer不阻塞；默认compactJSON含base64计2MiB/512events，error+ResponseDone独立reserve64KiB/8events，另有一个held event与独立finalclosure slot。普通事件overflow fail该response并只close该session；保留待发ending身份改failed，不重复已接受ending，移除失败partialhistory且保留enginecleanup binding。reserve满可省略error/ending，closure仍有位；oversizedclose details压缩。open rollback在首次await前去掉bufferowner，lateordinaryoutput不能回unboundedsharedqueue或重开handle。
- 禁止：把预算说成全部Python/RSS、rawstage mailbox或replaystore上限；阻塞全局pump等慢consumer；已close后接收lateaudio；承诺closure必达网络或资源cleanup必成功。
- 验收：ordinary/reserve/closure边界、overflowpendingending/已acceptedending、failedopen再cancel、latesend和两个独立session同时覆盖；slow一个session期间另一个继续有序输出。 ^[PR #7644]

## SERV-DUPLEX-OUT-1b — Cancelled audio 必须在 sequencing 前再次验证

- 触发：修改barge-in/silentclose、queued/heldaudio、WebSocketattachmentlock、replayjournal或localiteration。
- 强制：取消按response ID与through_epoch先invalidate queued/heldaudio，active及cancelleddraining都在await stageabort前处理；其他response和nonaudio原顺序保留。WebSocket在connectionlock内以bufferguard再次验证，再分配sequence、journal与on_accepted；guard不能跨networkawait。localhandle共享同validity，单consumer完成当前event后再get。
- 禁止：只在dequeue时校验而让heldaudio等待lock后误发；清空其他response；回撤已经sequenced/journaled/transmitted audio，或把模型emission的sent_ms当物理播放/传输证明。
- 验收：锁前hold再cancel、queued+held、draining、silentclose、localiterator和另外session自然完成分别覆盖；无效audio既不sequenced也不journaled/callback，已交付音频需要客户端停止播放。 ^[PR #7644]

## SERV-DUPLEX-OUT-1c — Creation event payload 必须保持入队时计量大小

- 触发：修改response creation projector、conversation item增长或bufferbyteaccounting。
- 强制：growing state item与三类creation event使用不同dict/content，后续text/transcript delta只增长state，queuedcreationpayload保持原shape/size；有效audio前的completion FIFO顺序保持。
- 禁止：共享growingcontent使已计量事件无界长大；宣称此creation fix覆盖后续truncation的所有completion/retrievalmutableitem问题；以CPUfixture说明所有模型真实E2E已验证。
- 验收：真实projector产生creation→入队计量→追加text/transcript，检查state增长而queuedpayload/bytes不变；不同modelharness必须传manager与handle共享的output_buffer，新ownerfixture不能遗漏新增openmessage字段。 ^[PR #7644]
