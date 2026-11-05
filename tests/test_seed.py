import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from circle_recommender.db.seed import build_database

TABLES = (
    "topics",
    "users",
    "user_topic_interests",
    "circles",
    "circle_topics",
    "circle_tags",
    "circle_memberships",
    "circle_activity",
    "circle_features",
    "dataset_meta",
)


def dump(path: Path) -> dict[str, list[tuple[object, ...]]]:
    with sqlite3.connect(path) as connection:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall() for table in TABLES
        }


def test_seeding_twice_gives_identical_contents(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    build_database(path)
    first = dump(path)
    build_database(path)

    assert dump(path) == first
    assert len(first["users"]) == 100
    assert len(first["circles"]) == 40
    assert len(first["circle_memberships"]) == 441


def test_reference_time_defaults_to_newest_activity(tmp_path: Path) -> None:
    summary = build_database(tmp_path / "app.db")

    assert summary.reference_time == datetime(2026, 9, 21, tzinfo=UTC)


def test_reference_time_override_changes_derived_features(tmp_path: Path) -> None:
    path = tmp_path / "late.db"
    build_database(path, reference_time=datetime(2026, 11, 5, tzinfo=UTC))

    with sqlite3.connect(path) as connection:
        active = connection.execute("SELECT COUNT(*) FROM circle_features WHERE is_active = 1").fetchone()[0]
    assert active == 0


def test_derived_features_flag_the_planted_circles(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        full = [
            row[0] for row in connection.execute("SELECT circle_id FROM circle_features WHERE is_full = 1")
        ]
        inactive = [
            row[0] for row in connection.execute("SELECT circle_id FROM circle_features WHERE is_active = 0")
        ]
        tags_17 = connection.execute("SELECT COUNT(*) FROM circle_tags WHERE circle_id = 17").fetchone()[0]

    assert full == [20]
    assert inactive == [21, 32]
    assert tags_17 == 2
