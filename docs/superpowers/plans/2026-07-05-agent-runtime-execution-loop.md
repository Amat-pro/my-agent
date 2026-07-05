# Agent Runtime 执行循环实现计划

**文档标识：** `PLAN-2026-07-05-agent-runtime-execution-loop`

**文档类型：** 阶段 1 执行计划。

**上游来源：**

- 总体设计：`SPEC-2026-07-05-python-agent-application-design`
  - 文件：`docs/superpowers/specs/2026-07-05-python-agent-application-design.md`
- 阶段拆解：`PHASES-2026-07-05-python-agent-application`
  - 文件：`docs/superpowers/plans/2026-07-05-python-agent-application-phases.md`

**文档作用：** 展开阶段 1：Agent Runtime 最小执行内核。

**引用关系：**

```text
SPEC 总体设计
  -> PHASES 落地阶段拆解
    -> PLAN 当前文档：阶段 1 执行任务
```

**当前执行状态：** 已完成。阶段 1 的 Runtime 执行循环、工具调用、失败处理和
token usage 统计已实现，并通过 `make PYTHON=./.venv/bin/python3 check` 验证。

> **给后续执行 Agent 的要求：** 实施本计划时必须使用
> `superpowers:subagent-driven-development`（推荐）或
> `superpowers:executing-plans`，按任务逐个执行和验收。任务使用 checkbox
> `- [x]` 便于跟踪。

**目标：** 把当前只会 Echo 的 `AgentRuntime`，升级成一个最小但完整的结构化
Agent Runtime：支持 Run/Step 状态、Planner 结构化动作、本地工具调用、token
使用量统计和失败状态返回。

**架构原则：** 继续保持 FastAPI 单体应用，但边界必须清晰。Runtime 只负责编排；
Planner 决定下一步动作；Policy 做治理检查；Tool Registry 负责工具发现；
Tool Executor 负责执行；Token Counter 放在观测/计量边界，不塞进 Planner 或工具实现。

**技术栈：** Python 3.11+、FastAPI、Pydantic v2、pytest、Ruff、mypy。

## 所属阶段

这份计划只对应总体阶段拆解中的 **阶段 1：Agent Runtime 最小执行内核**。

总体阶段拆解见：

- `docs/superpowers/plans/2026-07-05-python-agent-application-phases.md`

本计划不再展开完整项目路线，只负责把阶段 1 拆成可执行任务。

## 全局约束

- 不引入真实 LLM SDK，不接 OpenAI/Claude/本地模型。
- 不引入 Postgres、Redis、RAG、SSE、Worker、审批系统和 Artifact 存储。
- `Agent Runtime` 不能直接依赖模型 SDK、数据库客户端或外部工具实现。
- Runtime 依赖接口：`Planner`、`PolicyEngine`、`ShortTermMemory`、
  `ToolRegistryReader`、`ToolExecutor`、`TokenCounter`。
- Runtime 输入输出使用 Pydantic 模型。
- 每个非空模块必须有模块级 docstring。
- 每个对外暴露的 Protocol、类、Pydantic 模型、dataclass、方法和函数必须有
  docstring。
- 日志只能记录稳定元数据，不能记录用户原始输入全文。
- 用户没有明确要求时不要提交 Git commit。

## 文件范围

- 修改 `app/agent/runtime/types.py`
  - 定义 Runtime 数据契约：Run、Step、PlannerAction、ToolCall、TokenUsage。
- 修改 `app/agent/planner/base.py`
  - 把 Planner 从返回字符串改成返回结构化动作。
- 修改 `app/agent/policy/base.py`
  - 增加工具调用前的 Policy 检查接口。
- 修改 `app/tools/executors/base.py`
  - 补齐 Tool Executor 的注释和执行边界。
- 修改 `app/agent/runtime/service.py`
  - 实现 Runtime 执行循环、工具调用、失败返回和 token 统计。
