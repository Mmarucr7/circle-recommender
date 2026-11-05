import pytest
from factories import LABELS, circle, member

from circle_recommender import config
from circle_recommender.recommender import activity
from circle_recommender.recommender.features import (
    activity_signal,
    location_signal,
    openness_signal,
    profile_signal,
    room_score,
    topic_signal,
)
from circle_recommender.recommender.filters import filter_reasons
from circle_recommender.recommender.models import CircleFormat, FilterReason, ReasonCode
from circle_recommender.recommender.text import normalise_location, topics_from_text


class TestTopicSignal:
    def test_primary_topic_match_is_full_strength(self) -> None:
        signal = topic_signal(member(stated_topics=("negotiation",)), circle(), LABELS)

        assert signal.value == 1.0
        assert signal.code is ReasonCode.TOPIC_MATCH
        assert signal.phrase == "matches your interest in negotiation"

    def test_tag_only_match_is_weaker(self) -> None:
        signal = topic_signal(
            member(stated_topics=("confidence",)),
            circle(primary_topic="networking", tags=("confidence",)),
            LABELS,
        )

        assert signal.value == config.TAG_TOPIC_MATCH
        assert signal.code is ReasonCode.TAG_MATCH

    def test_implied_interest_counts_at_half_strength(self) -> None:
        signal = topic_signal(member(stated_topics=(), implied_topics=("negotiation",)), circle(), LABELS)

        assert signal.value == config.IMPLIED_INTEREST_STRENGTH
        assert signal.code is ReasonCode.RELATED_TO_YOUR_CIRCLES

    def test_second_matching_interest_adds_a_bonus_capped_at_one(self) -> None:
        signal = topic_signal(
            member(stated_topics=("confidence", "networking")),
            circle(primary_topic="networking", tags=("confidence",)),
            LABELS,
        )

        assert signal.value == 1.0
        assert signal.detail == "networking and confidence"

    def test_no_overlap_gives_no_signal(self) -> None:
        signal = topic_signal(member(stated_topics=("confidence",)), circle(), LABELS)

        assert signal.value == 0.0
        assert signal.code is None


class TestProfileSignal:
    def test_bio_keywords_map_to_topics(self) -> None:
        topics = topics_from_text(
            "Senior IC eyeing my first leadership role. Working on executive presence.",
            config.PROFILE_KEYWORD_TOPICS,
        )

        assert topics == {"leadership-skills", "public-speaking"}

    def test_product_manager_is_not_read_as_people_manager(self) -> None:
        assert topics_from_text("Product Manager", config.PROFILE_KEYWORD_TOPICS) == frozenset()

    def test_primary_and_tag_matches(self) -> None:
        profile = frozenset({"negotiation"})

        assert profile_signal(profile, circle(), LABELS).value == config.PROFILE_PRIMARY_TOPIC_MATCH
        tagged = circle(primary_topic="networking", tags=("negotiation",))
        assert profile_signal(profile, tagged, LABELS).value == config.PROFILE_TAG_MATCH
        assert profile_signal(frozenset(), circle(), LABELS).value == 0.0


class TestActivity:
    def test_log_scaling_saturates_at_one(self) -> None:
        assert activity.log_scaled(0, 20) == 0.0
        assert 0 < activity.log_scaled(5, 20) < activity.log_scaled(10, 20) < 1.0
        assert activity.log_scaled(500, 20) == 1.0

    def test_recency_halves_every_half_life(self) -> None:
        assert activity.recency_decay(0) == 1.0
        assert activity.recency_decay(config.RECENCY_HALF_LIFE_DAYS) == pytest.approx(0.5)
        assert activity.recency_decay(2 * config.RECENCY_HALF_LIFE_DAYS) == pytest.approx(0.25)

    def test_activity_score_is_bounded_and_monotonic(self) -> None:
        quiet = activity.activity_score(2, 10, 3.0, 15)
        busy = activity.activity_score(15, 150, 15.0, 1)

        assert 0 <= quiet < busy <= 1

    def test_inactive_after_threshold_or_without_posts(self) -> None:
        assert activity.is_active(5, 20)
        assert not activity.is_active(0, 2)
        assert not activity.is_active(5, config.INACTIVE_AFTER_DAYS + 1)

    def test_capacity_helpers(self) -> None:
        assert activity.is_full(15, 15)
        assert not activity.is_full(30, None)
        assert activity.seats_left(10, 14) == 4
        assert activity.seats_left(10, None) is None

    def test_activity_reason_requires_enough_posts(self) -> None:
        assert activity_signal(circle(feed_posts_30d=12)).code is ReasonCode.VERY_ACTIVE
        assert activity_signal(circle(feed_posts_30d=5)).code is ReasonCode.ACTIVE
        assert activity_signal(circle(feed_posts_30d=2)).code is None


