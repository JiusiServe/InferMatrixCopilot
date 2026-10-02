---
title: "JiuwenBox 推理隐私代理：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L343-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L35-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L157-L165, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L21-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L37-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L100-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L370-L389, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L425-L448]
feature: "sandbox-privacy-proxy"
entry_points: ["jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py", "jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py"]
source_globs: ["jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py", "jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py"]
---

# JiuwenBox 推理隐私代理：实现深读

[功能概览](feature-sandbox-privacy-proxy.md) · [owner 入口](_index.md)

<!-- kb:depth feature=sandbox-privacy-proxy facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d6fb070b4ca4d9a797b99e284084b7c96ca34650c4055028b7ba44f725548123 -->
**listen_port=0 默认禁用与 skip_cert_verify 默认关闭**
start_proxy 在 config.listen_port == 0 时拒绝启动：只记 warning（"Cannot start proxy: listen_port=0 (disabled). ... Set listen_port > 0 in policy YAML to enable."）并返回当前状态字典，不抛异常也不改状态。ProxyRoute 的 skip_cert_verify 默认 False；仅当为 True 时 _get_ssl_context 才设置 check_hostname=False、verify_mode=ssl.CERT_NONE。

来源：[jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L343–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L343-L356), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L35–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py#L35-L40), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L157–L165](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py#L157-L165)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","start":343,"end":356,"sha256":"5061afee7cdf94a2a42bb92bea1660a249a3a4456ae646cecc250d32ac54f339"},{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py","start":35,"end":40,"sha256":"87ebecc4de7c2a596996255d76548c62a4d685838f319ef10a040a6de98b62bf"},{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py","start":157,"end":165,"sha256":"3dab6d171607f3ee7734256c1b71efbab3fd75db82538c589f87881cf06d203e"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox-privacy-proxy facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=218b08e3cbe60366ce432fa8ae1f249a377a75c333895b5dcb664de7ed9ef50c -->
**复用 policy 模块的头部注入校验**
manager 从 jiuwenbox.models.policy 导入 _contains_control_chars 与 _contains_crlf_or_null，在 _resolve_basic_credentials 中对用户名和解析出的密码做 CR/LF/NUL/控制字符检查，防止凭据值注入 HTTP 头部；校验放在 manager 层而非 Pydantic 模型，使 ValueError 消息为通用文本、不泄露密钥。

来源：[jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L21–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L21-L22), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L37–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L37-L53), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L100–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L100-L104)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","start":21,"end":22,"sha256":"557db75a54b6f7a12f4a85196408fd431eefe2db4c88f92fc21a347285ebb1cc"},{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","start":37,"end":53,"sha256":"cc865177eb4189e215557d109567aebd8064e24f9ac1f1cc6c5df8d8de3d4b92"},{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","start":100,"end":104,"sha256":"cb19bd394b45e0e579af1cc63bf377867fbcb13b9897b4d18da4fbe9cf34ea88"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox-privacy-proxy facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd002e11b704cad8756b158b8b11e8123a7a2b893b81f7b39fef2deb4fc830cb -->
**启动失败的错误传播与最后一路由停用**
start_proxy 中 proxy.start() 或 enable_route 抛异常时，路由状态被置为 ProxyState.ERROR、error_message 记录 str(e) 并写入日志后重新 raise，向 REST 调用方传播。stop_proxy 在禁用最后一条路由（get_enabled_route_count()==0）时停止全局代理监听并将实例置 None、状态回到 STOPPED；停用过程抛异常同样置 ERROR 并 raise。

来源：[jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L370–L389](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L370-L389), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L425–L448](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L425-L448)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","start":370,"end":389,"sha256":"5d58656792f0801fe9423318a54a5d97ab46a49efccdcd853d39823fff8783f8"},{"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","start":425,"end":448,"sha256":"ca515767ea5c4aa27913aa6a3d16f2f412d262ecd45517a50ce5cb3544a6f555"}],"trace":[]} -->
<!-- /kb:depth -->
