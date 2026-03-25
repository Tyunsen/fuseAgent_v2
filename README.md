# fuseAgent / ApeRAG

这个仓库基于 ApeRAG，当前包含：

- Python/FastAPI 后端
- Next.js 前端
- PostgreSQL / Redis / Qdrant / Elasticsearch
- 可选 Neo4j 图数据库
- Celery 异步任务与 Flower

这份 README 只保留一件事：怎么把系统稳定跑起来。

## 运行方式

推荐直接用 Docker Compose。

### 1. 准备环境

需要先安装：

- Docker Desktop
- Docker Compose
- Git

建议机器配置至少：

- CPU 4 核
- 内存 8 GB

### 2. 初始化本地环境变量

在项目根目录执行：

```powershell
Copy-Item .\envs\env.template .\.env
```

如果你需要自定义端口、模型配置、对象存储或鉴权方式，直接修改根目录的 `.env`。

### 3. 启动基础服务

```powershell
docker compose up -d
```

这会启动：

- `frontend`
- `api`
- `celeryworker`
- `celerybeat`
- `flower`
- `postgres`
- `redis`
- `qdrant`
- `es`

### 4. 如果要用图谱能力，再启动 Neo4j

这一步很重要。

当前 Docker 环境里的 API 默认通过 `envs/docker.env.overrides` 连接 `aperag-neo4j:7687`。如果你需要图谱检索、图谱问答、图谱索引相关功能，请额外启动 Neo4j profile：

```powershell
docker compose --profile neo4j up -d neo4j
```

如果不启动这一步，依赖 Neo4j 的功能可能会报错，例如：

```text
Cannot resolve address aperag-neo4j:7687
```

### 5. 访问系统

如果你使用的是 `env.template` 默认端口：

- 前端: [http://127.0.0.1:3000/web](http://127.0.0.1:3000/web)
- API 文档: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Flower: [http://127.0.0.1:5555](http://127.0.0.1:5555)
- Neo4j Browser: [http://127.0.0.1:7474](http://127.0.0.1:7474)

如果你的 `.env` 里改过宿主机端口，请以 `.env` 为准。

## 当前这台机器上的运行地址

这份仓库当前本机已经实际跑起来，端口不是默认值，而是：

- 前端: [http://127.0.0.1:36130/web](http://127.0.0.1:36130/web)
- API 文档: [http://127.0.0.1:36180/docs](http://127.0.0.1:36180/docs)
- Neo4j Browser: [http://127.0.0.1:7474](http://127.0.0.1:7474)

Neo4j 默认登录：

- 用户名: `neo4j`
- 密码: `password`

## 常用命令

### 启动全部基础服务

```powershell
docker compose up -d
```

### 启动基础服务 + Neo4j

```powershell
docker compose up -d
docker compose --profile neo4j up -d neo4j
```

### 查看容器状态

```powershell
docker compose ps
```

### 查看 API 日志

```powershell
docker logs -f aperag-api
```

### 查看前端日志

```powershell
docker logs -f aperag-frontend
```

### 停止服务

```powershell
docker compose down
```

### 停止服务并删除数据卷

这会清空本地数据库和索引数据，谨慎执行。

```powershell
docker compose down -v
```

## 常见问题

### 1. 报错 `Cannot resolve address aperag-neo4j:7687`

原因通常是 Neo4j 没启动。

修复：

```powershell
docker compose --profile neo4j up -d neo4j
```

### 2. 前端打不开

先看容器状态：

```powershell
docker compose ps
```

再看前端日志：

```powershell
docker logs -f aperag-frontend
```

### 3. API 没起来或 `/docs` 打不开

先看 API 日志：

```powershell
docker logs -f aperag-api
```

再确认 PostgreSQL、Redis、Qdrant、Elasticsearch 都是 `healthy`。

## 仓库结构

```text
aperag/          Python 后端
web/             Next.js 前端
config/          Celery 与运行配置
deploy/          Helm 与数据库部署脚本
envs/            环境变量模板
scripts/         启动与初始化脚本
tests/           测试
docker-compose.yml
```

## 开发备注

- `.env` 不提交到 GitHub
- `web/node_modules/` 不提交到 GitHub
- 如果只是本地体验系统，优先走 Docker Compose
- 如果要完整使用图谱相关能力，记得带上 Neo4j profile