class TestLocation:
    def test_normalise_location(self) -> None:
        assert normalise_location("Seattle, WA") == ("seattle-wa", "Seattle")
        assert normalise_location("Remote") is None
        assert normalise_location(None) is None

    @pytest.mark.parametrize(
        ("circle_format", "circle_location", "expected"),
        [
            (CircleFormat.VIRTUAL, None, config.VIRTUAL_FIT),
            (CircleFormat.HYBRID, "seattle-wa", config.LOCAL_FIT),
            (CircleFormat.HYBRID, "boston-ma", config.HYBRID_NOT_LOCAL_FIT),
            (CircleFormat.IN_PERSON, "seattle-wa", config.LOCAL_FIT),
            (CircleFormat.IN_PERSON, None, config.IN_PERSON_UNKNOWN_LOCATION_FIT),
            (CircleFormat.IN_PERSON, "boston-ma", 0.0),
        ],
    )
    def test_location_fit(
        self, circle_format: CircleFormat, circle_location: str | None, expected: float
    ) -> None:
        target = circle(format=circle_format, location_key=circle_location, location_label=circle_location)

        assert location_signal(member(), target).value == expected

    def test_local_reason_names_the_members_own_city(self) -> None:
        target = circle(format=CircleFormat.IN_PERSON, location_key="seattle-wa", location_label="Seattle")

        assert location_signal(member(), target).phrase == "meets near you in Seattle"


class TestOpenness:
    def test_room_score(self) -> None:
        assert room_score(circle(seats_left=4)) == 1.0
        assert room_score(circle(seats_left=1)) == 0.25
        assert room_score(circle(seats_left=None, max_members=None, member_count=10)) == 1.0
        assert room_score(circle(seats_left=None, max_members=None, member_count=30)) == 0.5

    def test_request_to_join_scores_lower_than_open(self) -> None:
        assert openness_signal(circle(is_open=False)).value < openness_signal(circle(is_open=True)).value
        assert openness_signal(circle(is_open=False)).code is ReasonCode.HAS_ROOM


class TestHardFilters:
    def test_each_filter_has_a_reason_code(self) -> None:
        local = member()
        assert filter_reasons(local, circle(is_full=True)) == (FilterReason.FULL,)
        assert filter_reasons(local, circle(is_active=False)) == (FilterReason.INACTIVE,)
        assert filter_reasons(local, circle(is_public=False)) == (FilterReason.UNLISTED,)
        assert filter_reasons(member(joined_circle_ids=frozenset({100})), circle()) == (
            FilterReason.ALREADY_MEMBER,
        )
        far = circle(format=CircleFormat.IN_PERSON, location_key="boston-ma", location_label="Boston")
        assert filter_reasons(local, far) == (FilterReason.OUT_OF_AREA,)

    def test_unknown_locations_are_never_filtered(self) -> None:
        unknown_member = member(location_key=None, location_label=None)
        far = circle(format=CircleFormat.IN_PERSON, location_key="boston-ma", location_label="Boston")

        assert filter_reasons(unknown_member, far) == ()
        assert filter_reasons(member(), circle(format=CircleFormat.IN_PERSON)) == ()

    def test_same_cluster_as_a_joined_circle(self) -> None:
        joined = member(joined_circle_ids=frozenset({10}), joined_cluster_ids=frozenset({10}))

        assert filter_reasons(joined, circle(id=11, cluster_id=10)) == (FilterReason.SAME_AS_JOINED,)
