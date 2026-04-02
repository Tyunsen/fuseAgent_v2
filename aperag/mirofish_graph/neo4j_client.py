from __future__ import annotations

import threading

from neo4j import Driver, GraphDatabase, Session

from aperag.config import settings

from .neo4j_queries import SCHEMA_QUERIES


class Neo4jClientManager:
    _driver: Driver | None = None
    _lock = threading.Lock()

    @classmethod
    def _build_driver(cls) -> Driver:
        return GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

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
        return cls.get_driver().session(database=settings.neo4j_database)

    @classmethod
    def ensure_ready(cls) -> None:
        with cls.get_session() as session:
            session.run("RETURN 1")
            for query in SCHEMA_QUERIES:
                session.run(query)

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._driver is not None:
                cls._driver.close()
                cls._driver = None
