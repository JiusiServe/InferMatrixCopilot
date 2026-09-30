# profiles/establish.py —— 规范

<!-- verified-against: 2026-09-30 -->

`LOC ~180 · profile（Stage 0–1.5 helper） · refactor-status: ok`

## 职责
确定性的建立期 helper。

## 公开契约
`fact_id`、`build_doc_corpus`、`is_redundant`、`extract_directives`、
`scan_modules`、`scan_modules_at_depth`、`normalize_root`、`ROOT_MODULE`、`HUMAN_DOC_NAMES`、`doc_files`。

## 不变量
- `is_redundant`（对 README+docs 做 6 词 shingle）会丢弃任何**仓库自己的文档已经写过**
  的 briefing 行（ETH 研究那条规则，**D5**）。
- `scan_modules` 是确定性的、按语言索引的，跳过非代码目录。
- `extract_directives` 限制行长（只收短祈使句）。
- `scan_modules_at_depth`（kb init 的模块定义）：源根以下至多 `depth` 层目录为模块，更深的文件归最深的那层祖先；
  非空行少于 `min_loc` 的模块由深到浅折入父目录模块，直到稳定；源根永不折叠（`normalize_root` 先把 `.`、`./pkg`、`/pkg/` 等写法规范化，仓库根为 `""` 且包含其他根，保证折叠必然终止）；嵌套源根各自拥有自己的文件；
  每一层都跳过隐藏目录与非代码目录；`exclude` 按仓库相对路径做 fnmatch；未知语言返回 `{}`；结果确定、有序。
- `build_doc_corpus(..., globs=None)`：不给 `globs` 时语料与原来完全相同（README* + docs/**/*.md）；给出时读
  `doc_files(repo, globs)` —— 按 glob 顺序、再按路径排序，每个文件只读一次，只收普通文件，解析后逃出仓库的
  符号链接一律跳过。kb init 用它按 adapter 的 `doc_globs` 建 D5 语料，归一化与 briefing 路径是同一份。

## 边界 —— 不属于这里
纯确定性 helper —— 不含 LLM、不写 store、不含 step 逻辑。

## 依赖（允许）
仅 stdlib。

## 测试
`test_profile_steps.py`（冗余过滤、模块扫描、指令抽取）；`test_kb_init_coverage.py`（按深度的模块扫描）；`test_kb_init_skeleton.py`（`doc_files` 与带 `globs` 的语料）。

## 重构备注
纯函数 —— 易测、易复用。冗余过滤器是承载 ETH 研究结论的关键防线；**保持它确定性**。

## 精简 —— **K2**（共享语言规则）—— 已完成
本模块曾经拥有 `LANGUAGE_SUFFIXES`，那是按语言规则集的三份副本之一
（另两份在 `review._sweep_targets` 和 `repo_map`）。数据现在住在叶子模块
`profiles/languages.py`，藏在小访问器（`suffixes` / `symbol_re` / `sweep_re`）
之后并从那里消费；这个符号已从本模块的公开契约中消失。按设计保留的一点：
**未知语言产出空的模块扫描，而不是猜测**。
