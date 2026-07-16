# vLLM-Omni 代码模块

| 代码模块 | 查看哪里 | 负责什么 |
|---|---|---|
| Diffusion | [diffusion](diffusion/_index.md) | 多模型共享的 diffusion pipeline、denoise 和执行机制 |
| Model Executor | [model-executor](model-executor/_index.md) | AR/LLM stage、stage config、并行与设备启动、输入处理和跨 stage 数据桥接 |
| Serving | [serving](serving/_index.md) | 用户入口、请求解析、在线服务和 engine 边界 |
