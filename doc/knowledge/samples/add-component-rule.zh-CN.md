# 已有 component：复制一条规则

适用于 Configuration、Scheduler、Diffusion、Serving、Model Executor 等共享模块。

## 直接照做

1. 打开 `knowledge/repos/vllm-omni/components/<模块>/rules.md`。
2. 复制该文件最后一条现有规则到末尾。
3. 修改 ID、标题、触发、必须/强制、禁止、验收和来源。
4. 修改文件顶部的 `updated` 和 `sources`。

复制同文件现有规则，可以自动沿用正确的 `##`/`###` 层级和措辞。

如果文件没有现成规则，复制下面这段：

```markdown
### <COMPONENT 前缀的新 ID> — <一句话标题>

- 触发：<什么字段、入口、数据流或故障会触发这条规则>
- 必须：<实现或审核时必须完成什么>
- 禁止：<不能再接受的做法>
- 验收：<真实入口、consumer、测试或运行结果怎样证明完成> ^[<来源>]
```

## 完整改写样本

```markdown
### CONF-NEXT — 新配置字段必须到达真实 consumer

- 触发：新增或转发 deploy、CLI、stage config 字段。
- 必须：从公开入口跟踪字段经过归一化和构造，直到第一位真实 consumer。
- 禁止：只证明 parser、dataclass 或中间字典保存了字段。
- 验收：一个非默认值通过生产构造路径到达 consumer，同时未知字段仍然失败。 ^[PR #<编号>]
```

`NEXT` 必须换成当前未使用的下一个 ID。

文件顶部同时更新：

```yaml
updated: <今天的 YYYY-MM-DD>
sources: [<保留旧来源>, <新增源码路径、设计文档或 PR URL>]
```

同一规则有多个来源时写在一个标记里，用分号分隔：

```markdown
^[PR #1234; vllm_omni/path/to/file.py]
```

没有可核对来源时不要编造，也不要提交规则。已有 `_index.md` 已链接此
`rules.md` 时，不需要修改索引。

## 提交前复制

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
git diff --check
```

Windows 上 `LF will be replaced by CRLF` 只是换行符提醒，不是失败。
