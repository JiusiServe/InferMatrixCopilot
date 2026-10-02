---
title: "初始化与服务启动：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/init_workspace.py:L154-L173, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_init_workspace.py:L54-L177, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/init_workspace.py:L44-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1674-L1677, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L378-L394, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/init_workspace.py:L63-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/init_workspace.py:L26-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/init_workspace.py:L100-L144]
feature: "bootstrap"
entry_points: ["jiuwenswarm/init_workspace.py"]
source_globs: ["jiuwenswarm/init_workspace.py"]
---

# 初始化与服务启动：实现深读

[功能概览](feature-bootstrap.md) · [owner 入口](_index.md)

<!-- kb:depth feature=bootstrap facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d7a1f45af0e2a80a0c000b22c455e9c5cdb39ce45690bf684134cc42e419ecd -->
**run_init 的返回值契约**
run_init(force, name) 返回 int：实例名校验失败（56-61 行）、实例运行中、或 init_user_workspace 返回 "cancelled"（146-147 行，含用户拒绝确认和语言选择取消——utils.py 1674-1677 行 lang 为 None 也返回 "cancelled"）时返回 1；命名实例初始化成功在 143-144 行返回 0。调用方 main() 原样返回该值（173 行），未展示的行不能证明它成为进程退出码。

来源：[jiuwenswarm/init_workspace.py:L44–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/init_workspace.py#L44-L151), [jiuwenswarm/common/utils.py:L1674–L1677](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L1674-L1677)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/init_workspace.py","start":44,"end":151,"sha256":"a09b080b83575c624a998c3d0bc5173f55858e388b6ebd99c593705bd18e3c38"},{"path":"jiuwenswarm/common/utils.py","start":1674,"end":1677,"sha256":"2655f36e774d48b4753f96c23342e9a33ed0a40bbc785c9f3721a643f6431d57"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=bootstrap facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40927c1efc2c849c32192a9e8a0e11199e0c7832a8fe8ce69cf01e71d8eb2e6e -->
**JIUWENSWARM_HOME 与默认工作区路径**
默认工作区是 get_user_home() / ".jiuwenswarm"（init_workspace.py 68-69 行）。get_user_home 的优先级是：缓存的 _user_home 首先命中，其次 JIUWENSWARM_HOME 环境变量，最后 Path.home()（utils.py 386-394 行）。因此一旦模块内已缓存 _user_home，之后设置 JIUWENSWARM_HOME 不会改变本次返回值。

来源：[jiuwenswarm/common/utils.py:L378–L394](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L378-L394), [jiuwenswarm/init_workspace.py:L63–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/init_workspace.py#L63-L71)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/utils.py","start":378,"end":394,"sha256":"ffcb431bf29371fccab86de7594eab6d898545428fa7b427bb27489f70ec872b"},{"path":"jiuwenswarm/init_workspace.py","start":63,"end":71,"sha256":"60b7f6724bc9782d432d3e9a756ad8f7e09abf9fc97be3fe7310eac0bc427aba"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=bootstrap facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc2b3ff3e13fd56def629e752a9161d2cd345d177d853f8c75fa0beb3c632d05 -->
**parse_known_args 的取舍**
设计推断（非作者历史意图）：

main() 用 parse_known_args 而非 parse_args，源码注释说明这是为了让 main() 在 pytest（sys.argv 残留测试路径）下不因未知参数 SystemExit。推断（inference）：代价是真实命令行上的拼写错误参数（如 --nmae）会被静默忽略，以默认值继续执行而非报错。

来源：[jiuwenswarm/init_workspace.py:L154–L173](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/init_workspace.py#L154-L173)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/init_workspace.py","start":154,"end":173,"sha256":"5d395f1ebf980b618e14c76438c1a9431c9fbb1734d74d773c80f20f005d7422"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=bootstrap facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=598a8f2cbc9b866b606edba6d571156d652a10f2db7270ae90db975e972d8028 -->
**语言选择与默认值的系统测试**
tests/system_tests/test_init_workspace.py 的 TestPromptPreferredLanguage 通过 monkeypatch 模拟输入断言：选 "1"/"zh" 得 "zh"、"2"/"en" 得 "en"，输入 no/n/q/invalid 返回 None；TestResolvePreferredLanguage.test_resolve_default_to_zh 断言无配置文件时语言默认 "zh"。这是对初始化语言交互契约的断言记录，不证明当前已运行通过。

来源：[tests/system_tests/test_init_workspace.py:L54–L177](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/system_tests/test_init_workspace.py#L54-L177)

<!-- kb:depth-proof {"evidence":[{"path":"tests/system_tests/test_init_workspace.py","start":54,"end":177,"sha256":"4eff8ab35147a389b2a4139d1a2a142afa2fdf9465af10e63fcd3076b13f894b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=bootstrap facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c1b7c311b07b519aa12e39b4492ce8ae2dd565f518f4e3a519d4c44ba3823cc7 -->
**命名实例初始化对 instance_manager 端口预留的依赖**
run_init 的命名实例分支直接复用 jiuwenswarm.instance_manager（27-41 行导入）：get_instance_index/calculate_instance_ports 算出本组端口后逐一 is_port_available("127.0.0.1", p) 检测（110-113 行），有冲突时先 collect_all_ports(exclude_name=name) 排除兄弟实例，再 find_available_ports(base_index=index, scan_range=20, exclude_ports=...) 向上扫描（117-123 行），最后 update_instances_yaml + create_bootstrap_env 落盘（138、141 行）。源码注释（106-109 行）说明目的：让实例创建后立即可启动，否则首次 jiuwenswarm-start --name 会撞端口并退回启动时兜底。

来源：[jiuwenswarm/init_workspace.py:L26–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/init_workspace.py#L26-L41), [jiuwenswarm/init_workspace.py:L100–L144](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/init_workspace.py#L100-L144)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":41,"path":"jiuwenswarm/init_workspace.py","sha256":"8d1f57776977744471c0ce09c29c2c180743c7c42068ce1fd37a877d87f76910","start":26},{"end":144,"path":"jiuwenswarm/init_workspace.py","sha256":"f04b26b2735fdbcd3d3ceef7a869846cdb201e1c0fd249d51095a63a88830c2b","start":100}],"trace":[]} -->
<!-- /kb:depth -->
