from collections.abc import Mapping, Sequence

from circle_recommender import config
from circle_recommender.recommender.features import Signal
from circle_recommender.recommender.models import Circle, CircleFormat, Reason, ReasonCode, Strategy

INDEPENDENT_CLAUSE_CODES = frozenset({ReasonCode.ACTIVE, ReasonCode.VERY_ACTIVE})
ACTIVITY_CODES = INDEPENDENT_CLAUSE_CODES
FORMAT_WORDS: Mapping[CircleFormat, str] = {
    CircleFormat.VIRTUAL: "virtual",
    CircleFormat.HYBRID: "hybrid",
    CircleFormat.IN_PERSON: "in-person",
}
COLD_START_SUFFIX = ", a great place to start."


def build_reasons(signals: Mapping[str, Signal], weights: Mapping[str, float]) -> tuple[Reason, ...]:
    reasons = [
        Reason(
            signal.code,
            signal.detail,
            signal.phrase,
            round(weights[name] * signal.value, config.SCORE_DECIMALS),
        )
        for name, signal in signals.items()
        if signal.code is not None and weights[name] * signal.value >= config.REASON_MIN_CONTRIBUTION
    ]
    return tuple(sorted(reasons, key=lambda reason: (-reason.contribution, reason.code)))


def _capitalise(text: str) -> str:
    return text[:1].upper() + text[1:]


def compose_sentence(reasons: Sequence[Reason]) -> str:
    chosen = list(reasons[: config.EXPLANATION_CLAUSES])
    if not chosen:
        return "Has room for new members."
    ordered = [r for r in chosen if r.code not in INDEPENDENT_CLAUSE_CODES] + [
        r for r in chosen if r.code in INDEPENDENT_CLAUSE_CODES
    ]
    first = _capitalise(ordered[0].phrase)
    if len(ordered) > 1:
        sentence = f"{first}, and {ordered[1].phrase}."
        if len(sentence) <= config.EXPLANATION_MAX_CHARS:
            return sentence
    return f"{first}."


def cold_start_sentence(circle: Circle, reasons: Sequence[Reason], labels: Mapping[str, str]) -> str:
    codes = {reason.code for reason in reasons}
    active = bool(codes & ACTIVITY_CODES)
    format_word = "local" if ReasonCode.NEAR_YOU in codes else FORMAT_WORDS[circle.format]
    opener = "An active" if active else "A welcoming"
    middle = (
        f" where members posted {circle.feed_posts_30d} times this month"
        if active
        else " with room for new members"
    )
    topic = labels.get(circle.primary_topic, "").lower() if circle.primary_topic else ""
    with_topic = f"{opener} {format_word} Circle on {topic}{middle}{COLD_START_SUFFIX}"
    if topic and len(with_topic) <= config.EXPLANATION_MAX_CHARS:
        return with_topic
    return f"{opener} {format_word} Circle{middle}{COLD_START_SUFFIX}"


def good_first_circle_reason() -> Reason:
    return Reason(ReasonCode.GOOD_FIRST_CIRCLE, "suggested while we learn your interests", "", 0.0)


def explain(
    circle: Circle, reasons: tuple[Reason, ...], strategy: Strategy, labels: Mapping[str, str]
) -> tuple[tuple[Reason, ...], str]:
    if strategy is Strategy.COLD_START:
        return (good_first_circle_reason(), *reasons), cold_start_sentence(circle, reasons, labels)
    return reasons, compose_sentence(reasons)
