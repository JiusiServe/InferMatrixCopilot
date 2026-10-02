---
title: "单机多实例：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/config.py:L141-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/config.py:L183-L188, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/bootstrap.py:L139-L202, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/status.py:L261-L294, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/bootstrap.py:L172-L202, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/instance_manager/bootstrap.py:L93-L120]
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