- 新增 `app/observability/token_usage/__init__.py`
  - Token usage 观测模块入口。
- 新增 `app/observability/token_usage/base.py`
  - Token 计数接口和本地近似计数器。
- 修改 `tests/test_runtime.py`
  - 覆盖 Runtime 主链路、工具链路、失败链路和 token usage。
- 新增 `tests/test_planner.py`
  - 覆盖 Planner 结构化动作。
- 新增 `tests/test_tool_executor.py`
  - 覆盖本地工具执行器。
- 新增 `tests/test_token_usage.py`
  - 覆盖 token 近似计数器。

---

## Task 1：补 Runtime 数据契约

**目标：** 让一次 Run 不再只是 `run_id/status/output`，而是能返回可审计的
`steps`、失败原因和 token usage 占位结构。

**文件：**

- 修改：`app/agent/runtime/types.py`
- 修改测试：`tests/test_runtime.py`

**新增/调整接口：**

- `StepStatus`
  - `created`
  - `running`
  - `succeeded`
  - `failed`
  - `skipped`
- `StepType`
  - `planner`
  - `tool`
  - `final_answer`
  - `approval`
- `PlannerActionType`
  - `final_answer`
  - `tool_call`
- `ToolCallRequest`
  - `tool_name: str`
  - `arguments: dict[str, Any]`
- `ToolCallResult`
  - `tool_name: str`
  - `output: Any`
- `PlannerRequest`
  - `user_input: str`
  - `session_id: str`
  - `available_tools: list[str]`
  - `previous_tool_result: ToolCallResult | None`
- `PlannerAction`
  - `action_type: PlannerActionType`
  - `final_answer: str | None`
  - `tool_call: ToolCallRequest | None`
- `AgentStep`
  - `step_id: str`
  - `step_type: StepType`
  - `status: StepStatus`
  - `tool_call: ToolCallRequest | None`
  - `tool_result: ToolCallResult | None`
  - `output: str | None`
  - `error_message: str | None`
- `TokenUsage`
  - `prompt_tokens: int`
  - `completion_tokens: int`
  - `total_tokens: int`
  - `estimation_method: str`
- `AgentRunResult`
  - 保留 `run_id/status/output/steps_used`
  - 新增 `steps: list[AgentStep]`
  - 新增 `token_usage: TokenUsage`
  - 新增 `error_message: str | None`

**执行步骤：**

- [x] 在 `tests/test_runtime.py` 增加测试：
  - 普通输入 `hello` 返回成功。
  - `result.steps` 长度为 1。
  - 第一个 step 是 `StepType.FINAL_ANSWER`。
  - 第一个 step 状态是 `StepStatus.SUCCEEDED`。
  - `result.error_message is None`。
- [x] 运行：

```bash
python3 -m pytest tests/test_runtime.py::test_runtime_result_contains_structured_steps -q
```

预期：失败，因为类型和字段还没实现。

- [x] 修改 `app/agent/runtime/types.py`，补齐上面的枚举和 Pydantic 模型。
- [x] 再运行同一个测试。

预期：可能仍然失败，但失败点应该从“类型不存在”变成“Runtime 还没有填充 steps”。
这说明数据契约已经生效，Runtime 行为留到后续任务实现。

---

## Task 2：把 Planner 改成结构化动作协议

**目标：** Planner 不再返回纯字符串，而是返回 Runtime 可以理解的结构化动作：
最终回答或工具调用。

**文件：**

- 修改：`app/agent/planner/base.py`
- 新增测试：`tests/test_planner.py`
- 修改测试：`tests/test_runtime.py`

**接口变化：**

当前：

```python
def plan(self, user_input: str) -> str
```

改成：

```python
def plan(self, request: PlannerRequest) -> PlannerAction
```

**Planner 实现：**

- `EchoPlanner`
  - 始终返回 `PlannerActionType.FINAL_ANSWER`
  - `final_answer = f"Received: {request.user_input}"`
