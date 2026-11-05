import os
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
SEED_DATA_DIR: Final = PROJECT_ROOT / "data" / "seed" / "data"
SCHEMA_PATH: Final = PROJECT_ROOT / "schema.sql"
DEFAULT_DATABASE_PATH: Final = PROJECT_ROOT / "data" / "app.db"

DATABASE_PATH_ENV: Final = "CIRCLES_DB_PATH"
REFERENCE_TIME_ENV: Final = "CIRCLES_REFERENCE_TIME"


def database_path() -> Path:
    return Path(os.environ.get(DATABASE_PATH_ENV, str(DEFAULT_DATABASE_PATH)))


def reference_time_override() -> datetime | None:
    raw = os.environ.get(REFERENCE_TIME_ENV)
    if not raw:
        return None
    parsed = datetime.fromisoformat(raw)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


DEFAULT_LIMIT: Final = 10
MIN_LIMIT: Final = 1
MAX_LIMIT: Final = 50

INACTIVE_AFTER_DAYS: Final = 45.0
MIN_POSTS_30D_TO_BE_ACTIVE: Final = 1

RECENCY_HALF_LIFE_DAYS: Final = 14.0
POSTS_30D_SATURATION: Final = 20
CHAT_30D_SATURATION: Final = 200
ENGAGEMENT_PER_POST_SATURATION: Final = 20.0
ACTIVITY_WINDOW_DAYS: Final = 30
ACTIVITY_COMPONENT_WEIGHTS: Final = MappingProxyType(
    {"posts": 0.35, "chat": 0.25, "engagement": 0.15, "recency": 0.25}
)

SOFT_CIRCLE_SIZE: Final = 15
SEATS_FOR_FULL_ROOM_SCORE: Final = 4
OPEN_JOIN_POLICY_SCORE: Final = 1.0
REQUEST_JOIN_POLICY_SCORE: Final = 0.6
OPENNESS_ROOM_SHARE: Final = 0.6

VIRTUAL_FIT: Final = 1.0
LOCAL_FIT: Final = 1.0
HYBRID_NOT_LOCAL_FIT: Final = 0.7
IN_PERSON_UNKNOWN_LOCATION_FIT: Final = 0.5
NON_METRO_LOCATIONS: Final = frozenset({"remote"})

STATED_INTEREST_STRENGTH: Final = 1.0
IMPLIED_INTEREST_STRENGTH: Final = 0.5
PRIMARY_TOPIC_MATCH: Final = 1.0
TAG_TOPIC_MATCH: Final = 0.4
EXTRA_MATCHED_INTEREST_BONUS: Final = 0.15

PROFILE_PRIMARY_TOPIC_MATCH: Final = 1.0
PROFILE_TAG_MATCH: Final = 0.5
PROFILE_KEYWORD_TOPICS: Final = MappingProxyType(
    {
        "leadership": ("leadership-skills",),
        "leaders": ("leadership-skills",),
        "executive presence": ("leadership-skills", "public-speaking"),
        "first-time manager": ("managing-a-team",),
        "engineering manager": ("managing-a-team",),
        "operations manager": ("managing-a-team",),
        "sales manager": ("managing-a-team",),
        "director": ("leadership-skills",),
        "founder": ("leadership-skills",),
        "comp conversation": ("negotiation",),
        "pay equity": ("negotiation",),
        "confidence": ("confidence",),
        "next level": ("getting-promoted",),
        "promotion": ("getting-promoted",),
        "career break": ("career-breaks",),
        "mentoring": ("sponsorship-mentorship",),
    }
)

FEATURES: Final = ("topic", "activity", "location", "profile", "openness")
PERSONALIZED_WEIGHTS: Final = MappingProxyType(
    {"topic": 0.40, "activity": 0.25, "location": 0.15, "profile": 0.10, "openness": 0.10}
)
NEW_MEMBER_WEIGHTS: Final = MappingProxyType(
    {"topic": 0.40, "activity": 0.25, "location": 0.15, "profile": 0.05, "openness": 0.15}
)
COLD_START_WEIGHTS: Final = MappingProxyType(
    {"topic": 0.0, "activity": 0.50, "location": 0.30, "profile": 0.0, "openness": 0.20}
)
NEW_MEMBER_DAYS: Final = 30

CONFIDENCE_INTEREST_SHARE: Final = 0.7
CONFIDENCE_COMPLETENESS_SHARE: Final = 0.3
INTERESTS_FOR_FULL_CONFIDENCE: Final = 2.0
IMPLIED_TOPIC_EVIDENCE: Final = 0.25
IMPLIED_EVIDENCE_CAP: Final = 0.5
PERSONALIZED_CONFIDENCE_MIN: Final = 0.75

MAX_PER_TOPIC: Final = 2
COLD_START_MAX_PER_TOPIC: Final = 1

DEDUPE_NAME_OVERLAP_MIN: Final = 1.0
NAME_STOPWORDS: Final = frozenset(
    {"a", "an", "and", "at", "for", "in", "like", "of", "the", "to", "with", "who", "women"}
)
GENERIC_GROUP_NOUNS: Final = frozenset(
    {"circle", "circles", "collective", "group", "guild", "lab", "room", "table", "club", "society"}
)
STEM_SUFFIXES: Final = (
    "ations",
    "ation",
    "ating",
    "ates",
    "ate",
    "ence",
    "ent",
    "ers",
    "er",
    "ship",
    "ing",
    "s",
)
MIN_STEM_LENGTH: Final = 4

SCORE_DECIMALS: Final = 6
REASON_MIN_CONTRIBUTION: Final = 0.02
ACTIVE_REASON_MIN_POSTS: Final = 4
VERY_ACTIVE_MIN_POSTS: Final = 10
EXPLANATION_MAX_CHARS: Final = 140
EXPLANATION_CLAUSES: Final = 2
