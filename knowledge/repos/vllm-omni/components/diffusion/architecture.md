# Diffusion 共享架构

## 负责什么

`vllm_omni/diffusion/` 承载 diffusion stage 的共享执行框架。它负责接收上游准备好的条件和 diffusion 配置，运行模型 pipeline 与 denoise 过程，并把生成结果交给后处理或下一阶段。

## 不负责什么

- 模型专有 transformer、tokenizer、VAE wrapper 和 checkpoint 兼容细节由对应模型目录说明。
- 请求字段怎样从 HTTP/CLI 进入系统由 serving 模块负责。
- AR/LLM stage 怎样产生跨阶段输入由 model-executor 负责。

## 调查顺序

1. 先确认问题是否同时影响多个 diffusion 模型。
2. 沿配置、runner、pipeline、denoise loop 和输出逐层查证。
3. 如果最终只在一个模型的 pipeline 或 checkpoint 上复现，把正文放回模型目录，并从这里链接。

源码会变化，具体类名和路径在改代码前必须以目标仓库当前版本为准。
