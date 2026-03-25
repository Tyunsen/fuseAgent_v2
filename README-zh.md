# fuseAgent

本仓库基于 [ApeRAG](https://github.com/apecloud/ApeRAG)，当前包含：

- Python/FastAPI 后端
- Next.js 前端
- PostgreSQL / Redis / Qdrant / Elasticsearch
- 可选 Neo4j 图数据库
- Celery 异步任务与 Flower

## 快速启动

> 确保机器已安装 Docker 和 Docker Compose。

```bash
git clone https://github.com/Tyunsen/fuseAgent_v2.git
cd fuseAgent_v2
cp envs/env.template .env
docker compose up -d --pull always
```

## 访问系统

| 服务 | 地址 |
|------|------|
| 前端 | http://127.0.0.1:36130/web |
| API 文档 | http://127.0.0.1:36180/docs |
| Flower | http://127.0.0.1:36555 |
| Neo4j Browser | http://127.0.0.1:7474 |

> Neo4j 默认登录：用户名 `neo4j`，密码 `password`

> 如果你的 `.env` 里改过宿主机端口，请以 `.env 中 `APERAG_*_HOST_PORT` 配置为准。

## 可选服务

启动 Neo4j（需在 `docker-compose.yml` 中取消注释 neo4j 服务或使用 `--profile neo4j`）：

```bash
docker compose --profile neo4j up -d
```

## 开发指南

参考 [docs/zh-CN/development-guide.md](docs/zh-CN/development-guide.md)。
