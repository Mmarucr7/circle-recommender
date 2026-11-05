import json
import os
import sqlite3
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from circle_recommender import config
from circle_recommender.recommender.activity import (
    activity_score,
    engagement_per_post,
    is_active,
    is_full,
    seats_left,
)
from circle_recommender.recommender.dedupe import DedupeInput, cluster_circles
from circle_recommender.recommender.text import normalise_location

Record = dict[str, Any]


@dataclass(frozen=True, slots=True)
class SeedData:
    topics: list[Record]
    users: list[Record]
    circles: list[Record]
    memberships: list[Record]
    activity: list[Record]


@dataclass(frozen=True, slots=True)
class SeedSummary:
    path: Path
    reference_time: datetime
    counts: dict[str, int]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_seed_data(seed_dir: Path) -> SeedData:
    def read(name: str) -> list[Record]:
        with (seed_dir / f"{name}.json").open(encoding="utf-8") as handle:
            records: list[Record] = json.load(handle)
        return records

    return SeedData(
        topics=read("topics"),
        users=read("users"),
        circles=read("circles"),
        memberships=read("memberships"),
        activity=read("activity"),
    )


def default_reference_time(data: SeedData) -> datetime:
    timestamps = [parse_time(a["created_at"]) for a in data.activity]
    timestamps += [parse_time(c["last_activity_at"]) for c in data.circles]
    return max(timestamps)


def insert_core(connection: sqlite3.Connection, data: SeedData) -> None:
    topic_ids = {t["slug"]: t["id"] for t in data.topics}
    connection.executemany(
        "INSERT INTO topics (id, slug, label, domain) VALUES (?, ?, ?, ?)",
        [(t["id"], t["slug"], t["label"], t["domain"]) for t in data.topics],
    )
    connection.executemany(
        """INSERT INTO users (id, first_name, last_name, has_photo, bio, job_title, company, industry,
               location, joined_at, profile_completeness)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                u["id"],
                u["first_name"],
                u["last_name"],
                int(u["has_photo"]),
                u["bio"],
                u["job_title"],
                u["company"],
                u["industry"],
                u["location"],
                u["joined_at"],
                u["profile_completeness"],
            )
            for u in data.users
        ],
    )
    connection.executemany(
        "INSERT INTO user_topic_interests (user_id, topic_id) VALUES (?, ?)",
        [(u["id"], topic_ids[slug]) for u in data.users for slug in sorted(set(u["topic_interests"]))],
    )
    connection.executemany(
        """INSERT INTO circles (id, name, slug, description, cover_image_url, format, access, join_policy,
               max_members, member_count, created_at, last_activity_at, feed_posts_30d, chat_messages_30d)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                c["id"],
                c["name"],
                c["slug"],
                c["description"],
                c["cover_image_url"],
                c["format"],
                c["access"],
                c["join_policy"],
                c["max_members"],
                c["member_count"],
                c["created_at"],
                c["last_activity_at"],
                c["feed_posts_30d"],
                c["chat_messages_30d"],
            )
            for c in data.circles
        ],
    )
    connection.executemany(
        "INSERT INTO circle_topics (circle_id, topic_id) VALUES (?, ?)",
        [(c["id"], topic_ids[c["topic"]]) for c in data.circles if c["topic"] is not None],
    )
    connection.executemany(
        "INSERT INTO circle_tags (circle_id, tag) VALUES (?, ?)",
        [(c["id"], tag) for c in data.circles for tag in sorted(set(c["tags"]))],
    )
    connection.executemany(
        "INSERT INTO circle_memberships (circle_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
        [(m["circle_id"], m["user_id"], m["role"], m["joined_at"]) for m in data.memberships],
    )
    connection.executemany(
        """INSERT INTO circle_activity (id, circle_id, author_user_id, body, reaction_count, comment_count,
               save_count, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                a["id"],
                a["circle_id"],
                a["author_user_id"],
                a["body"],
                a["reaction_count"],
                a["comment_count"],
                a["save_count"],
                a["created_at"],
            )
            for a in data.activity
        ],
    )


def circle_feature_rows(data: SeedData, reference_time: datetime) -> list[tuple[Any, ...]]:
    users = {u["id"]: u for u in data.users}
    leaders = {m["circle_id"]: m["user_id"] for m in data.memberships if m["role"] == "leader"}
    window_start = reference_time - timedelta(days=config.ACTIVITY_WINDOW_DAYS)
    recent_engagement: dict[int, list[int]] = defaultdict(list)
    for post in data.activity:
        if window_start < parse_time(post["created_at"]) <= reference_time:
            total = post["reaction_count"] + post["comment_count"] + post["save_count"]
            recent_engagement[post["circle_id"]].append(total)
    clusters = cluster_circles([DedupeInput(c["id"], c["name"], c["topic"]) for c in data.circles])

    rows: list[tuple[Any, ...]] = []
    for c in data.circles:
        days_since = max(0.0, (reference_time - parse_time(c["last_activity_at"])) / timedelta(days=1))
        engagement = engagement_per_post(recent_engagement[c["id"]])
        leader = users.get(leaders.get(c["id"], -1))
        location = normalise_location(leader["location"] if leader else None)
        rows.append(
            (
                c["id"],
                activity_score(c["feed_posts_30d"], c["chat_messages_30d"], engagement, days_since),
                round(engagement, config.SCORE_DECIMALS),
                round(days_since, config.SCORE_DECIMALS),
                seats_left(c["member_count"], c["max_members"]),
                int(is_full(c["member_count"], c["max_members"])),
                int(is_active(c["feed_posts_30d"], days_since)),
                clusters[c["id"]],
                location[0] if location else None,
                location[1] if location else None,
            )
        )
    return rows


def build_database(
    target: Path,
    seed_dir: Path = config.SEED_DATA_DIR,
    schema_path: Path = config.SCHEMA_PATH,
    reference_time: datetime | None = None,
) -> SeedSummary:
    data = load_seed_data(seed_dir)
    reference = reference_time or default_reference_time(data)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(suffix=".db", dir=target.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        connection = sqlite3.connect(temp_path)
        try:
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            with connection:
                insert_core(connection, data)
                connection.executemany(
                    """INSERT INTO circle_features (circle_id, activity_score, engagement_per_post_30d,
                           days_since_last_activity, seats_left, is_full, is_active, dedupe_cluster_id,
                           location_key, location_label)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    circle_feature_rows(data, reference),
                )
                connection.execute(
                    "INSERT INTO dataset_meta (key, value) VALUES ('reference_time', ?)",
                    (reference.isoformat(),),
                )
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise ValueError(f"Foreign key violations in seed data: {violations[:5]}")
        finally:
            connection.close()
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    counts = {
        "topics": len(data.topics),
        "users": len(data.users),
        "circles": len(data.circles),
        "memberships": len(data.memberships),
        "activity": len(data.activity),
    }
    return SeedSummary(target, reference, counts)


def main() -> None:
    summary = build_database(config.database_path(), reference_time=config.reference_time_override())
    counts = ", ".join(f"{name}={count}" for name, count in summary.counts.items())
    print(f"Seeded {summary.path} (reference_time={summary.reference_time.isoformat()}): {counts}")


if __name__ == "__main__":
    main()
