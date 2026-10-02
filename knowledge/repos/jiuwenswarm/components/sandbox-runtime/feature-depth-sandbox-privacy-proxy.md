---
title: "JiuwenBox 推理隐私代理：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L343-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L35-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L157-L165, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L21-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L37-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L100-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L370-L389, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L425-L448, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L327-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L367-L396, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L219-L255, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/tests/integration/test_inference_privacy_proxy.py:L484-L497, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/tests/integration/test_inference_privacy_proxy.py:L500-L502, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L284-L294, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L219-L246, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L354-L372]
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

<!-- kb:depth feature=sandbox-privacy-proxy facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b2f4a7dcb497d33e42b339e1baf4667809eba074fabaf7d3d1b57810323d0eb8 -->
**无 basic_username 且无 api_key 的路由经 _inject_api_key 原样透传，仅当 route.use_tls 才走 TLS 转发**
_handle_connection 先 client_reader.read(65536) 读入请求；354 行把整理好的 new_headers_raw 交给 _inject_api_key——route.basic_username 未设（230–231 行不触发 Basic 改写）且 route.api_key 为空时按 233–234 行原样返回字节；重组后的请求仅当 route.use_tls 才构造 ssl_ctx，随后写入并 drain 到 route.target_host:route.target_port（358–368 行）。

来源：[jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L284–L294](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py#L284-L294), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L219–L246](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py#L219-L246), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L354–L372](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py#L354-L372)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":294,"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py","sha256":"90d174da72a48be1b45b98e79d7c488c917e25cb894fe65d254903e097e79a2d","start":284},{"end":246,"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py","sha256":"52a39e10cbaef8c529cad0adedc126e6708dc0955566a384c0493879a4391fd7","start":219},{"end":372,"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py","sha256":"74efbdd27eb52e3564faeff62a011c0569f82c1c0c17411a4101bc70c46e997a","start":354}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox-privacy-proxy facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d37c7b8106764804168bb3febae1f865da49eb232921a875fdf669d2b912c14f -->
**start_proxy(name) 契约：缺失抛 not found，listen_port=0 仅告警返回**
start_proxy(name) 持锁查 _proxies["default"] 与同名路由，任一缺失抛 ValueError("Proxy '<name>' not found")；listen_port==0 时不抛错，记 warning "Set listen_port > 0 in policy YAML to enable." 后返回 {name,state,started_at,error_message}，启用由调用方在 policy YAML 设端口。

来源：[jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L327–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L327-L356), [jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py:L367–L396](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py#L367-L396)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":356,"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","sha256":"17f6fcae4b64974e1894c9f4b5f4408a34b8be596fcddc88725b2030330c1665","start":327},{"end":396,"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy_manager.py","sha256":"4c22f37aa812f3599ccd7d90b0c7e8429a11e3492d0efe1a405f0673607726d0","start":367}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox-privacy-proxy facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c456795dbe0019e1d546d21381e486d4864973f64de39bf28a7987c4a353a0c -->
**通配覆写仅替换已存在的凭据头：可纠正占位密钥但不为缺失头新增凭据（推断）**
设计推断（非作者历史意图）：

推断：L238-L250 以 `re.sub` 把已存在的 `Authorization: Bearer …` 与 `X-Api-Key: …` 整体替换为路由配置的 `route.api_key`，客户端带任意占位值都会被纠正为策略密钥；代价是请求本不带这两类头时不会新增凭据（无匹配则 `result` 原样、`injected` 为 False，仅少一条注入日志）。

来源：[jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py:L219–L255](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py#L219-L255)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":255,"path":"jiuwenbox/src/jiuwenbox/proxy/inference_privacy_proxy.py","sha256":"779dfc83d1eea893c0f7487960444f3a4dc46d8c3218c3b967d955c74ab2367f","start":219}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox-privacy-proxy facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e35ea39e0ecd02c7a1ad5fff74e563242a6d3507340b27b1ab2089196c25416 -->
**test_start_proxy 断言 start_proxy 返回 running；缺失名断言抛 ValueError "not found"**
`TestProxyManagerLifecycle.test_start_proxy`（L484-L497）在运行时断言 `manager.start_proxy("test")` 返回 `state=="running"`、`get_proxy("test")` 亦为 running，随后调用 `validate_proxy_http(proxy_listen_port, "/test/v1/chat", expect_forward=True)` 辅助（其内部断言未在所示片段给出）；`test_start_nonexistent_proxy_raises`（L500-L502）断言 `start_proxy("nonexistent")` 抛 `ValueError` 且 match="not found"。

来源：[jiuwenbox/tests/integration/test_inference_privacy_proxy.py:L484–L497](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/tests/integration/test_inference_privacy_proxy.py#L484-L497), [jiuwenbox/tests/integration/test_inference_privacy_proxy.py:L500–L502](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/tests/integration/test_inference_privacy_proxy.py#L500-L502)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":497,"path":"jiuwenbox/tests/integration/test_inference_privacy_proxy.py","sha256":"eb2e30b3fb480995562ebf966536cab279f1112f90f0f1db641920d6dcbed3fe","start":484},{"end":502,"path":"jiuwenbox/tests/integration/test_inference_privacy_proxy.py","sha256":"755efd326ccaf614945f525e972b7b861f7d8785b1a1ba86b1c65d949626710d","start":500}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
