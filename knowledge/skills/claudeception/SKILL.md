---
name: claudeception
description: |
  把会话中的可复用经验和具体错题写回当前仓库的 framework/ 或 repos/。
  触发：/claudeception、用户要求“落盘/记住/写错题”，或一次复杂排障结束后。
  写入前先查重复，展示修改内容并得到用户确认；不生成新 skill。
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# Claudeception — 把经验写回知识目录

## 先判断放在哪里

1. 换到无关仓库仍然成立 → `framework/<主题>/`。
2. 依赖某个仓库的代码、命令或流程 → `repos/<仓库>/<主题>/`。
3. 根因属于多个模型共用的代码 → `repos/<仓库>/components/<模块>/`。
4. 根因只属于某个模型 → `repos/<仓库>/models/<模型>/`。
5. 当前机器地址、账号、cache 或 venv → ignored `local/`，不进入知识页面。

具体失败写到最近目录的 `incidents/`；稳定方法写到 guide、rules 或 architecture。归属规则见 [目录归属](../../contributing/layout.md)，复盘规则见 [复盘和错题](../../contributing/incidents.md)。

## 写之前

1. 从 `framework/_index.md` 和 `repos/_index.md` 找最近入口。
2. 用标题、错误签名和关键词全文搜索，确认没有重复正文。
3. 明确页面最终路径和需要更新的 `_index.md`。
4. 去掉私人 host、token、账号、私钥和用户绝对路径。

## 错题格式

按 [错题正文格式](../../contributing/incidents.md#正文模板) 编写，一篇只写一件事故。至少包含：

- 编号；
- 归属；
- 状态；
- 搜索词；
- 影响范围；
- 当时在做什么、现象、影响、原因、修复、验证和防复发。

根因没查清时状态写“待归类”或“处理中”，禁止把猜测伪装成结论。

## 稳定经验格式

普通 Markdown 即可，不要求 YAML。标题和正文要让人能直接搜索；在最近 `_index.md` 增加一行“遇到什么 → 查看哪里”。

如果经验来自一篇错题，在错题末尾增加“已提炼到”链接；稳定页面不复制完整事故经过。

## 写完必做

1. 更新当前目录 `_index.md`。
2. 如果新建了子目录，更新上一层 `_index.md`。
3. 修复所有相对链接。
4. 运行 `python tools/check_knowledge_tree.py`。
5. 同一类错误反复发生且需要每次开工拦截时：跨仓库都成立才建议升级到根 `CLAUDE.md`；只属于一个仓库则写入并链接 `repos/<仓库>/rules.md`。

## 不要

- 写入系统、全局或个人 memory。
- 建立 `_private/` 或第二套索引。
- 生成新 `SKILL.md`。
- 重复已有正文。
- 保存一次性聊天流水账、完整长日志或未经验证的猜测。
- 保存密码、真实 IP、账号、私钥或用户绝对路径。
