# fuseAgent

fuseAgent 是基于 ApeRAG 的本地 RAG 知识库系统，支持混合检索、图谱查询和异步任务处理。

## 快速启动

```bash
git clone https://github.com/Tyunsen/fuseAgent_v2.git
cd fuseAgent_v2
cp envs/env.template .env
docker compose up -d --pull always
```

## 访问系统

如果你使用的是 env.template 默认端口：

- 前端: http://127.0.0.1:3000/web
- API 文档: http://127.0.0.1:8000/docs
- Flower: http://127.0.0.1:5555
- Neo4j Browser: http://127.0.0.1:7474

如果你的 .env 里改过宿主机端口，请以 .env 为准。

**当前这台机器上的运行地址**

这份仓库当前本机已经实际跑起来，端口不是默认值，而是：

- 前端: http://127.0.0.1:36130/web
- API 文档: http://127.0.0.1:36180/docs
- Neo4j Browser: http://127.0.0.1:7474

Neo4j 默认登录：用户名: neo4j，密码: password

## 可选服务

启动 Neo4j：

```bash
docker compose --profile neo4j up -d
```
