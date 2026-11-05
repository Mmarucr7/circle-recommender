from datetime import timedelta

import pytest
from factories import LABELS, REFERENCE_TIME, circle, member

from circle_recommender import config
from circle_recommender.recommender.diversify import diversify
from circle_recommender.recommender.models import Strategy
from circle_recommender.recommender.pipeline import recommend
from circle_recommender.recommender.scoring import (
    choose_strategy,
    effective_weights,
    is_new_member,
    personalization_confidence,
)


@pytest.mark.parametrize(
    "weights",
    [config.PERSONALIZED_WEIGHTS, config.NEW_MEMBER_WEIGHTS, config.COLD_START_WEIGHTS],
)
def test_weight_sets_sum_to_one(weights: dict[str, float]) -> None:
    assert sum(weights.values()) == pytest.approx(1.0)


class TestConfidence:
    def test_full_profile_with_two_interests_is_fully_personalized(self) -> None:
        full = member(stated_topics=("a", "b"), profile_completeness=1.0)

        assert personalization_confidence(full) == 1.0
        assert choose_strategy(full) == (Strategy.PERSONALIZED, 1.0)

    def test_no_interests_and_no_memberships_is_cold_start(self) -> None:
        empty = member(stated_topics=(), profile_completeness=0.8)

        assert choose_strategy(empty) == (Strategy.COLD_START, 0.0)

    def test_implied_interests_alone_cap_below_personalized(self) -> None:
        implied_only = member(
            stated_topics=(), implied_topics=tuple("abcdef"), has_memberships=True, profile_completeness=1.0
        )
        strategy, confidence = choose_strategy(implied_only)

        assert strategy is Strategy.BLENDED
        assert confidence == pytest.approx(0.7 * config.IMPLIED_EVIDENCE_CAP + 0.3)

    def test_completeness_raises_confidence(self) -> None:
        sparse = member(stated_topics=("a",), profile_completeness=0.2)
        complete = member(stated_topics=("a",), profile_completeness=1.0)

        assert personalization_confidence(sparse) < personalization_confidence(complete)


class TestBlending:
    def test_zero_confidence_uses_cold_start_weights(self) -> None:
        assert effective_weights(0.0, new_member=False) == pytest.approx(dict(config.COLD_START_WEIGHTS))

    def test_full_confidence_uses_personalized_weights(self) -> None:
        assert effective_weights(1.0, new_member=False) == pytest.approx(dict(config.PERSONALIZED_WEIGHTS))

    def test_blend_is_linear_in_confidence(self) -> None:
        blended = effective_weights(0.5, new_member=False)
        for name in config.FEATURES:
            expected = 0.5 * config.PERSONALIZED_WEIGHTS[name] + 0.5 * config.COLD_START_WEIGHTS[name]
            assert blended[name] == pytest.approx(expected)

    def test_new_members_get_more_weight_on_openness(self) -> None:
        assert effective_weights(1.0, True)["openness"] > effective_weights(1.0, False)["openness"]
        recent = member(joined_at=REFERENCE_TIME - timedelta(days=3))
        assert is_new_member(recent, REFERENCE_TIME)
        assert not is_new_member(member(), REFERENCE_TIME)


class TestPipeline:
    def test_topic_match_outranks_a_busier_unrelated_circle(self) -> None:
        matching = circle(id=1, primary_topic="negotiation", activity_score=0.6, feed_posts_30d=5)
        unrelated = circle(id=2, primary_topic="networking", activity_score=0.95, feed_posts_30d=20)

        result = recommend(member(), [unrelated, matching], LABELS, REFERENCE_TIME)

        assert [item.circle.id for item in result.items] == [1, 2]

    def test_one_result_per_cluster_and_best_one_wins(self) -> None:
        weaker = circle(id=1, cluster_id=1, activity_score=0.4, feed_posts_30d=3)
        stronger = circle(id=2, cluster_id=1, activity_score=0.9, feed_posts_30d=15)

        result = recommend(member(), [weaker, stronger], LABELS, REFERENCE_TIME)

        assert [item.circle.id for item in result.items] == [2]
        assert result.diversified_out == (1,)

    def test_ties_break_by_circle_id(self) -> None:
        result = recommend(member(), [circle(id=9), circle(id=3)], LABELS, REFERENCE_TIME)

        assert [item.circle.id for item in result.items] == [3, 9]

    def test_limit_is_respected(self) -> None:
        circles = [circle(id=i, primary_topic=f"t{i}") for i in range(1, 8)]

        assert len(recommend(member(), circles, LABELS, REFERENCE_TIME, limit=3).items) == 3


class TestDiversify:
    def test_topic_cap_applies_with_several_interests(self) -> None:
        circles = [circle(id=i, primary_topic="negotiation") for i in (1, 2, 3)]
        two_interests = member(stated_topics=("negotiation", "confidence"))

        result = recommend(two_interests, circles, LABELS, REFERENCE_TIME)

        assert len(result.items) == config.MAX_PER_TOPIC

    def test_topic_cap_is_lifted_for_a_single_stated_interest(self) -> None:
        circles = [circle(id=i, primary_topic="negotiation") for i in (1, 2, 3)]

        result = recommend(member(stated_topics=("negotiation",)), circles, LABELS, REFERENCE_TIME)

        assert len(result.items) == 3

    def test_cold_start_allows_one_circle_per_topic(self) -> None:
        circles = [circle(id=i, primary_topic="negotiation") for i in (1, 2)]
        empty = member(stated_topics=())

        result = recommend(empty, circles, LABELS, REFERENCE_TIME)

        assert result.strategy is Strategy.COLD_START
        assert len(result.items) == 1

    def test_circles_without_a_topic_share_one_bucket(self) -> None:
        circles = [circle(id=i, primary_topic=None) for i in (1, 2, 3)]

        result = recommend(member(stated_topics=("a", "b")), circles, LABELS, REFERENCE_TIME)

        assert [item.circle.id for item in result.items] == [1, 2]
        assert result.diversified_out == (3,)

    def test_diversify_keeps_rank_order(self) -> None:
        circles = [circle(id=i, primary_topic=f"t{i}") for i in (1, 2, 3)]
        ranked = recommend(member(), circles, LABELS, REFERENCE_TIME).items

        kept, dropped = diversify(list(reversed(ranked)), Strategy.PERSONALIZED, frozenset())

        assert [item.circle.id for item in kept] == [3, 2, 1]
        assert dropped == []
