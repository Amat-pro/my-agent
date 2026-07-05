# my-agent 项目 Agent 说明

## 项目概览

`my-agent` 是一个 Python Agent 应用脚手架。项目起步形态是 `FastAPI 单体应用
+ 清晰模块边界`，后续可以逐步演进出独立 Runtime、Tool Worker、知识库服务、
观测与治理能力。

主要设计参考：
`docs/superpowers/specs/2026-07-05-python-agent-application-design.md`

当前项目状态：

- API 入口：`app/main.py`
- 健康检查接口：`GET /health`
- Agent Runtime 骨架：`app/agent/runtime/service.py`
- Tool Registry 骨架：`app/tools/registry/base.py`
- 短期记忆骨架：`app/memory/short_term/base.py`
- 容器入口：`Dockerfile`
- 本地服务编排：`docker-compose.yaml`

## 目录边界

本项目优先保持单体仓库，但必须保持模块边界清晰：

- `app/api/`：FastAPI 路由、请求/响应 Schema、中间件。
- `app/agent/`：Agent Runtime、Planner、Executor、Policy、Session、Checkpoint
  等运行时编排逻辑。
- `app/models/`：LLM 与 Embedding 适配器。业务层不得直接依赖模型厂商 SDK。
- `app/tools/`：工具定义、工具注册、工具执行器、内置工具、外部连接器。
- `app/memory/`：短期记忆、长期记忆、检索记忆。
- `app/storage/`：数据库、缓存、向量库、对象存储等基础设施适配器。
- `app/workers/`：长任务、异步任务入口。
- `app/observability/`：日志、Trace、Metrics。
- `app/security/`：鉴权、ACL、沙箱、审批和安全治理。
- `app/domain/`：业务实体和业务服务。
- `app/config/`：配置加载、环境变量、运行时设置。

## Python 环境

- Python 版本以项目配置为准，当前由 `.python-version` 和 `pyproject.toml`
  共同约束。
- 包元数据、依赖和工具配置统一放在 `pyproject.toml`。
- 运行时依赖放在 `[project].dependencies`。
- 开发工具依赖放在 `[project.optional-dependencies].dev`。
- 本地环境变量从 `.env.example` 复制到 `.env`。
- 不要提交 `.env`、虚拟环境、缓存、日志、数据库文件和生成产物。

推荐本地初始化：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## 工程规则

- `Agent Runtime` 不得直接耦合具体 LLM SDK、存储客户端或外部工具实现。
- 编排逻辑放在 `app/agent/`，可调用能力放在 `app/tools/`，业务规则放在
  `app/domain/`。
- Session、Run、Step、Artifact、Audit Event 等状态必须显式建模。
- 高风险工具必须先经过 Policy 检查，再进入执行器。
- 长任务不得阻塞 API 请求链路，应放入 `app/workers/` 或后续队列系统。
- 修改 Runtime、Policy、Tool、Memory、API 行为时，必须同步新增或更新测试。
- 外部输入输出、API 合约和运行时状态优先使用 Pydantic 模型。
- 模型厂商、数据库、缓存、对象存储、外部 API 等具体实现必须藏在 Adapter
  或 Connector 后面。
- 路由函数只负责校验输入、调用应用服务、返回响应，不承载复杂业务逻辑。

## Python 架构范式

- 先设计接口，再提供具体实现。默认使用 `typing.Protocol` 表达结构化接口；
  只有需要共享基础实现或生命周期钩子时，才考虑 `abc.ABC`。
- Runtime 和 Domain Service 必须依赖接口，而不是依赖具体类。例如
  `AgentRuntime` 应依赖 `Planner`、`PolicyEngine`、`ShortTermMemory`、
  `ToolRegistryReader` 这类协议。
- 具体类命名要体现实现策略，例如 `EchoPlanner`、`AllowAllPolicyEngine`、
  `InMemoryShortTermMemory`、`PostgresRunRepository`。
- 接口要小而聚焦。优先拆成多个窄接口，不要堆出一个万能 Service。
- 依赖通过构造函数注入。不要在 Runtime、Domain、Tool 执行逻辑里创建全局
  单例客户端。
- 数据契约和行为边界要分开：
  - API / Runtime 输入输出：使用 Pydantic 模型。
  - 小型内部不可变值对象：使用 `dataclass(frozen=True)`。
  - 行为抽象：使用 `Protocol` 或 `ABC`。
- 一个类通常只应该有一个变化原因。规划、执行、权限、记忆、持久化、外部调用
  要拆成不同对象。
- 基础设施适配器只负责翻译项目接口和外部 SDK，不放业务决策。
- 优先组合，谨慎继承。继承只用于真正共享行为或框架扩展点。
- 测试应尽量面向接口编写，用 fake 实现替代真实外部服务。

### 接口写法约定

新增行为边界时，优先使用下面的形态：

```python
from typing import Protocol


class RunRepository(Protocol):
    """Run 持久化仓储接口。"""

    def save(self, run: AgentRunResult) -> None:
        """保存一次 Agent Run 的执行结果。"""
```

服务类通过构造函数注入接口：

```python
class RunService:
    """Run 应用服务，负责任务级编排。"""

    def __init__(self, repository: RunRepository) -> None:
        self.repository = repository
```

Runtime / Domain 代码中避免直接创建基础设施实现：

```python
repository = PostgresRunRepository()
```

具体实现的组装位置应放在 `app/main.py`、依赖提供器、Worker 启动入口或测试
fixture 中。

