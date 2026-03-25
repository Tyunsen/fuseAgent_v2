# fuseAgent

本地 RAG 知识库系统，基于 ApeRAG，支持混合检索、图谱查询和异步任务处理。

## 快速启动

### 1. 准备环境

- Docker Desktop
- Docker Compose
- Git

### 2. 初始化并启动

```bash
git clone https://github.com/Tyunsen/fuseAgent_v2.git
cd fuseAgent_v2
cp envs/env.template .env
docker compose up -d --pull always
```

## 访问地址

本机运行端口：

- 前端: http://127.0.0.1:36130/web
- API 文档: http://127.0.0.1:36180/docs
- Flower: http://127.0.0.1:36555
- Neo4j Browser: http://127.0.0.1:7474

Neo4j 登录：用户名 `neo4j`，密码 `password`

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看 API 日志
docker logs -f aperag-api

# 停止服务
docker compose down

# 停止服务并清除数据
docker compose down -v
```
