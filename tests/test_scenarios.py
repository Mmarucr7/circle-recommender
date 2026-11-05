from conftest import RunFor

from circle_recommender.recommender.models import FilterReason, Strategy


def circle_ids(run_for: RunFor, user_id: int, top: int | None = None) -> list[int]:
    return [item.circle.id for item in run_for(user_id).result.items[:top]]


def test_cold_start_member_gets_diverse_active_circles(run_for: RunFor) -> None:
    result = run_for(42).result
    topics = [item.circle.primary_topic for item in result.items]

    assert result.strategy is Strategy.COLD_START
    assert len(result.items) == 10
    assert len(set(topics)) == len(topics)
    assert all(item.circle.is_active and not item.circle.is_full for item in result.items)
    assert all("great place to start" in item.explanation for item in result.items)


def test_obvious_matches_rank_in_top_three(run_for: RunFor) -> None:
    top_three = circle_ids(run_for, 7, 3)

    assert {5, 6} <= set(top_three)
    assert run_for(7).result.strategy is Strategy.PERSONALIZED


def test_only_one_of_the_duplicate_negotiation_circles_is_returned(run_for: RunFor) -> None:
    returned = [c for c in circle_ids(run_for, 15) if c in {10, 11, 12}]

    assert len(returned) == 1
    assert circle_ids(run_for, 15, 1) == returned


def test_full_and_inactive_circles_give_way_to_the_healthy_alternative(run_for: RunFor) -> None:
    run = run_for(23, include_unavailable=True)
    filtered = {f.circle_id: f.reasons for f in run.result.filtered}

    assert circle_ids(run_for, 23, 1) == [22]
    assert FilterReason.FULL in filtered[20]
    assert FilterReason.INACTIVE in filtered[21]
    assert {20, 21}.isdisjoint(circle_ids(run_for, 23))


def test_duplicate_of_a_joined_circle_is_filtered(run_for: RunFor) -> None:
    run = run_for(18, include_unavailable=True)
    filtered = {f.circle_id: f.reasons for f in run.result.filtered}

    assert filtered[10] == (FilterReason.SAME_AS_JOINED,)
    assert filtered[11] == (FilterReason.SAME_AS_JOINED,)
