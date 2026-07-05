# Python Agent 应用落地阶段拆解

**文档标识：** `PHASES-2026-07-05-python-agent-application`

**文档类型：** 总体设计的阶段拆解。

**上游来源：**

- `SPEC-2026-07-05-python-agent-application-design`
- 文件：`docs/superpowers/specs/2026-07-05-python-agent-application-design.md`

**下游计划：**

- 阶段 1 执行计划：
  `docs/superpowers/plans/2026-07-05-agent-runtime-execution-loop.md`

**文档作用：** 把总体架构设计拆成可逐步落地、可分别生成 plan、可独立验收的阶段。

**引用关系：**

```text
SPEC 总体设计
  -> PHASES 当前文档：落地阶段拆解
    -> PLAN 阶段执行计划
```

**当前执行状态：**

- 阶段 0：项目骨架与工程基线，基本已完成。
- 阶段 1：Agent Runtime 最小执行内核，已完成。
- 阶段 2：Model Adapter 与真实 LLM 接入，下一步建议展开执行计划。
- 阶段 3 及以后：暂未展开执行计划。

**拆解原则：**

- 先做能跑起来的最小内核，再接真实模型和基础设施。
- 每个阶段都要产出可测试的软件状态，不只产出目录或抽象。
- Runtime、Model、Tool、Memory、Storage、Worker、Observability 分阶段推进，避免一次性平台化。
- 阶段之间允许重叠演进，但每个阶段都要有明确边界和验收标准。

---

## 阶段 0：项目骨架与工程基线

**定位：** 把 Python/FastAPI 单体应用的工程底座搭好。

**对应设计文档：**

- `0. 一页结论`
- `6. 推荐技术选型`
- `7. 推荐项目目录`

**当前状态：** 基本已完成。

**范围：**

- FastAPI 应用入口。
- 健康检查接口。
- 配置加载。
- JSON 行日志。
- 基础目录边界。
- Dockerfile 和 docker-compose。
- Ruff、mypy、pytest、`make check`。

**验收标准：**

- `GET /health` 可用。
- `make check` 可以运行。
- 项目目录已经按 API、Agent、Model、Tool、Memory、Storage、Observability、Security 分层。

**后续 plan：** 已完成则不需要单独生成；如果要补齐工程基线，可以单独生成“工程基线完善计划”。

---

## 阶段 1：Agent Runtime 最小执行内核

**定位：** 先把 Agent 的执行协议跑通，而不是先接真实模型或数据库。

**对应设计文档：**

- `3.2 第三层：Agent Runtime 层`
- `4.1 同步问答链路`
- `5.1 Agent Runtime 内部模块`
- `10. 观测与评测`

**范围：**

- Run/Step 显式建模。
- Planner 返回结构化动作。
- Runtime 执行循环。
- 本地 Tool Registry + Tool Executor 闭环。
- Policy 基础检查。
- token 使用量近似统计。
- 失败状态和 `max_steps` 终止保护。

**暂不做：**

- 真实 LLM。
- 数据库持久化。
- RAG。
- 异步 Worker。
- 审批流。
- Artifact 文件管理。

**验收标准：**

- 普通输入能返回最终回答。
- Planner 能触发本地工具调用。
- Runtime 能记录 steps。
- Runtime 能返回 token usage。
- 未知工具和超过最大步数能返回结构化失败结果。

**已生成 plan：**

- `docs/superpowers/plans/2026-07-05-agent-runtime-execution-loop.md`

**当前状态：** 已完成。

---

## 阶段 2：Model Adapter 与真实 LLM 接入

**定位：** 把真实模型接进来，但不能让 Runtime 直接耦合模型厂商 SDK。

**对应设计文档：**

- `2. 设计原则` 里的“模型解耦”
- `3.2 第四层：能力层`
- `6. 推荐技术选型`

**范围：**

- 完善 `LLMClient` / `ChatModel` 协议。
- 定义模型请求、响应、usage 数据契约。
- 实现至少一个真实模型 Adapter。
- 增加模型错误、超时、重试边界。
- 将 provider 返回的真实 token usage 接入 `TokenUsage`。
- 支持通过配置切换 Echo、本地测试模型和真实模型。

**暂不做：**

- 多模型复杂路由。
- 成本预算策略。
- 模型评测平台。

**验收标准：**

- Runtime 不直接 import 模型厂商 SDK。
- 至少一个真实模型可以被 Planner 或 Model Adapter 调用。
- token usage 优先使用 provider 返回的真实值。
- 模型调用失败能转换成结构化错误。

**建议后续 plan：**

- `2026-07-05-model-adapter-llm-integration.md`

---

## 阶段 3：状态持久化与会话管理

**定位：** 让 Run、Session、Message、Step 能跨请求保存、查询和回放。

**对应设计文档：**

- `1.1 要解决什么问题`
- `3.2 第五层：基础设施层`
- `5.3 Memory 模块`
- `10. 观测与评测`

**范围：**

- Session 模型。
- Run Repository 接口。
- Step Repository 接口。
- Message Repository 接口。
- Postgres/SQLAlchemy 或 SQLModel 适配器。
- Run 查询 API。
- Memory 从纯内存实现演进到可持久化实现。

**暂不做：**

- 完整 RAG。
- 异步 Worker。
- 多租户复杂权限。

**验收标准：**

- 能创建 Run。
- 能查询 Run 状态和 steps。
- 能查询某个 session 的消息历史。
- Runtime 依赖 Repository 接口，不依赖具体数据库实现。

