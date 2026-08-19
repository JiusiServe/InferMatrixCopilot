# 已有 model：复制一条规则

适用于 HunyuanImage3、Cosmos3、Qwen3-TTS 等单模型 owner。

## 直接照做

1. 打开 `knowledge/repos/vllm-omni/models/<模型>/rules.md`。
2. 复制该文件最后一条现有规则到末尾。
3. 修改 ID、标题、触发、必须/强制、禁止、验收和来源。
4. 修改文件顶部的 `updated` 和 `sources`。

不要把模型专有规则写进共享 component。

如果文件没有现成规则，复制下面这段：

```markdown
## <MODEL 前缀的新 ID> — <一句话标题>

- 触发：<修改该模型的 prompt、checkpoint、processor、stage 交接或输出时>
- 必须：<必须保持的模型专有合同>
- 禁止：<不能用哪个共享默认值、mock 或其他模型行为代替>
- 验收：<真实 checkpoint、processor、公开入口或基线> ^[<来源>]
```

## 完整改写样本

```markdown
## HY3-NEXT — checkpoint 对齐必须使用真实 key 集合

- 触发：修改 HunyuanImage3 的权重映射、rename 或加载兼容逻辑。
- 必须：用受支持 checkpoint 的真实 key 集合核对映射前后覆盖率。
- 禁止：只用手写 mock 字典证明加载逻辑正确。
- 验收：至少一个受支持 checkpoint 完成 key dry-run，未知 key 明确失败且没有静默丢失。 ^[PR #<编号>]
```

`NEXT` 必须换成该模型当前未使用的下一个 ID。

文件顶部同时更新：

```yaml
updated: <今天的 YYYY-MM-DD>
sources: [<保留旧来源>, <新增源码路径、设计文档或 PR URL>]
```

同一规则有多个来源时写在一个标记里：

```markdown
^[PR #1234; vllm_omni/diffusion/models/<model>/]
```

没有可核对来源时先补证据。已有目录和 `rules.md` 时，不创建第二份文件，也不修改
`_index.md`。

## 提交前复制

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
git diff --check
```

Windows 上 `LF will be replaced by CRLF` 只是换行符提醒，不是失败。
