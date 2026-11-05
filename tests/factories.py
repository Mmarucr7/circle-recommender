from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from circle_recommender.recommender.models import Circle, CircleFormat, Member

REFERENCE_TIME = datetime(2026, 9, 21, tzinfo=UTC)
LABELS = {
    "negotiation": "Negotiation",
    "confidence": "Confidence",
    "leadership-skills": "Leadership skills",
    "public-speaking": "Public speaking",
    "getting-promoted": "Getting promoted",
    "networking": "Networking",
}

BASE_MEMBER = Member(
    id=1,
    location_key="seattle-wa",
    location_label="Seattle",
    stated_topics=("negotiation",),
    implied_topics=(),
    joined_circle_ids=frozenset(),
    joined_cluster_ids=frozenset(),
    profile_text="",
    profile_completeness=1.0,
    joined_at=datetime(2025, 1, 1, tzinfo=UTC),
    has_memberships=False,
)

BASE_CIRCLE = Circle(
    id=100,
    name="Test Circle",
    description=None,
    format=CircleFormat.VIRTUAL,
    is_public=True,
    is_open=True,
    member_count=8,
    max_members=12,
    seats_left=4,
    primary_topic="negotiation",
    tags=(),
    cover_image_url=None,
    feed_posts_30d=10,
    activity_score=0.8,
    is_full=False,
    is_active=True,
    cluster_id=100,
    location_key=None,
    location_label=None,
)


def member(**overrides: Any) -> Member:
    return replace(BASE_MEMBER, **overrides)


def circle(**overrides: Any) -> Circle:
    if "id" in overrides and "cluster_id" not in overrides:
        overrides["cluster_id"] = overrides["id"]
    return replace(BASE_CIRCLE, **overrides)
