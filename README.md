# my-agent

`my-agent` 是一个 Python Agent 应用脚手架，架构设计参考：
`docs/superpowers/specs/2026-07-05-python-agent-application-design.md`。

项目当前采用 `FastAPI 单体应用 + 清晰模块边界` 的起步形态，重点先把
Agent Runtime、Tool、Memory、Storage、Worker、Observability、Security 等边界
拆清楚，方便后续逐步演进。

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
cp .env.example .env
make run
```

`make run` 会使用项目内的 Uvicorn 日志配置，控制台日志默认按 JSON 行输出。

服务启动后，可以用下面的命令检查健康状态：

```bash
curl http://127.0.0.1:8000/health
```

正常返回：

```json
{"status":"ok"}
```

## Docker 启动

```bash
make docker-up
```

API 默认暴露在 `http://localhost:8000`。在 Docker Compose 网络中，Postgres
服务名是 `postgres`，Redis 服务名是 `redis`。

如果反复构建后出现 `<none>` 镜像，可以清理 dangling 镜像：

```bash
make docker-prune
```

需要无缓存重建并自动清理 dangling 镜像时：

```bash
make docker-rebuild
```

## 验证命令

```bash
make check
```

## 依赖与配置文件

- `pyproject.toml`：项目依赖、包信息和工具配置的主入口。
- `requirements.txt`：运行时依赖安装兼容入口。
- `requirements-dev.txt`：开发依赖安装兼容入口。
- `.pre-commit-config.yaml`：提交前格式化、lint 和类型检查配置。
- `.env.example`：本地环境变量示例。

## 目录结构

```text
app/
  api/              FastAPI 路由、Schema、中间件
  agent/            Runtime、Planner、Executor、Policy、Session、Checkpoint
  models/           LLM 和 Embedding 适配器
  tools/            工具注册、工具执行器、内置工具、连接器
  memory/           短期记忆、长期记忆、检索记忆
  storage/          数据库、缓存、向量库、对象存储适配器
  workers/          长任务和异步任务入口
  observability/    日志、Trace、Metrics
  security/         鉴权、ACL、沙箱控制
  domain/           业务实体和业务服务
  config/           配置加载和运行时设置
tests/
docs/
```
