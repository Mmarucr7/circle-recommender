from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class CircleFormat(StrEnum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


class Strategy(StrEnum):
    PERSONALIZED = "personalized"
    BLENDED = "blended"
    COLD_START = "cold_start"


class FilterReason(StrEnum):
    ALREADY_MEMBER = "ALREADY_MEMBER"
    SAME_AS_JOINED = "SAME_AS_JOINED"
    FULL = "FULL"
    INACTIVE = "INACTIVE"
    UNLISTED = "UNLISTED"
    OUT_OF_AREA = "OUT_OF_AREA"


class ReasonCode(StrEnum):
    TOPIC_MATCH = "TOPIC_MATCH"
    TAG_MATCH = "TAG_MATCH"
    RELATED_TO_YOUR_CIRCLES = "RELATED_TO_YOUR_CIRCLES"
    PROFILE_MATCH = "PROFILE_MATCH"
    VERY_ACTIVE = "VERY_ACTIVE"
    ACTIVE = "ACTIVE"
    NEAR_YOU = "NEAR_YOU"
    VIRTUAL = "VIRTUAL"
    HYBRID = "HYBRID"
    HAS_ROOM = "HAS_ROOM"
    OPEN_TO_JOIN = "OPEN_TO_JOIN"
    GOOD_FIRST_CIRCLE = "GOOD_FIRST_CIRCLE"


@dataclass(frozen=True, slots=True)
class Member:
    id: int
    location_key: str | None
    location_label: str | None
    stated_topics: tuple[str, ...]
    implied_topics: tuple[str, ...]
    joined_circle_ids: frozenset[int]
    joined_cluster_ids: frozenset[int]
    profile_text: str
    profile_completeness: float
    joined_at: datetime
    has_memberships: bool


@dataclass(frozen=True, slots=True)
class Circle:
    id: int
    name: str
    description: str | None
    format: CircleFormat
    is_public: bool
    is_open: bool
    member_count: int
    max_members: int | None
    seats_left: int | None
    primary_topic: str | None
    tags: tuple[str, ...]
    cover_image_url: str | None
    feed_posts_30d: int
    activity_score: float
    is_full: bool
    is_active: bool
    cluster_id: int
    location_key: str | None
    location_label: str | None


@dataclass(frozen=True, slots=True)
class Reason:
    code: ReasonCode
    detail: str
    phrase: str
    contribution: float


@dataclass(frozen=True, slots=True)
class FeatureVector:
    topic: float
    activity: float
    location: float
    profile: float
    openness: float

    def as_dict(self) -> dict[str, float]:
        return {
            "topic": self.topic,
            "activity": self.activity,
            "location": self.location,
            "profile": self.profile,
            "openness": self.openness,
        }


@dataclass(frozen=True, slots=True)
class ScoredCircle:
    circle: Circle
    features: FeatureVector
    contributions: dict[str, float]
    score: float
    reasons: tuple[Reason, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class FilteredCircle:
    circle_id: int
    reasons: tuple[FilterReason, ...]


@dataclass(frozen=True, slots=True)
class Recommendations:
    strategy: Strategy
    confidence: float
    weights: dict[str, float]
    items: tuple[ScoredCircle, ...]
    filtered: tuple[FilteredCircle, ...] = field(default=())
    diversified_out: tuple[int, ...] = field(default=())
