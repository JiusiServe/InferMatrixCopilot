# vLLM-Omni config audit 说人话规则

## 什么时候用

用户讨论 vLLM-Omni `config/deploy/pipeline/cli` cleanup、Unified `VllmOmniConfig`、diffusion config owner、deploy config / stage config 迁移时，先用会议室里所有人都能听懂的话解释问题，再补函数名和文件证据。

## 先说核心问题

不要先说“字段归属矩阵”“source of truth”“runtime payload”。

先说：

> 配置现在不是一个地方说了算，而是好几个地方都在改配置。

## 围绕五个问题展开

1. 入口太多。
   - 新入口是 `--deploy-config`。
   - 老入口是 `--stage-configs-path`。
   - 还有不传配置时的 diffusion fallback。

2. 默认 diffusion 配置有好几处在造。
   - factory 有逻辑。
   - engine 有逻辑。
   - CLI wrapper 也有逻辑。
   - 讲清楚问题是“以后默认值要改，到底改谁”。

3. 配置中途会被反复加工。
   - 用户写的配置不是直接拿去跑。
   - 中间会合并、转格式、补字段、规范化。
   - 所以光看 yaml 不知道最后 runtime 真正用了什么。

4. 新老配置路径混在一起。
   - `--deploy-config` 是新方向。
   - `--stage-configs-path` 还没死。
   - 文档里出现 stage config 不一定都是错的，要区分过时写法和 legacy-required。

5. 模型迁移和 runtime bugfix 容易混在一起。
   - pipeline registry 迁移应该讲 topology。
   - runtime bugfix 应该单独说明。
   - 不要让 reviewer 分不清这是配置清理还是模型行为修复。

## 术语必须翻译

- 字段归属 = 这个配置字段到底谁管。
- source of truth = 最终配置到底谁说了算。
- runtime config = 最后真正拿去跑的配置。
- topology = 模型有几个 stage、stage 怎么连。
- legacy-required = 现在还不能删，因为还有模型或测试真的靠它跑。

## P0 的人话表达

不要说“先产出字段归属矩阵”。

说：

> Stage 1 先不急着改代码。先搞清楚配置从哪里来、最后在哪里生效、哪些 legacy 还不能删。否则 cleanup 很容易删错字段，或者把模型运行行为改掉。

