# Personal-Agent RFC 服务部署与回滚

这是可移植 RFC 服务的首个实例。部署地址为
`https://world-model.43.155.186.30.nip.io/roadmap`，RFC 状态与旧的性能观察服务分开。
服务不要求 vLLM-Omni 的知识适配器；仓库授权后即可导入其他 RFC。

## 运行配置

- 独立 Python 3.12 环境：`/home/ubuntu/world-model/rfc-service/venv`。
- SQLite 工作空间：`/home/ubuntu/world-model/data/rfc-service`。
- 提供方配置：`/home/ubuntu/world-model/rfc-service/config.json`。
- systemd 服务：`infermatrix-rfc.service`，监听 `127.0.0.1:8792`。
- Caddy 代理 `/roadmap*`、`/api/roadmap*`、`/api/v1/*` 和前端资源。
- 旧 Node 服务仍处理性能观察页面，其旧 RFC 数据接口在部署切换后拒绝访问。

平台令牌只配置在部署端的受保护环境文件中。浏览器使用个人令牌换取
HttpOnly、Secure、SameSite 会话，API/MCP 使用个人 Bearer 令牌。
个人管理凭据位于操作者的配置目录，不属于服务数据库或发布的静态目录。
数据库保存令牌哈希；凭据文件只供操作者取得首次签发的令牌并配置客户端。

## 比较与切换

1. 导入原始 Markdown，保留正文和稳定标识，以配套元数据表达跟踪状态。
2. 使用 `migrate-personal-agent` 比较正文、特性 ID 与旧记录计数。
3. 使用 `--apply` 前自动备份目标 SQLite；旧数据库与静态资源另存完整备份。
4. 停止旧 roadmap timer/path 和正在执行的发布任务后，指定新工作空间为写入方。
5. 明确纳管并刷新来源，验证授权页面、API、导出和旧入口。

旧浏览器填写的用户名只迁入 `historical_claims`，不会成为已认证身份。
旧发现的拒绝与人工删除意图保留。PR 合并只表示实现事实；验收仍要求维护者
确认版本、环境和证据。来源不可用时保持上次核验结果及时间，不生成进展。

后台每 30 秒处理队列，每个 RFC 默认每小时核验和发现一次。后台委托绑定
纳管用户的有效凭据与当前权限；凭据过期、撤销或角色被收回时，状态为
`requires_reauthorization`，维护者须重新纳管。普通用户不需要部署端平台令牌。

聊天通过独立 Zcode GLM-5.3-Flash 队列运行，服务最多两轮并发；对话按用户、仓库和
RFC 隔离。确认提案后先保存候选，再为已有来源排队 `rfcs.update_source`；来源冲突
或失败不会丢弃候选，重新审阅同时显示当前来源与候选版本的差异。来源更新未确认时
普通核验保留候选正文，关联 PR 的状态仍可刷新。`wm-7074` 上线回归只读取页面，
真实模型和来源写回使用专用测试 RFC。

## 回滚

先停止 `infermatrix-rfc.service` 和其他前台 worker，检查 pending/running/uncertain
来源操作是否已经对外写入。用 SQLite backup API 保存当前数据库，再回滚程序和配置；
新增聊天表、会话、提案和已保存候选应保留。出现来源写回后不能盲目恢复较早数据库，
需要先核对远端结果和本地操作记录。仅无后续写入的初次迁移可直接恢复迁移生成的
`backup_path`。不要直接覆盖仍有写入进程的 SQLite/WAL 文件。
机器迁移或从备份恢复时，先停止旧写入方；数据库的 workspace ID 会保留，
复制数据库并同时启动两个独立部署不属于允许的写入拓扑。

若需恢复旧跟踪任务，先将新实例设为只读并停止其 worker，然后恢复备份的
timer/path 配置。保留 RFC 的授权代理和旧 Node 接口拒绝规则，避免恢复公开的
旧认领接口或静态快照。完整旧资源位于部署时建立的受保护备份目录。

其他机器使用 `infermatrix-rfc serve` 或 `sync --watch` 即可；systemd 是该部署的
运行包装。Windows/macOS/Linux 的路径与 SQLite 并发契约由
`rfc-portability.yml` 的多系统检查覆盖，远端离线不会切换到另一套本地状态。
