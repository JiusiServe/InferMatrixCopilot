# Docstring 规范 —— infermatrix-copilot

本仓库的 docstring 约定，结构以 [PEP 257](https://peps.python.org/pep-0257/) 为准，
"写什么"以 [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
为准，再按本代码库"简洁、先讲理由"的语气做了调整。

**每个 module、class、function、method 都要有 docstring。** 它解释的是*逻辑*
（做什么，以及那些不显然的*为什么*）和*输入/输出* —— 而不是把签名再抄一遍。

## 形式（PEP 257）

- 三个双引号 `"""..."""`。module docstring 是文件的**第一条语句**
  （排在 `from __future__ import ...` 和所有 import 之前）。
- **摘要行**：一句祈使语气，≤ 约 88 列，以句号结尾。显然的情况下，摘要行本身就是
  整个 docstring（单行式）。
- 不平凡的情况：摘要行、空行、然后正文。
- 多行 docstring 的收尾 `"""` 单独占一行。

## 各类分别该写什么

- **Module** —— 这个文件独占的那一件事，加一行说明它导出什么。对于只做再导出的
  `__init__.py`，说明这个包聚合了什么、以及公开面是再导出的。
- **Class** —— 一行说清它的行为/角色；当不显然时，点出关键属性或它维持的不变量。
  `@dataclass` 的字段含义写在类 docstring 里（或用行内 `#` 注释），除非字段很多，
  否则不要单开 `Attributes` 段。
- **Function / method** —— 先摘要行为，再用**散文**写清 输入 → 输出 和那些不显然的
  逻辑。点名那些真正承载语义的参数，并说明返回值代表什么。只有参数很多、散文反而
  更难读时，才启用显式的 `Args:`/`Returns:` 段。

## 语气（与现有代码保持一致）

- **理由优先**：与其逐行复述代码已经写明的*做了什么*，不如解释*为什么*。当某个选择
  由设计或评测决定时，把它引出来（例如"single untooled reduction call: a
  tool-looped reducer over-dropped in live runs"）。
- 保留 SPEC 使用的那套安全/契约措辞：说明某个函数是不是 fail-closed 门、是否为后续
  step 发布状态（**B2**）、是否降级为类型化的 BLOCKED 结果、是否记录 `capability_gap`。
- **不要编造行为。** 拿不准某个分支做什么时，就按代码能支撑的粒度描述 —— 绝不猜测
  代码里并不存在的具体量（行号、阈值）。

## 示例（取自本仓库）

Function —— 输入 → 输出 + 为什么：

```python
def guard_push(policy: PushPolicy, protected_branches: list[str]) -> PushDecision:
    """Authorize a push: allow only when `policy.allowed` AND the target branch
    is not in `protected_branches`. Returns a PushDecision carrying the concrete
    git command (never run here) or a deny reason — the single C4 choke point, so
    every push path is authorized in one place."""
```

Class —— 角色 + 关键属性：

```python
class StepResult:
    """The outcome of one step: `ok` plus, on failure, a typed `failure_kind`
    (drives the engine's retry/replan/escalate branch) and the `state_updates`
    a later step consumes. Never raises across the step boundary — failures are
    values, not exceptions."""
```

只做再导出的 `__init__.py`：

```python
"""Review subsystem: diff summarization, trigger evaluation, and the patch/plan
reviewers. Re-exports the public surface (`build_diff_summary`, `ReviewVerdict`,
`run_patch_review`) so callers import from the package, not its modules."""
```

> 示例里的 docstring 保持英文原样 —— **代码内的 docstring 依然用英文写**，本页统一
> 中文说的是这份规范文档本身，不是被规范的对象。

## 不要这样做

- 不要给平凡的访问器套上 `Args:`/`Returns:`/`Raises:` 脚手架 —— 单行式才是正确的，
  也是 PEP 257 所偏好的。
- 补写新 docstring 时，**不要**顺手改代码、改签名，或改动已有的（正确的）docstring。
  docstring 是**追加式**的。
- 不要复述逐文件 SPEC —— docstring 是代码内的局部视角，SPEC 才是规范性契约。
