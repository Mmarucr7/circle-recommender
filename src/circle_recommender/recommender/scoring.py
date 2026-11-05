from collections.abc import Mapping
from datetime import datetime

from circle_recommender import config
from circle_recommender.recommender.models import Member, Strategy


def personalization_confidence(member: Member) -> float:
    stated_share = min(1.0, len(member.stated_topics) / config.INTERESTS_FOR_FULL_CONFIDENCE)
    implied_share = min(
        config.IMPLIED_EVIDENCE_CAP, config.IMPLIED_TOPIC_EVIDENCE * len(member.implied_topics)
    )
    interest_share = min(1.0, stated_share + implied_share)
    confidence = (
        config.CONFIDENCE_INTEREST_SHARE * interest_share
        + config.CONFIDENCE_COMPLETENESS_SHARE * member.profile_completeness
    )
    return round(min(1.0, confidence), config.SCORE_DECIMALS)


def choose_strategy(member: Member) -> tuple[Strategy, float]:
    if not member.stated_topics and not member.has_memberships:
        return Strategy.COLD_START, 0.0
    confidence = personalization_confidence(member)
    if confidence >= config.PERSONALIZED_CONFIDENCE_MIN:
        return Strategy.PERSONALIZED, confidence
    return Strategy.BLENDED, confidence


def is_new_member(member: Member, reference_time: datetime) -> bool:
    return (reference_time - member.joined_at).days <= config.NEW_MEMBER_DAYS


def effective_weights(confidence: float, new_member: bool) -> dict[str, float]:
    personal = config.NEW_MEMBER_WEIGHTS if new_member else config.PERSONALIZED_WEIGHTS
    return {
        name: round(
            confidence * personal[name] + (1 - confidence) * config.COLD_START_WEIGHTS[name],
            config.SCORE_DECIMALS,
        )
        for name in config.FEATURES
    }


def weighted_contributions(features: Mapping[str, float], weights: Mapping[str, float]) -> dict[str, float]:
    return {name: weights[name] * features[name] for name in config.FEATURES}
