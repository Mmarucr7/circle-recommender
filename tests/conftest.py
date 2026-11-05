import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from circle_recommender.api.app import create_app
from circle_recommender.db.connection import read_only_connection
from circle_recommender.db.seed import build_database
from circle_recommender.services.recommendations import RecommendationRun, recommend_for_user

RunFor = Callable[..., RecommendationRun]


@pytest.fixture(scope="session")
def database_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("db") / "test.db"
    build_database(path)
    return path


@pytest.fixture
def connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    with read_only_connection(database_path) as conn:
        yield conn


@pytest.fixture
def run_for(connection: sqlite3.Connection) -> RunFor:
    def run(user_id: int, limit: int = 10, include_unavailable: bool = False) -> RecommendationRun:
        return recommend_for_user(connection, user_id, limit, include_unavailable)

    return run


@pytest.fixture
def client(database_path: Path) -> TestClient:
    return TestClient(create_app(database_path))
