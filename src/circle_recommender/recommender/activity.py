import math
from collections.abc import Sequence

from circle_recommender import config


def log_scaled(value: float, saturation: float) -> float:
    if value <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(saturation))


def recency_decay(days_since: float, half_life_days: float = config.RECENCY_HALF_LIFE_DAYS) -> float:
    return float(0.5 ** (max(0.0, days_since) / half_life_days))


def engagement_per_post(engagements: Sequence[int]) -> float:
    return sum(engagements) / len(engagements) if engagements else 0.0


def activity_score(posts_30d: int, chat_30d: int, engagement: float, days_since_last: float) -> float:
    weights = config.ACTIVITY_COMPONENT_WEIGHTS
    score = (
        weights["posts"] * log_scaled(posts_30d, config.POSTS_30D_SATURATION)
        + weights["chat"] * log_scaled(chat_30d, config.CHAT_30D_SATURATION)
        + weights["engagement"] * log_scaled(engagement, config.ENGAGEMENT_PER_POST_SATURATION)
        + weights["recency"] * recency_decay(days_since_last)
    )
    return round(min(1.0, score), config.SCORE_DECIMALS)


def is_active(posts_30d: int, days_since_last: float) -> bool:
    return posts_30d >= config.MIN_POSTS_30D_TO_BE_ACTIVE and days_since_last <= config.INACTIVE_AFTER_DAYS


def is_full(member_count: int, max_members: int | None) -> bool:
    return max_members is not None and member_count >= max_members


def seats_left(member_count: int, max_members: int | None) -> int | None:
    return None if max_members is None else max(0, max_members - member_count)
