import sqlite3
from datetime import datetime

from circle_recommender.recommender.models import Circle, CircleFormat, Member
from circle_recommender.recommender.text import normalise_location


def fetch_reference_time(connection: sqlite3.Connection) -> datetime:
    row = connection.execute("SELECT value FROM dataset_meta WHERE key = ?", ("reference_time",)).fetchone()
    return datetime.fromisoformat(str(row["value"]))


def fetch_topic_labels(connection: sqlite3.Connection) -> dict[str, str]:
    rows = connection.execute("SELECT slug, label FROM topics ORDER BY slug").fetchall()
    return {str(row["slug"]): str(row["label"]) for row in rows}


def fetch_user_ids(connection: sqlite3.Connection) -> list[int]:
    return [int(row["id"]) for row in connection.execute("SELECT id FROM users ORDER BY id")]


def fetch_member(connection: sqlite3.Connection, user_id: int) -> Member | None:
    user = connection.execute(
        "SELECT id, bio, job_title, location, joined_at, profile_completeness FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if user is None:
        return None
    stated = tuple(
        str(row["slug"])
        for row in connection.execute(
            """SELECT t.slug FROM user_topic_interests i JOIN topics t ON t.id = i.topic_id
               WHERE i.user_id = ? ORDER BY t.slug""",
            (user_id,),
        )
    )
    joined_rows = connection.execute(
        """SELECT m.circle_id, f.dedupe_cluster_id FROM circle_memberships m
           JOIN circle_features f ON f.circle_id = m.circle_id
           WHERE m.user_id = ?""",
        (user_id,),
    ).fetchall()
    joined = frozenset(int(row["circle_id"]) for row in joined_rows)
    joined_clusters = frozenset(int(row["dedupe_cluster_id"]) for row in joined_rows)
    implied = tuple(
        str(row["slug"])
        for row in connection.execute(
            """SELECT DISTINCT t.slug FROM circle_memberships m
               JOIN circle_topics ct ON ct.circle_id = m.circle_id
               JOIN topics t ON t.id = ct.topic_id
               WHERE m.user_id = ? ORDER BY t.slug""",
            (user_id,),
        )
        if str(row["slug"]) not in stated
    )
    location = normalise_location(user["location"])
    profile_text = " ".join(part for part in (user["bio"], user["job_title"]) if part)
    return Member(
        id=int(user["id"]),
        location_key=location[0] if location else None,
        location_label=location[1] if location else None,
        stated_topics=stated,
        implied_topics=implied,
        joined_circle_ids=joined,
        joined_cluster_ids=joined_clusters,
        profile_text=profile_text,
        profile_completeness=float(user["profile_completeness"]),
        joined_at=datetime.fromisoformat(str(user["joined_at"])),
        has_memberships=bool(joined),
    )


CIRCLE_COLUMNS = """
    SELECT c.id, c.name, c.description, c.format, c.access, c.join_policy, c.member_count,
           c.max_members, c.cover_image_url, c.feed_posts_30d, t.slug AS primary_topic,
           f.activity_score, f.seats_left, f.is_full, f.is_active, f.dedupe_cluster_id,
           f.location_key, f.location_label
    FROM circle_features f
    JOIN circles c ON c.id = f.circle_id
    LEFT JOIN circle_topics ct ON ct.circle_id = c.id
    LEFT JOIN topics t ON t.id = ct.topic_id
"""
AVAILABLE_ONLY = "WHERE f.is_active = ? AND f.is_full = ? AND c.access = ?"


def fetch_circles(connection: sqlite3.Connection, include_unavailable: bool) -> list[Circle]:
    tags: dict[int, list[str]] = {}
    for row in connection.execute("SELECT circle_id, tag FROM circle_tags ORDER BY circle_id, tag"):
        tags.setdefault(int(row["circle_id"]), []).append(str(row["tag"]))
    if include_unavailable:
        rows = connection.execute(f"{CIRCLE_COLUMNS} ORDER BY c.id").fetchall()
    else:
        rows = connection.execute(
            f"{CIRCLE_COLUMNS} {AVAILABLE_ONLY} ORDER BY c.id", (1, 0, "public")
        ).fetchall()
    return [
        Circle(
            id=int(row["id"]),
            name=str(row["name"]),
            description=row["description"],
            format=CircleFormat(row["format"]),
            is_public=row["access"] == "public",
            is_open=row["join_policy"] == "open",
            member_count=int(row["member_count"]),
            max_members=row["max_members"],
            seats_left=row["seats_left"],
            primary_topic=row["primary_topic"],
            tags=tuple(tags.get(int(row["id"]), [])),
            cover_image_url=row["cover_image_url"],
            feed_posts_30d=int(row["feed_posts_30d"]),
            activity_score=float(row["activity_score"]),
            is_full=bool(row["is_full"]),
            is_active=bool(row["is_active"]),
            cluster_id=int(row["dedupe_cluster_id"]),
            location_key=row["location_key"],
            location_label=row["location_label"],
        )
        for row in rows
    ]
