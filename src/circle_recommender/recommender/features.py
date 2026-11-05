from collections.abc import Mapping
from dataclasses import dataclass

from circle_recommender import config
from circle_recommender.recommender.models import Circle, CircleFormat, Member, ReasonCode
from circle_recommender.recommender.text import join_labels


@dataclass(frozen=True, slots=True)
class Signal:
    value: float
    code: ReasonCode | None = None
    detail: str = ""
    phrase: str = ""


NO_SIGNAL = Signal(0.0)


def _match_strength(topic: str, circle: Circle) -> float:
    if topic == circle.primary_topic:
        return config.PRIMARY_TOPIC_MATCH
    if topic in circle.tags:
        return config.TAG_TOPIC_MATCH
    return 0.0


def _ordered_labels(topics: list[str], circle: Circle, labels: Mapping[str, str]) -> list[str]:
    ranked = sorted(topics, key=lambda topic: (topic != circle.primary_topic, topic))
    return [labels.get(topic, topic).lower() for topic in ranked]


def topic_signal(member: Member, circle: Circle, labels: Mapping[str, str]) -> Signal:
    stated = [t for t in member.stated_topics if _match_strength(t, circle) > 0]
    implied = [t for t in member.implied_topics if t not in stated and _match_strength(t, circle) > 0]
    if not stated and not implied:
        return NO_SIGNAL
    strengths = [config.STATED_INTEREST_STRENGTH * _match_strength(t, circle) for t in stated] + [
        config.IMPLIED_INTEREST_STRENGTH * _match_strength(t, circle) for t in implied
    ]
    extra_matches = len(strengths) - 1
    value = min(1.0, max(strengths) + config.EXTRA_MATCHED_INTEREST_BONUS * extra_matches)
    if stated:
        names = join_labels(_ordered_labels(stated, circle, labels))
        if circle.primary_topic in stated:
            return Signal(value, ReasonCode.TOPIC_MATCH, names, f"matches your interest in {names}")
        return Signal(value, ReasonCode.TAG_MATCH, names, f"also covers {names}, which you're interested in")
    names = join_labels(_ordered_labels(implied, circle, labels)[:1])
    return Signal(
        value,
        ReasonCode.RELATED_TO_YOUR_CIRCLES,
        names,
        f"builds on {names}, a topic from Circles you're already in",
    )


def profile_signal(profile_topics: frozenset[str], circle: Circle, labels: Mapping[str, str]) -> Signal:
    if circle.primary_topic is not None and circle.primary_topic in profile_topics:
        value, topic = config.PROFILE_PRIMARY_TOPIC_MATCH, circle.primary_topic
    else:
        tag_hits = sorted(tag for tag in circle.tags if tag in profile_topics)
        if not tag_hits:
            return NO_SIGNAL
        value, topic = config.PROFILE_TAG_MATCH, tag_hits[0]
    label = labels.get(topic, topic).lower()
    return Signal(value, ReasonCode.PROFILE_MATCH, label, f"fits your profile's focus on {label}")


def activity_signal(circle: Circle) -> Signal:
    posts = circle.feed_posts_30d
    if posts >= config.VERY_ACTIVE_MIN_POSTS:
        code: ReasonCode | None = ReasonCode.VERY_ACTIVE
    elif posts >= config.ACTIVE_REASON_MIN_POSTS:
        code = ReasonCode.ACTIVE
    else:
        return Signal(circle.activity_score)
    return Signal(
        circle.activity_score,
        code,
        f"{posts} posts in the last 30 days",
        f"members posted {posts} times this month",
    )


def is_local(member: Member, circle: Circle) -> bool:
    return member.location_key is not None and member.location_key == circle.location_key


def is_out_of_area(member: Member, circle: Circle) -> bool:
    return (
        circle.format is CircleFormat.IN_PERSON
        and member.location_key is not None
        and circle.location_key is not None
        and member.location_key != circle.location_key
    )


def location_signal(member: Member, circle: Circle) -> Signal:
    if circle.format is CircleFormat.VIRTUAL:
        return Signal(
            config.VIRTUAL_FIT, ReasonCode.VIRTUAL, "virtual", "meets online, so you can join from anywhere"
        )
    if is_local(member, circle):
        city = member.location_label or ""
        suffix = " and online" if circle.format is CircleFormat.HYBRID else ""
        return Signal(config.LOCAL_FIT, ReasonCode.NEAR_YOU, city, f"meets near you in {city}{suffix}")
    if circle.format is CircleFormat.HYBRID:
        return Signal(
            config.HYBRID_NOT_LOCAL_FIT, ReasonCode.HYBRID, "hybrid", "meets both online and in person"
        )
    if is_out_of_area(member, circle):
        return NO_SIGNAL
    return Signal(config.IN_PERSON_UNKNOWN_LOCATION_FIT)


def room_score(circle: Circle) -> float:
    if circle.seats_left is None:
        return min(1.0, config.SOFT_CIRCLE_SIZE / max(circle.member_count, 1))
    return min(1.0, circle.seats_left / config.SEATS_FOR_FULL_ROOM_SCORE)


def openness_signal(circle: Circle) -> Signal:
    join_score = config.OPEN_JOIN_POLICY_SCORE if circle.is_open else config.REQUEST_JOIN_POLICY_SCORE
    value = config.OPENNESS_ROOM_SHARE * room_score(circle) + (1 - config.OPENNESS_ROOM_SHARE) * join_score
    if circle.is_open:
        return Signal(
            value, ReasonCode.OPEN_TO_JOIN, "open join policy", "welcomes new members to join right away"
        )
    detail = "no member cap" if circle.seats_left is None else f"{circle.seats_left} open spots"
    return Signal(value, ReasonCode.HAS_ROOM, detail, "has room for new members")
