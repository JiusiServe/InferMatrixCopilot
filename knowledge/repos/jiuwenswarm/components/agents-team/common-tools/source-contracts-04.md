---
title: "common-tools 源码接口与集成边界 04"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-tools 源码接口与集成边界 04

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f725b2986a1c1eeee2e840a625a2604e55d1bda35b7d063b377f3ae12ba07d9 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py`**

- 源码对模块职责的说明：Contact tools - 联系人工具.。
- 异步入口 `search_contact(name)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L1-L102)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e642fc08cd850bb7b5791e6c337db8d98cb42450339a80e4219d55459e9a4ed -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_tools.py`**

- 源码对模块职责的说明：File tools - 文件工具.。
- 异步入口 `search_file(query)`；声明返回 `Dict[str, Any]`。
- 异步入口 `upload_file(file_infos)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_tools.py#L1-L340)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da2a70ce66b1e49bf2f83400f784b38ee9a973e1c7a830e6868fee333f943286 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py`**

- 源码对模块职责的说明：OBS 上传辅助：prepare、upload、completeAndQuery 获取公网 URL.。
- `XiaoyiObsUploadConfig` 定义类型边界。
- 异步入口 `upload_local_file_public_url(session, config, file_path, object_type)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import os`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L1-L97)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/image_reading_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fcbe144cc20ee2e558340daeadf0180d2e106d52be277083d408c7f12fd9831f -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/image_reading_tool.py`**

- 源码对模块职责的说明：image_reading：。
- 异步入口 `image_reading(local_url, remote_url, prompt)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import tempfile`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/image_reading_tool.py#L1-L293)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f48fc0202aad35958cfafb75e2776859ae384e61cb828ecf3feaa6599aa2d34 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py`**

- 源码对模块职责的说明：Location tool - 获取手机当前定位.。
- 异步入口 `get_user_location()`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L1-L86)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/message_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73581785f2fb01ac88170fb8efa06ff21e545eb9c5f51cf7a8a2d8007987759d -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/message_tools.py`**

- 源码对模块职责的说明：Message tools - 短信/消息工具.。
- 异步入口 `send_message(phone_number, content)`；声明返回 `Dict[str, Any]`。
- 异步入口 `search_message(content)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict, Optional`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/message_tools.py#L1-L247)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0a938a7f6144b03215fe071d0bd26d87265a7300675a3b481811689a2b970b7 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py`**

- 源码对模块职责的说明：Note tools - 备忘录工具.。
- 异步入口 `create_note(title, content)`；声明返回 `Dict[str, Any]`。
- 异步入口 `search_notes(query)`；声明返回 `Dict[str, Any]`。
- 异步入口 `modify_note(entity_id, text)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any, Dict`；`from openjiuwen.core.foundation.tool import tool`；`from jiuwenswarm.common.utils import logger`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L1-L251)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e28379d5efef73b3d19ea7846370402ff819053cb02fd803eecb7c5576a3cc0 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py`**

- 源码对模块职责的说明：Phone tools - 电话工具.。
- 异步入口 `call_phone(phone_number, slot_id)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict, Optional`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L1-L113)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=566d74653dd162b82fa9abb94becfc9962fdbcb07e0ed17e200ac72d8acdde8b -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py`**

- 源码对模块职责的说明：Photo tools - 相册工具.。
- 异步入口 `search_photo_gallery(query)`；声明返回 `Dict[str, Any]`。
- 异步入口 `upload_photo(media_uris)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict, List, Union`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L1-L281)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e5e81d6c19159fb75110aaf97135cacfbfd8971ddfdd3c91d97542580d6f62b8 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py`**

- 源码对模块职责的说明：Push result tool - 查看推送记录工具.。
- 调用入口 `view_push_result(keywords, limit)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict, Optional`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L1-L152)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b9bc057ba6027e44423cf53ef033154e244262dfb865260021a700324d201a4 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py`**

- 源码对模块职责的说明：PushData 持久化管理器.。
- 调用入口 `save_push_data(data_detail)`；声明返回 `str`。
- 调用入口 `search_push_data(keywords)`；声明返回 `List[Dict[str, str]]`。
- 调用入口 `get_all_push_data()`；声明返回 `List[Dict[str, str]]`。
- 调用入口 `clear_all_push_data()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import uuid`。
- 模块级配置或常量名称：`PUSHDATA_FILE`, `MAX_PUSHDATA_ITEMS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L1-L147)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d87f88b533b1183500c0b01e2e40f595904e8bc47081a631b5b53977b9848638 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py`**

- 源码对模块职责的说明：Save tools - 保存到手机工具.。
- 异步入口 `save_media_to_gallery(url, media_type, file_name)`；声明返回 `Dict[str, Any]`。
- 异步入口 `save_file_to_file_manager(file_name, url, suffix)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`from typing import Any, Dict, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L1-L277)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e2a52f5aa1c95a237e1b71919d38ceb0acc5bebf527e907cf393a4f6a0a66885 -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py`**

- 源码对模块职责的说明：Timestamp tool - 时间戳转换工具.。
- 调用入口 `convert_timestamp_to_utc8_time(timestamp)`；声明返回 `dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from datetime import datetime, timedelta, timezone`；`from openjiuwen.core.foundation.tool import tool`；`from jiuwenswarm.common.utils import logger`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_gui_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf2fc4eaf5ed1c3f48bd6f7ed7ddf452b9e2b8e8b283cefdf8bceb277d86eb0b -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_gui_tool.py`**

- 源码对模块职责的说明：小艺 GUI 自动化（xiaoyi_gui_agent）：通过 InvokeJarvisGUIAgent 与设备协同完成屏幕操作.。
- 异步入口 `xiaoyi_gui_agent(query)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import time`；`import uuid`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_gui_tool.py#L1-L167)。
<!-- /kb:file -->
