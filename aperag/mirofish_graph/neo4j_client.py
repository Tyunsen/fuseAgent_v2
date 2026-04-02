from __future__ import annotations

import logging
import threading

from neo4j import Driver, GraphDatabase, Session
from neo4j.exceptions import ServiceUnavailable

from aperag.config import settings

from .neo4j_queries import SCHEMA_QUERIES

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Raised when Neo4j connection fails with helpful instructions."""

    def __init__(self, uri: str, original_error: Exception | None = None) -> None:
        self.uri = uri
        self.original_error = original_error
        message = (
            f"无法连接到 Neo4j 图数据库 (uri: {uri})。\n\n"
            "图索引构建需要 Neo4j 服务。请按以下步骤启动:\n"
            "1. 如果使用 Docker: docker compose up -d neo4j\n"
            "2. 等待 Neo4j 启动完成 (约 10-30 秒)\n"
            "3. 访问 http://localhost:7474 验证服务可用\n\n"
            "如需使用 LightRAG 图引擎（无需 Neo4j），请在集合配置中切换。"
        )
        super().__init__(message)


class Neo4jClientManager:
    _driver: Driver | None = None
    _lock = threading.Lock()
    _schema_ready: bool = False

    @classmethod
    def _build_driver(cls) -> Driver:
        try:
            return GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
        except ServiceUnavailable as e:
            raise Neo4jConnectionError(settings.neo4j_uri, e) from e

    @classmethod
    def get_driver(cls) -> Driver:
        if cls._driver is not None:
            return cls._driver
        with cls._lock:
            if cls._driver is None:
                cls._driver = cls._build_driver()
        return cls._driver

    @classmethod
    def get_session(cls) -> Session:
        try:
            return cls.get_driver().session(database=settings.neo4j_database)
        except ServiceUnavailable as e:
            raise Neo4jConnectionError(settings.neo4j_uri, e) from e

    @classmethod
    def ensure_ready(cls) -> None:
        try:
            with cls.get_session() as session:
                session.run("RETURN 1")
                if not cls._schema_ready:
                    for query in SCHEMA_QUERIES:
                        session.run(query)
                    cls._schema_ready = True
        except ServiceUnavailable as e:
            logger.error("Neo4j connection failed: %s", e)
            raise Neo4jConnectionError(settings.neo4j_uri, e) from e

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._driver is not None:
                cls._driver.close()
                cls._driver = None
            cls._schema_ready = False