- `KeywordToolPlanner`
  - 测试用 Planner，不接真实 LLM。
  - 输入格式：`tool:<tool_name> message=<value>`
  - 没有工具结果时返回 `TOOL_CALL`。
  - 有 `previous_tool_result` 时返回 `FINAL_ANSWER`，内容为工具结果。

**执行步骤：**

- [x] 新增 `tests/test_planner.py`。
- [x] 增加测试：`EchoPlanner` 返回 `FINAL_ANSWER`。
- [x] 增加测试：`KeywordToolPlanner` 对 `tool:echo message=hello` 返回工具调用。
- [x] 运行：

```bash
python3 -m pytest tests/test_planner.py -q
```

预期：失败，因为 Planner 协议还没改。

- [x] 修改 `app/agent/planner/base.py`：
  - 增加模块 docstring。
  - 更新 `Planner` Protocol。
  - 更新 `EchoPlanner`。
  - 新增 `KeywordToolPlanner`。
- [x] 再运行：

```bash
python3 -m pytest tests/test_planner.py -q
```

预期：通过。

---

## Task 3：实现 Runtime 工具调用执行循环

**目标：** Runtime 能根据 Planner 动作执行一个最小闭环：

```text
创建 Run
写入用户消息
循环 max_steps 次：
  调 Planner
  如果是 final_answer：写 assistant memory，返回成功
  如果是 tool_call：查 Tool Registry，过 Policy，调 Tool Executor，记录 Tool Step
超过 max_steps：返回失败
```

**文件：**

- 修改：`app/agent/policy/base.py`
- 修改：`app/tools/executors/base.py`
- 修改：`app/agent/runtime/service.py`
- 修改测试：`tests/test_runtime.py`
- 新增测试：`tests/test_tool_executor.py`

**接口变化：**

- `PolicyEngine` 新增：

```python
def assert_tool_allowed(self, request: ToolCallRequest, tool: ToolDefinition) -> None
```

- `AgentRuntime.__init__` 新增：

```python
tool_executor: ToolExecutor | None = None
```

**执行步骤：**

- [x] 新增 `tests/test_tool_executor.py`：
  - 注册一个 `echo` 工具。
  - `LocalToolExecutor.execute()` 能调用 handler。
- [x] 在 `tests/test_runtime.py` 增加工具调用测试：
  - 注册 `echo` 工具。
  - 使用 `KeywordToolPlanner`。
  - 输入 `tool:echo message=hello`。
  - Runtime 返回成功。
  - `output == "hello"`。
  - `steps_used == 2`。
  - steps 依次为 `TOOL`、`FINAL_ANSWER`。
  - 第一个 step 有 `tool_call` 和 `tool_result`。
- [x] 运行：

```bash
python3 -m pytest tests/test_runtime.py::test_runtime_executes_tool_call_and_returns_final_answer -q
```

预期：失败，因为 Runtime 还不能执行工具。

- [x] 修改 `app/agent/policy/base.py`：
  - 增加模块 docstring。
  - `PolicyEngine` 增加 `assert_tool_allowed()`。
  - `AllowAllPolicyEngine` 默认允许已注册工具调用。
- [x] 修改 `app/tools/executors/base.py`：
  - 增加模块 docstring。
  - 给 `ToolExecutor` 和 `LocalToolExecutor` 补齐 docstring。
- [x] 修改 `app/agent/runtime/service.py`：
  - 注入 `tool_executor`。
  - 默认使用 `LocalToolExecutor()`。
  - 用 `PlannerRequest` 调用 Planner。
  - 根据 `PlannerActionType` 分支处理。
  - 工具调用时执行：

```text
tools.get(tool_name)
policy.assert_tool_allowed(...)
tool_executor.execute(...)
记录 ToolCallResult
追加 AgentStep(step_type=TOOL, status=SUCCEEDED)
```

