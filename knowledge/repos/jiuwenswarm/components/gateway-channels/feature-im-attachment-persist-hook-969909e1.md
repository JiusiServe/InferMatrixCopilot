---
title: "IM Attachment Persist Hook (E2A + HTTP Bridge) — ChannelManager wiring"
created: 2026-10-06
updated: 2026-10-07
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L163-L183, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L230-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L206-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L260-L262, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L127-L162, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L176-L185, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L223-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L186-L193, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L195-L219, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L127-L147, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L163-L185, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L195-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L266-L272, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L160-L182, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L203-L234]
feature: "im-attachment-persist-hook-969909e1"
entry_points: ["jiuwenswarm/gateway/channel_manager/channel_manager.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/channel_manager.py"]
---

# IM Attachment Persist Hook (E2A + HTTP Bridge) — ChannelManager wiring

<!-- kb:knowledge owner=feature-im-attachment-persist-hook-969909e1 facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Supported routing modes and explicit deferral**

The hook supports single-user IM deployments with an E2A or HTTP-bridge-capable agent client, returning persisted-file metadata including the AgentServer-side deduplicated name. IM AgentOS multi-user routing is explicitly deferred: for AgentOS-routing clients a deliberately failing hook is installed that raises "IM attachment routing requires an authenticated AgentOS user_id", because the inbound IM protocol does not yet carry an authenticated per-message user_id routing key.

Sources / 来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L163–L183](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L163-L183), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L230–L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L230-L244)

<!-- kb:knowledge owner=feature-im-attachment-persist-hook-969909e1 facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Fail-hard over local fallback (decision D6)**

On any non-shared-directory client the hook never falls back to writing on the Gateway: upload or E2A failures raise so the message fails as retryable, trading availability for correctness — a local fallback would silently place attachments in the Gateway deployment directory instead of the target AgentServer's injection directory. The size-based transport split is a second deliberate tradeoff (design §10.5 per the comment): small attachments pay base64/E2A overhead while large ones avoid a `PayloadTooBig` error that would take down the whole Gateway↔AgentServer WebSocket connection.

Sources / 来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L206–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L206-L229), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L260–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L260-L262)

<!-- kb:knowledge owner=feature-im-attachment-persist-hook-969909e1 facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Hook injection and call contract**

The entry point is `_try_wire_file_persist_hook`, invoked from both `register_channel` and `register_channel_with_inbound` (channel_manager.py:L127-L147). Injection occurs only when the channel exposes `set_file_persist_hook` and the MessageHandler has an `agent_client`; otherwise it returns silently (L157-L162). The installed hook takes `(content, category, filename)` and returns a metadata dict. Failure behavior is conditional per branch: AgentOS-routing clients get a hook that always raises `RuntimeError` (L176-L183); legacy shared-directory clients get no hook at all (L184-L185); on the installed persist hook, a failed HTTP upload (L223-L229) or failed E2A call (L260-L261) is converted to `RuntimeError`, and the E2A success path returns the agent payload as-is without field validation (L262).

Sources / 来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L127–L162](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L127-L162), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L176–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L176-L185), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L223–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L223-L229), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L260–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L260-L262)

<!-- kb:knowledge owner=feature-im-attachment-persist-hook-969909e1 facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Derived identifiers, not user settings**

Within this file the hook is governed entirely by runtime discovery (channel capability, agent_client routing type), not by user-facing configuration keys; the ChannelManager `config` dict is unrelated to hook wiring. The storage platform identifier is derived from the channel's `channel_id`, lowercased and sanitized so only alphanumerics, `_` and `-` survive — e.g. the `feishu_enterprise:<bot_key>` form's colon cannot serve as a directory name — falling back to `im` when empty (L186-L193). The HTTP-bridge target path `agent/workspace/<platform>_files/downloads/<category>/<filename>` is fixed in code, and the transport threshold comes from `E2A_PAYLOAD_MAX_BYTES` imported from `agent_http_bridge` (L201-L219).

Sources / 来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L186–L193](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L186-L193), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L195–L219](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L195-L219)

<!-- kb:knowledge owner=feature-im-attachment-persist-hook-969909e1 facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Hook wiring points and routing-mode dispatch**

ChannelManager wires the attachment persist hook at two registration points: `register_channel` and `register_channel_with_inbound` both call `_try_wire_file_persist_hook` after registering the channel, while `register_external_channel` registers the instance without any callback or hook wiring. Inside `_try_wire_file_persist_hook`, three routing modes are distinguished via `e2a_proxy` predicates: AgentOS-routing clients get an explicitly failing hook (no authenticated user_id routing key, deferred), legacy shared-directory clients get no hook (FileService keeps local persistence), and other clients get a dual-transport hook — small payloads go base64 over E2A `IM_FILE_PERSIST` to the AgentServer, payloads over `E2A_PAYLOAD_MAX_BYTES` go through the authenticated HTTP bridge to `agent/workspace/<platform>_files/downloads/<category>/<filename>`, with failures raising rather than falling back to Gateway-local disk.

Sources / 来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L127–L147](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L127-L147), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L163–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L163-L185), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L195–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L195-L229), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L266–L272](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L266-L272)

<!-- kb:knowledge owner=feature-im-attachment-persist-hook-969909e1 facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Attachment persist hook unit tests**

Runtime pytest unit tests exist for the hook's routing-mode behavior. `test_agentos_attachment_never_falls_back_to_gateway_workspace` (pytest.mark.asyncio) wires the hook via `manager._try_wire_file_persist_hook` with `is_agentos_routing_client` monkeypatched to True, then asserts invoking `channel.hook(b"x", "images", "a.png")` raises RuntimeError matching "authenticated AgentOS user_id", matching the source's failing-hook branch. `test_legacy_single_user_keeps_file_service_local_persistence` monkeypatches `is_legacy_shared_directory_client` to True and asserts no hook is installed (`channel.hook is None`). `test_enterprise_feishu_bot_uses_safe_attachment_storage_platform` monkeypatches `e2a_proxy.fetch_agent_unary`, sets `channel_id = "feishu_enterprise:bot-a"`, and asserts the E2A params carry the sanitized `platform == "feishu_enterprise_bot-a"`. Tests have not been executed here.

Sources / 来源：[tests/unit_tests/channel/test_attachment_persist.py:L160–L182](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L160-L182), [tests/unit_tests/channel/test_attachment_persist.py:L203–L234](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L203-L234), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L163–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L163-L185)

