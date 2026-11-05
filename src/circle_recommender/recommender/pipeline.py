from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from circle_recommender import config
from circle_recommender.recommender.diversify import diversify
from circle_recommender.recommender.explain import build_reasons, explain
from circle_recommender.recommender.features import (
    Signal,
    activity_signal,
    location_signal,
    openness_signal,
    profile_signal,
    topic_signal,
)
from circle_recommender.recommender.filters import split_eligible
from circle_recommender.recommender.models import (
    Circle,
    FeatureVector,
    Member,
    Recommendations,
    ScoredCircle,
    Strategy,
)
from circle_recommender.recommender.scoring import (
    choose_strategy,
    effective_weights,
    is_new_member,
    weighted_contributions,
)
from circle_recommender.recommender.text import topics_from_text


@dataclass(frozen=True, slots=True)
class ScoringContext:
    member: Member
    profile_topics: frozenset[str]
    labels: Mapping[str, str]
    weights: Mapping[str, float]
    strategy: Strategy


def compute_signals(context: ScoringContext, circle: Circle) -> dict[str, Signal]:
    return {
        "topic": topic_signal(context.member, circle, context.labels),
        "activity": activity_signal(circle),
        "location": location_signal(context.member, circle),
        "profile": profile_signal(context.profile_topics, circle, context.labels),
        "openness": openness_signal(circle),
    }


def score_circle(context: ScoringContext, circle: Circle) -> ScoredCircle:
    signals = compute_signals(context, circle)
    features = FeatureVector(
        **{name: round(signal.value, config.SCORE_DECIMALS) for name, signal in signals.items()}
    )
    contributions = weighted_contributions(features.as_dict(), context.weights)
    reasons, explanation = explain(
        circle, build_reasons(signals, context.weights), context.strategy, context.labels
    )
    return ScoredCircle(
        circle=circle,
        features=features,
        contributions={name: round(value, config.SCORE_DECIMALS) for name, value in contributions.items()},
        score=round(sum(contributions.values()), config.SCORE_DECIMALS),
        reasons=reasons,
        explanation=explanation,
    )


def uncapped_topics(member: Member, strategy: Strategy) -> frozenset[str]:
    if strategy is not Strategy.COLD_START and len(member.stated_topics) == 1:
        return frozenset(member.stated_topics)
    return frozenset()


def recommend(
    member: Member,
    circles: Sequence[Circle],
    labels: Mapping[str, str],
    reference_time: datetime,
    limit: int = config.DEFAULT_LIMIT,
) -> Recommendations:
    strategy, confidence = choose_strategy(member)
    weights = effective_weights(confidence, is_new_member(member, reference_time))
    context = ScoringContext(
        member=member,
        profile_topics=topics_from_text(member.profile_text, config.PROFILE_KEYWORD_TOPICS),
        labels=labels,
        weights=weights,
        strategy=strategy,
    )
    eligible, filtered = split_eligible(member, circles)
    scored = [score_circle(context, circle) for circle in eligible]
    ranked = sorted(scored, key=lambda item: (-item.score, item.circle.id))
    kept, dropped = diversify(ranked, strategy, uncapped_topics(member, strategy))
    return Recommendations(
        strategy=strategy,
        confidence=confidence,
        weights=weights,
        items=tuple(kept[:limit]),
        filtered=tuple(filtered),
        diversified_out=tuple(dropped),
    )