- [x] final answer 时：
  - 追加 `AgentStep(step_type=FINAL_ANSWER, status=SUCCEEDED)`。
  - 写入 assistant memory。
  - 返回 `RunStatus.SUCCEEDED`。
- [x] 超过 `max_steps` 时：
  - 返回 `RunStatus.FAILED`。
  - `error_message = "Agent exceeded max_steps before producing a final answer."`
- [x] 运行：

```bash
python3 -m pytest tests/test_tool_executor.py tests/test_runtime.py -q
```

预期：除 Task 4 要新增的失败场景外，其余通过。

---

## Task 4：补失败场景

**目标：** Runtime 不应该把内部异常直接漏出去。未知工具、工具执行失败、
循环无法结束，都要转换成结构化失败结果。

**文件：**

- 修改：`app/agent/runtime/service.py`
- 修改测试：`tests/test_runtime.py`

**失败规则：**

- 未知工具：
  - 返回 `RunStatus.FAILED`
  - `output == ""`
  - `error_message == "Unknown tool: <name>"`
  - 失败 step 类型是 `StepType.TOOL`
  - 失败 step 状态是 `StepStatus.FAILED`
- 超过 `max_steps`：
  - 返回 `RunStatus.FAILED`
  - `output == ""`
  - `steps_used == max_steps`
  - `error_message == "Agent exceeded max_steps before producing a final answer."`

**执行步骤：**

- [x] 在 `tests/test_runtime.py` 增加未知工具测试：
  - 使用 `KeywordToolPlanner`。
  - 不注册任何工具。
  - 输入 `tool:missing message=hello`。
  - 断言返回结构化失败结果。
- [x] 在 `tests/test_runtime.py` 增加 `EndlessToolPlanner` 测试类：
  - 永远返回同一个工具调用。
  - Runtime 设置 `max_steps=2`。
  - 断言超过步数后失败。
- [x] 运行：

```bash
python3 -m pytest tests/test_runtime.py::test_runtime_returns_failed_result_for_unknown_tool tests/test_runtime.py::test_runtime_fails_when_max_steps_is_exceeded -q
```

预期：未知工具可能失败为未捕获 `KeyError`，max steps 测试应当通过或接近通过。

- [x] 修改 `app/agent/runtime/service.py`：
  - 包住工具查找、Policy 检查和工具执行。
  - 捕获 `KeyError` 和 `ValueError`。
  - 转换成 `AgentRunResult(status=RunStatus.FAILED, ...)`。
  - 记录 `agent_run_failed` 日志，只记录元数据，不记录用户输入全文。
- [x] 再运行上面的失败测试。

预期：通过。

---

## Task 5：新增 Token 计数模块

**目标：** 增加 token 使用量统计边界。当前阶段先做本地近似计数，不接真实
tokenizer，不把它当成模型账单。后面接模型时，优先使用模型 provider 返回的
真实 usage。

**文件：**

- 修改：`app/agent/runtime/types.py`
- 新增：`app/observability/token_usage/__init__.py`
- 新增：`app/observability/token_usage/base.py`
- 修改：`app/agent/runtime/service.py`
- 新增测试：`tests/test_token_usage.py`
- 修改测试：`tests/test_runtime.py`

**新增接口：**

- `TokenCounter` Protocol：

```python
def count_text(self, text: str) -> int
```

- `ApproximateTokenCounter`
  - 不依赖外部 SDK。
  - 英文/数字按连续单词计数。
  - CJK 字符按单字计数。
  - 空白文本返回 0。
- `TokenUsage`
  - `prompt_tokens`
  - `completion_tokens`
  - `total_tokens`
  - `estimation_method`
- `AgentRuntime.__init__` 新增：

```python
token_counter: TokenCounter | None = None
```

**执行步骤：**

