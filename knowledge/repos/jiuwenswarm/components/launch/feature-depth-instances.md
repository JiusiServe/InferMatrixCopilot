---
title: "单机多实例：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/config.py:L141-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/config.py:L183-L188, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/bootstrap.py:L139-L202, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/status.py:L261-L294, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/bootstrap.py:L172-L202, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/bootstrap.py:L93-L120, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_desktop_port_resolve.py:L223-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/config.py:L78-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/yaml.py:L54-L75, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/config.py:L33-L35]
feature: "instances"
entry_points: ["jiuwenswarm/instance_manager/bootstrap.py"]
source_globs: ["jiuwenswarm/instance_manager/bootstrap.py", "jiuwenswarm/instance_manager/*.py"]
---

# 单机多实例：实现深读

[功能概览](feature-instances.md) · [owner 入口](_index.md)

<!-- kb:depth feature=instances facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=91e473888158f318118737ce68c713e5e995e3881e52dcb7d4bdba59b4a0002e -->
**load_instance_bootstrap_by_name 的返回契约**
输入实例名，成功时返回 .env 路径并以 override=True 调用 load_dotenv 注入环境；实例名校验失败、instances.yaml 中不存在或工作区目录缺失时记录错误并返回 None，调用方需自行处理 None。

来源：[jiuwenswarm/instance_manager/bootstrap.py:L172–L202](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/bootstrap.py#L172-L202)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/instance_manager/bootstrap.py","start":172,"end":202,"sha256":"112cee8d657fac5b5bd46435081e7e5b737bde11c32e07298a9f34dcc1445da5"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=instances facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39b55241349614b56e8bc8c873797d8338fec14bd357c225f48828fb573bd4d7 -->
**端口基准的环境变量覆盖与分配公式**
实例端口 = 基准端口 + index × 1000（calculate_instance_ports）。基准优先取 JIUWENSWARM_<TYPE>_PORT 环境变量（PORT_ENV_OVERRIDES，供 Docker 场景），解析失败的非法整数值仅记 debug 日志后忽略，回落到静态 BASE_PORTS，未知端口类型再回落 10000。

来源：[jiuwenswarm/instance_manager/config.py:L141–L159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/config.py#L141-L159), [jiuwenswarm/instance_manager/config.py:L183–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/config.py#L183-L188)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/instance_manager/config.py","start":141,"end":159,"sha256":"bfe6b0eac6cf798f8111ed0155a7583dff1f8cc8253765e3b3415a1a33c3e664"},{"path":"jiuwenswarm/instance_manager/config.py","start":183,"end":188,"sha256":"1ee582140d85e2d82eb1ef421a01e0ecb4fd6aa2166ee1bca225aeae146b3502"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=instances facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c332503f65f7488a00774b87cf2ba8cab5b91a2a912d1487bc7d3a9298c47eeb -->
**bootstrap 依赖 status.get_instance_config 读取 instances.yaml**
load_instance_bootstrap_by_name 通过 get_instance_config(name) 从 instances.yaml 取得 workspace（未配置则用 get_instance_workspace_path 推导）和端口（未配置则 compute_auto_port 按声明顺序 index 自动计算），随后才能定位或重建 .env；instances.yaml 的条目顺序因此直接影响自动端口结果。

来源：[jiuwenswarm/instance_manager/bootstrap.py:L139–L202](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/bootstrap.py#L139-L202), [jiuwenswarm/instance_manager/status.py:L261–L294](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/status.py#L261-L294)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/instance_manager/bootstrap.py","start":139,"end":202,"sha256":"864d44675dc7673bf893b85439c0ba6bd8dccbd4622f23c9b717b836ecdf85f3"},{"path":"jiuwenswarm/instance_manager/status.py","start":261,"end":294,"sha256":"b1294ee9b23ace29af61d07827c15151c859b48605c325fd3dbfe06345437ef7"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=instances facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83af498192037f475e60e40723a4ba436277eaaf1db85b7d6c2346b87a462d7b -->
**早期 bootstrap 生成复制端口公式的代价**
设计推断（非作者历史意图）：

推断：_create_basic_bootstrap_env 为满足“不得依赖任何 jiuwenswarm 模块”的早期解析约束，静态复制了 base + index×1000 的端口公式；代价是它直接用 BASE_PORTS，不像 calculate_instance_ports 那样经过 _resolved_base_port 支持 JIUWENSWARM_<TYPE>_PORT 覆盖，两条路径在设置了环境覆盖时会算出不同端口。

来源：[jiuwenswarm/instance_manager/bootstrap.py:L93–L120](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/bootstrap.py#L93-L120), [jiuwenswarm/instance_manager/config.py:L183–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/config.py#L183-L188)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/instance_manager/bootstrap.py","start":93,"end":120,"sha256":"52da6f6a5c18f4b75b54d3397c1e519e8d598d6cfe527420cd2dcca5704de83e"},{"path":"jiuwenswarm/instance_manager/config.py","start":183,"end":188,"sha256":"1ee582140d85e2d82eb1ef421a01e0ecb4fd6aa2166ee1bca225aeae146b3502"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=instances facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1fb650e43d2424a76c5b49021ed4a94b497b4e08dc0f97ac653d19d325042554 -->
**桌面端口组测试对 instance_manager 端口公式的断言**
tests/unit_tests/test_desktop_port_resolve.py:223-252 三个用例均 monkeypatch desktop_app.find_available_ports 后断言 resolve_desktop_ports：默认组等于 calculate_instance_ports(0) 且 frontend/web 端口与 instance_manager 的 BASE_PORTS 一致；回退组为 calculate_instance_ports(1)，即 BASE_PORTS 各 +1000；扫描返回 None 时抛 RuntimeError 匹配 'No available desktop port group'。这是对端口组公式消费端映射的断言记录，不证明当前已运行通过。

来源：[tests/unit_tests/test_desktop_port_resolve.py:L223–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_desktop_port_resolve.py#L223-L252)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":252,"path":"tests/unit_tests/test_desktop_port_resolve.py","sha256":"6219d27bbefa463eaa1223addefbdf678627f7f7613122075da9f3a7690ff2d3","start":223}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=instances facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d60ca5b9092a1cad0cc3e987f5194752d00c3217ae07767777b957437a240cc2 -->
**名称合法且实例、工作区均存在时：取或补建 workspace/.env 并以 override=True 加载后返回路径**
validate_instance_name 无错误、get_instance_config 非 None 且 workspace 存在时，env_path 取 config.get_bootstrap_env_path() 即 workspace/.env；文件不存在则 create_bootstrap_env 补建，load_dotenv(env_path, override=True) 覆盖加载，函数局部返回 env_path。

来源：[jiuwenswarm/instance_manager/bootstrap.py:L172–L202](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/bootstrap.py#L172-L202), [jiuwenswarm/instance_manager/config.py:L78–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/config.py#L78-L80)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":202,"path":"jiuwenswarm/instance_manager/bootstrap.py","sha256":"112cee8d657fac5b5bd46435081e7e5b737bde11c32e07298a9f34dcc1445da5","start":172},{"end":80,"path":"jiuwenswarm/instance_manager/config.py","sha256":"37fc528bc05807b90dede280e74a4a4bfa66232459717d4bf0d7e6a0369782fa","start":78}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=instances facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8947f19322cb611ebc96a8660fedc7c9222d9d590419af661ef3eeb960891314 -->
**instances.yaml 读/解析失败时 _read_yaml_file 转抛带修复建议的 InstancesYamlError**
读取抛 IOError 或 yaml.safe_load 抛 yaml.YAMLError 时，_read_yaml_file 在本地分支转抛 InstancesYamlError：消息含 Path 与修复建议（如 "Run 'jiuwenswarm-init' to recreate a valid template"），并以 from exc 链接原异常；构造器再统一加 "[instances.yaml] " 前缀后向调用方传播。

来源：[jiuwenswarm/instance_manager/yaml.py:L54–L75](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/yaml.py#L54-L75), [jiuwenswarm/instance_manager/config.py:L33–L35](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/config.py#L33-L35)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":75,"path":"jiuwenswarm/instance_manager/yaml.py","sha256":"e4c2ce3bb100e82c5043ee7fde2966caac0151cf9855c34adde7bf96c60c579a","start":54},{"end":35,"path":"jiuwenswarm/instance_manager/config.py","sha256":"79218ef78c40a7d7ce7b5d5ff061a43cfbb8a92d20eb11860dbc797bfa263cf2","start":33}],"trace":[]} -->
<!-- /kb:depth -->