**建议后续 plan：**

- `2026-07-05-run-session-persistence.md`

---

## 阶段 4：API 层与流式输出

**定位：** 把 Runtime 能力暴露成稳定 API，并让客户端能观察执行过程。

**对应设计文档：**

- `3.2 第二层：接入层`
- `4.1 同步问答链路`
- `4.2 长任务链路`

**范围：**

- `POST /agent/runs`
- `GET /agent/runs/{run_id}`
- `GET /agent/runs/{run_id}/events`，优先 SSE。
- API 请求/响应 Schema。
- API 错误码和异常转换。
- 路由只做校验、调用应用服务、返回响应。

**暂不做：**

- Web 前端。
- WebSocket 双向交互。
- 完整长任务队列。

**验收标准：**

- 可以通过 API 创建 Run。
- 可以通过 API 查询 Run 状态。
- Runtime 执行过程可以通过 SSE 或事件接口被观察。
- API 层没有承载复杂业务逻辑。

**建议后续 plan：**

- `2026-07-05-agent-run-api-and-events.md`

---

## 阶段 5：Memory/RAG

**定位：** 把短期上下文、长期记忆和文档检索拆清楚。

**对应设计文档：**

- `5.3 Memory 模块`
- `8.1 第一阶段：最小可用版本`

**范围：**

- Short-term Memory 持久化。
- Long-term Memory 接口。
- Retrieval Memory 接口。
- 文档切分、索引、检索。
- 检索结果注入 Planner/Model 上下文。
- 最小知识库问答链路。

**暂不做：**

- 大规模知识库治理。
- 复杂召回排序。
- 多租户知识隔离。

**验收标准：**

- 聊天历史不被当成长期知识库滥用。
- RAG 只通过明确的 Retrieval 接口进入 Runtime。
- 可以测试“不命中知识”和“命中知识”两类场景。

**建议后续 plan：**

- `2026-07-05-memory-rag-minimum-loop.md`

---

## 阶段 6：异步 Worker、审批与高风险工具治理

**定位：** 把长任务和高风险工具从同步 API 链路中拆出来。

**对应设计文档：**

- `4.2 长任务链路`
- `4.3 人工介入链路`
- `9. 安全与治理`

**范围：**

- Worker 任务入口。
- 长任务 Run 状态流转。
- 高风险工具 Policy。
- Approval 记录。
- 人工通过/拒绝后的恢复或终止。
- 沙箱/外部系统调用边界。

**暂不做：**

- 平台级多 Agent 协作。
- Tool Marketplace。
- 完整治理后台。

**验收标准：**

- 长任务不会阻塞 API 请求。
- 高风险工具默认不能绕过 Policy。
- 每次审批都有审计记录。
- 拒绝审批后 Runtime 能终止或改写计划。

**建议后续 plan：**

- `2026-07-05-worker-approval-governance.md`

---

## 阶段 7：Artifact、评测、成本与治理面板

**定位：** 让 Agent 的产物、质量、成本和审计信息可管理。

**对应设计文档：**

- `3.2 第四层：能力层`
- `10. 观测与评测`
- `8.2 第二阶段：标准生产版`

**范围：**

- Artifact Manager。
- 对象存储适配器。
- Trace / Metrics。
- token / cost 统计。
- 回放与评测数据。
- 管理 API 或内部面板。

**暂不做：**

- 多业务线平台化。
- Tool Marketplace。
- 灰度实验平台。

**验收标准：**

- 每次 Run 的产物可追踪。
- 可以按 Run 查看耗时、步骤、工具、token、失败原因。
- 可以做基础回放和质量评测。

**建议后续 plan：**

- `2026-07-05-artifact-evaluation-observability.md`

---

## 阶段 8：平台化能力

**定位：** 当单体边界和核心链路稳定后，再考虑平台化复用。

**对应设计文档：**

- `8.3 第三阶段：平台化版本`

**范围：**

- 多 Agent 协作。
- Workflow 编排。
- Tool Marketplace / Connector Center。
- 多租户治理。
- Prompt / Agent 版本管理。
- 灰度发布与实验评估。

**进入条件：**

- 阶段 1 到阶段 7 的核心链路已经稳定。
- 已经出现多个业务场景复用同一套 Runtime/Tool/Memory 能力。
- 过早平台化会明显拖慢当前产品验证时，不进入本阶段。

**验收标准：**

- 平台能力服务于已有业务复用，而不是为了抽象而抽象。
- 多租户、版本、工具治理有明确使用场景。

---

## 推荐执行顺序

1. 先执行阶段 1：Runtime 最小执行内核。
2. 再执行阶段 2：Model Adapter 与真实 LLM 接入。
3. 接着执行阶段 3：状态持久化与会话管理。
4. 然后执行阶段 4：API 层与流式输出。
5. 之后根据真实产品方向，在阶段 5 和阶段 6 中二选一优先：
   - 如果是知识问答产品，先做阶段 5。
   - 如果是任务执行产品，先做阶段 6。
6. 阶段 7 在有真实 Run 数据后做。
7. 阶段 8 只有在多个业务线复用时再做。

## Review 要点

- 阶段 1 是否足够小，能否作为第一个可执行闭环。
- 阶段 2 是否应该只接一个模型，而不是一开始做多模型路由。
- 阶段 3 和阶段 4 的顺序是否符合当前产品需求。
- 阶段 5 和阶段 6 哪个更符合你的真实使用方向。
- 阶段 8 是否明确延后，避免过早平台化。