- [x] 新增 `tests/test_token_usage.py`：
  - `hello world` 计数为 2。
  - `你好` 计数为 2。
  - `hello 世界` 计数为 3。
  - 空白文本计数为 0。
- [x] 在 `tests/test_runtime.py` 增加 token usage 测试：
  - 输入 `hello world`。
  - `prompt_tokens == 2`。
  - Echo 输出 `Received: hello world`，`completion_tokens == 3`。
  - `total_tokens == 5`。
  - `estimation_method == "approximate"`。
- [x] 运行：

```bash
python3 -m pytest tests/test_token_usage.py tests/test_runtime.py::test_runtime_result_includes_token_usage_estimate -q
```

预期：失败，因为 token usage 模块和字段还不存在。

- [x] 在 `app/agent/runtime/types.py` 增加 `TokenUsage`，并把它挂到
  `AgentRunResult.token_usage`。
- [x] 新增 `app/observability/token_usage/__init__.py`。
- [x] 新增 `app/observability/token_usage/base.py`：
  - 定义 `TokenCounter`。
  - 定义 `ApproximateTokenCounter`。
  - 使用稳定的正则规则计数。
- [x] 修改 `app/agent/runtime/service.py`：
  - 注入 `token_counter`。
  - 默认使用 `ApproximateTokenCounter()`。
  - Run 开始时统计用户输入为 `prompt_tokens`。
  - final answer 时统计输出为 `completion_tokens`。
  - 所有返回路径都带上 `token_usage`。
- [x] 成功/失败日志增加数字字段：
  - `prompt_tokens`
  - `completion_tokens`
  - `total_tokens`

这些字段是数字摘要，不包含用户原文，可以记录。

- [x] 运行：

```bash
python3 -m pytest tests/test_token_usage.py tests/test_runtime.py::test_runtime_result_includes_token_usage_estimate -q
```

预期：通过。

---

## Task 6：整体验证

**目标：** 确认 Runtime 执行循环、Planner 协议、工具调用、失败处理、token 统计
和项目质量检查都通过。

**执行步骤：**

- [x] 运行完整测试：

```bash
python3 -m pytest -q
```

预期：通过。

- [x] 运行项目检查：

```bash
make check
```

预期：通过。该命令会执行：

```text
ruff format --check .
ruff check .
mypy app
pytest
python3 -c "from app.main import create_app; create_app()"
```

- [x] 查看工作区状态：

```bash
git status --short
```

预期：只包含本计划涉及的文件。不要提交，除非用户明确要求。

## Review 要点

你 review 这份计划时重点看这几件事：

- 是否同意先做 Runtime 执行协议，而不是先接真实模型。
- 是否同意 token 计数先用近似实现，后面接模型时再替换为真实 usage。
- 是否同意工具调用先只支持本地 `LocalToolExecutor`。
- 是否同意本阶段不做数据库、RAG、Worker、审批、Artifact。
- 是否同意 Runtime 返回结构里直接暴露 `steps` 和 `token_usage`。

## 自检

- 覆盖了设计文档里的第一阶段核心：Runtime、状态、工具、Policy、观测。
- 没有引入真实外部依赖，便于本地测试。
- 每个任务都有明确文件、接口和验收命令。
- token usage 已作为独立观测模块加入，不和 Planner/Tool 耦合。
- 最终检查使用项目已有 `make check`。

## 执行结果

**完成状态：** 已完成。

**实际验证命令：**

```bash
./.venv/bin/python3 -m pytest -q
make PYTHON=./.venv/bin/python3 check
```

**验证结果：**

- `ruff format --check .` 通过。
- `ruff check .` 通过。
- `mypy app` 通过。
- `pytest` 通过，18 个测试全部通过。
- `from app.main import create_app; create_app()` 通过。

**说明：**

- 验证中出现 1 个 `StarletteDeprecationWarning`，来自 FastAPI/TestClient 依赖层，
  不影响本阶段功能通过。
