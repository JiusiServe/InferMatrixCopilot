---
title: "Web 通道本机目录/可执行文件选择器（跨平台后端链）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L296-L309, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L427-L443, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L290-L295, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L339-L346, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L501-L520, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3603-L3620, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L415-L425, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/directory_picker.py:L355-L370, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_app_web_handlers.py:L484-L541]
feature: "web-native-directory-picker"
entry_points: ["jiuwenswarm/channels/web/directory_picker.py"]
source_globs: ["jiuwenswarm/channels/web/directory_picker.py"]
---

# Web 通道本机目录/可执行文件选择器（跨平台后端链）：实现深读

[功能概览](feature-web-native-directory-picker.md) · [owner 入口](_index.md)

<!-- kb:depth feature=web-native-directory-picker facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=caedc97902da9c6071897cfb80443f96b5f9928e6fbcab6a293f789de7639b89 -->
**select_file_native(*, initial_dir=None, title=None)：title 为 None 或全空白时回退 _FILE_DIALOG_TITLE，调用方自行校验文件可用性**
入口先经 _resolve_initial_dir 得到 start_dir；dialog_title 仅当传入的 title 是非空白字符串时取其 strip() 结果，否则用模块常量 _FILE_DIALOG_TITLE。随后按 sys.platform 分派：win32→_select_file_windows_tk，darwin→_select_file_macos，linux 前缀→_select_file_linux，其余平台直接抛 RuntimeError。docstring 明确调用方负责验证所选文件在其领域是否为可用可执行文件。

来源：[jiuwenswarm/channels/web/directory_picker.py:L501–L520](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L501-L520)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":520,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"2ffddda58c643a1c0aa0349820f25058de37b16eec66492510ff9507122ac5cc","start":501}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-native-directory-picker facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=07fbacf2c1a0ea1b19ea74db5e7b3346afdc669691376aa473ffc5d08745e0df -->
**tkinter 子进程用环境变量传参，initial 默认 ~，title 默认 Select Directory**
_try_tkinter_subprocess 通过 JIUWEN_DIR_PICKER_INITIAL 和 JIUWEN_DIR_PICKER_TITLE 环境变量传参；子进程内 initial 缺省为 expanduser("~")，title 缺省为 "Select Directory"。

来源：[jiuwenswarm/channels/web/directory_picker.py:L296–L309](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L296-L309)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":309,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"56effa58568f026a380491c69375e32ce010c66436dbbc4b0b25564b53b937b9","start":296}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-native-directory-picker facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ef623ba49bf3b27524429b5f086217293207f7329e5ac2f0f4f7bcbbaec3bc75 -->
**后端异常记录后继续；TimeoutExpired 立即中止；全部失败抛 RuntimeError**
循环中除 subprocess.TimeoutExpired（转为 RuntimeError "directory picker timed out" 并中止）外的异常记入 errors 并尝试下一 backend；全部失败时抛 RuntimeError，消息含各 backend 错误与 "fallback to typing an absolute path in the UI" 提示。

来源：[jiuwenswarm/channels/web/directory_picker.py:L427–L443](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L427-L443)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":443,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"659a0941eeec4cbb1562403c4399e8768fb38fec5d0076d5b41f895dfab5eaf4","start":427}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-native-directory-picker facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f25df9d0ca8974057143e7e58555b14bb0c8eab44f85668a21ab5d61116efc30 -->
**独立子进程跑 tkinter：换来线程安全，付出进程启动与 600s 超时代价**
设计推断（非作者历史意图）：

docstring 声明在独立子进程中运行 tkinter 以保证 Tk 位于该进程主线程、可从 asyncio.to_thread 工作线程安全调用（收益）；代价是每次选择都启动一个 Python 子进程，且受 timeout=600.0 约束（此为标注的实现内推断）。

来源：[jiuwenswarm/channels/web/directory_picker.py:L290–L295](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L290-L295), [jiuwenswarm/channels/web/directory_picker.py:L339–L346](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L339-L346)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":295,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"78fd2d2c3dbae335469b74a7160bd76a882411ea2bf41357d31ee5b143737569","start":290},{"end":346,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"5d32db974b70905020e8b6e84bbe480fac27ee22d9acd8a43ad50c1a36b2ee12","start":339}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-native-directory-picker facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=082f5c82eb2b84c8b8089e528faae2ac0bb5e7610c38b495af6f9f0e0303e4ac -->
**path.select_file 处理器经 asyncio.to_thread 调用 select_file_native，异常时回 UNSUPPORTED**
处理器先把 initial_dir 去空白；仅当 initial_path 是字符串且 strip() 后非空白时，用其 expanduser 后的父目录覆盖 resolved_initial_dir（L3604–L3605）。import 在 try 外，随后在 try 内用 asyncio.to_thread 调用 select_file_native 并传入 initial_dir 与 title；捕获任何 Exception 后记录 warning，并通过 channel.send_response 发送 ok=False、code="UNSUPPORTED" 的响应后返回。

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3603–L3620](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3603-L3620)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3620,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"16147ab2d9c928d8bf6add171ed2fc5a698cf9cf934f12f0903d40b55b6621a3","start":3603}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-native-directory-picker facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d84fcb6147bfe90c5e880359b2378de085f4c29dd690d1dc9857f6828e054ed -->
**Linux 目录后端链依赖 shutil.which 探测，tkinter 子进程后端始终追加**
_select_directory_linux 用 shutil.which 依次探测 zenity/kdialog/yad，探测到才加入后端列表，tkinter 子进程后端总是无条件追加（目录链 L415–L425）。tkinter 文件子进程后端复制 os.environ 并设置 JIUWEN_FILE_PICKER_INITIAL/JIUWEN_FILE_PICKER_TITLE 传参，docstring 说明 Tk 在独立进程的主线程创建（L355–L370）；未展示子进程启动代码本身。

来源：[jiuwenswarm/channels/web/directory_picker.py:L415–L425](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L415-L425), [jiuwenswarm/channels/web/directory_picker.py:L355–L370](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L355-L370)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":425,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"eb65ffb6ba3d9843ab732396665645c33141d2987c5382ae9b4215866ba4a2a0","start":415},{"end":370,"path":"jiuwenswarm/channels/web/directory_picker.py","sha256":"57f4f68aff32733282d532f11f8def9b7b7c3e6ca913fba1eeded0f0757e49c9","start":355}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-native-directory-picker facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bb07dee0e89be3fc12cb066b87fdb333c27b4763aeded06e43edc36fa98af907 -->
**单测用 monkeypatch 假体验证 path.select_file 的参数转发与取消/成功响应（未触真实 OS 对话框）**
test_path_select_file_returns_selected_path 将 select_file_native 替换为 fake，断言传入的 initial_dir 为 initial_path 的父目录、title 原样转发，且响应 payload 为 {"path": selected_path, "cancelled": False}（L484–L521）；test_path_select_file_returns_cancelled 将其替换为返回 None 的 lambda，断言 ok=True 且 payload 为 {"path": None, "cancelled": True}（L524–L541）。断言仅覆盖处理器对 fake 的转发，不执行真实本机选择器。

来源：[tests/unit_tests/gateway/test_app_web_handlers.py:L484–L541](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_app_web_handlers.py#L484-L541)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":541,"path":"tests/unit_tests/gateway/test_app_web_handlers.py","sha256":"73eef2010e7f22500eb61c80726bfed68ffa72b46009e3228bc04f1de4b7eacf","start":484}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