## 代码风格

- 使用 Ruff 统一格式化和 lint。
- 行宽限制为 100 字符。
- 使用现代 Python 类型写法，例如 `str | None`、`list[str]`。
- 命名要体现领域含义，尤其是 Runtime 状态、Policy 决策、Tool、Artifact。
- 避免宽泛的 `except Exception`。如果必须捕获，要在清晰边界统一转换、记录和
  返回。
- 测试必须可重复，不依赖真实模型、数据库、网络或浏览器服务；确实需要时标记为
  integration 测试。

## 规范化注释要求

编写或修改代码时，必须添加规范化注释。注释目标是帮助后续维护者理解“边界、
意图、约束和副作用”，不是复述代码语法。

### 必须写注释的位置

- 每个非空模块文件应有模块级 docstring，说明该文件所属层次和职责。
- 每个对外暴露的 `Protocol`、类、Pydantic 模型、dataclass 必须写 docstring。
- 每个对外暴露的方法和函数必须写 docstring，说明输入、输出、异常或副作用。
- 复杂流程、状态转换、重试、审批、权限判断、外部调用前后必须写短注释。
- TODO 必须带原因和后续动作，例如 `TODO: 接入真实审批存储后移除内存实现。`

### 注释格式约定

模块注释：

```python
"""Agent Runtime 编排入口。

本模块只协调 Planner、Policy、Memory 和 Tool Registry，不直接依赖具体模型
SDK 或数据库客户端。
"""
```

类注释：

```python
class AgentRuntime:
    """Agent 执行运行时。

    负责创建 Run、执行 Policy 检查、写入短期记忆，并委托 Planner 生成下一步
    响应或动作。
    """
```

函数注释：

```python
def run(self, request: AgentRunRequest) -> AgentRunResult:
    """执行一次 Agent Run。

    Raises:
        ValueError: 当输入为空或违反 Policy 时抛出。
    """
```

复杂逻辑注释：

```python
# 高风险工具必须先经过 PolicyEngine；这里不直接调用 ToolExecutor。
self.policy.assert_tool_allowed(tool, user)
```

### 不推荐的注释

不要写这种只复述语法的注释：

```python
# 创建一个变量
run_id = str(uuid4())
```

不要写含糊注释：

```python
# 处理逻辑
```

更好的写法是说明业务意图：

```python
# 每次 Run 使用独立 ID，便于后续审计、回放和问题定位。
run_id = str(uuid4())
```

## 日志规范

项目默认使用 JSON 行日志。应用内部日志由
`app/observability/logging/config.py` 配置，Uvicorn 日志由
`app/observability/logging/uvicorn.json` 配置。

### 必须记录的日志

- 应用启动和配置完成：记录 `app_name`、`app_env`。
- Agent Run 生命周期：开始、成功、失败、取消。
- Tool 调用生命周期：准备调用、调用成功、调用失败、被 Policy 拒绝。
- Policy 决策：高风险动作、拒绝原因、审批状态变化。
- 外部系统调用：目标系统、动作类型、耗时、状态，不记录密钥和完整请求体。
- 异步任务：任务创建、开始、重试、完成、失败。
- 数据迁移、批处理、长任务：开始、进度摘要、最终状态。

### 日志级别

- `DEBUG`：本地排查信息，不能包含敏感数据，默认不依赖它判断线上状态。
- `INFO`：正常业务状态变化，例如 `agent_run_started`、`agent_run_succeeded`。
- `WARNING`：可恢复异常、重试、降级、Policy 拒绝、外部依赖慢响应。
- `ERROR`：请求失败、任务失败、工具调用失败、外部依赖不可用。
- `CRITICAL`：进程无法继续、数据一致性风险、安全边界失效。

### 结构化字段约定

业务日志应使用稳定事件名作为 message，并通过 `extra={"fields": {...}}`
传入结构化字段：

```python
logger.info(
    "agent_run_succeeded",
    extra={
        "fields": {
            "run_id": run_id,
            "session_id": session_id,
            "status": "succeeded",
            "steps_used": steps_used,
        }
    },
)
```

常用字段：

- `run_id`：一次 Agent Run 的唯一标识。
- `session_id`：用户会话标识。
- `step_id`：执行步骤标识。
- `tool_name`：工具名。
- `status`：执行状态。
- `duration_ms`：耗时。
- `error_type`：错误类型。
- `approval_id`：人工审批记录标识。

### 禁止记录的内容

- 用户原始输入全文，除非明确做了脱敏和采样控制。
- API Key、Token、Cookie、Authorization header。
- 数据库密码、连接串密码、私钥、证书内容。
- 文件原文、模型完整 prompt、工具完整参数中的敏感字段。
- 大体积响应正文、图片、二进制内容。

如果必须定位问题，只记录摘要、长度、哈希、资源 ID 或脱敏后的片段。

## 验证命令

声明任务完成前，优先运行最小必要检查：

```bash
make check
```

等价命令：

```bash
ruff format --check .
ruff check .
mypy app
pytest
```

API 相关修改还要确认 FastAPI 应用能正常导入：

```bash
python3 -c "from app.main import create_app; create_app()"
```

Docker 相关修改要确认 Compose 文件可解析：

```bash
docker compose config
```

## Git 规则

- 用户没有明确要求时，不要提交。
- 提交前必须先查看工作区状态，避免混入用户的无关改动。
- 脚手架、规范、业务实现、修复应尽量拆成可审查的独立提交。
