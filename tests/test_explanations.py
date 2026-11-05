import re
import sqlite3

import pytest
from conftest import RunFor

from circle_recommender import config
from circle_recommender.db import queries
from circle_recommender.recommender.explain import compose_sentence
from circle_recommender.recommender.models import Reason, ReasonCode, ScoredCircle, Strategy

PHRASE_EVIDENCE = {
    "matches your interest": {ReasonCode.TOPIC_MATCH},
    "which you're interested in": {ReasonCode.TAG_MATCH},
    "circles you're already in": {ReasonCode.RELATED_TO_YOUR_CIRCLES},
    "your profile": {ReasonCode.PROFILE_MATCH},
    "members posted": {ReasonCode.ACTIVE, ReasonCode.VERY_ACTIVE},
    "near you": {ReasonCode.NEAR_YOU},
    "meets online": {ReasonCode.VIRTUAL},
    "online and in person": {ReasonCode.HYBRID},
    "welcomes new members": {ReasonCode.OPEN_TO_JOIN},
    "has room for new members": {ReasonCode.HAS_ROOM},
    "great place to start": {ReasonCode.GOOD_FIRST_CIRCLE},
}
BANNED_WORDS = re.compile(
    r"\b(score|weight|feature|personali[sz]ation|algorithm|cluster|strategy|not|no|never|can't|won't)\b", re.I
)


@pytest.fixture
def all_items(connection: sqlite3.Connection, run_for: RunFor) -> list[tuple[Strategy, ScoredCircle]]:
    return [
        (run.result.strategy, item)
        for user_id in queries.fetch_user_ids(connection)
        for run in [run_for(user_id)]
        for item in run.result.items
    ]


def test_explanations_are_short_single_sentences(all_items: list[tuple[Strategy, ScoredCircle]]) -> None:
    for _, item in all_items:
        assert len(item.explanation) <= config.EXPLANATION_MAX_CHARS
        assert item.explanation.endswith(".")
        assert item.explanation.count(".") == 1


def test_explanations_contain_no_scores_jargon_or_negative_wording(
    all_items: list[tuple[Strategy, ScoredCircle]],
) -> None:
    for _, item in all_items:
        assert not re.search(r"\d+\.\d+|%", item.explanation)
        assert not BANNED_WORDS.search(item.explanation), item.explanation


def test_explanations_never_name_other_members(
    connection: sqlite3.Connection, all_items: list[tuple[Strategy, ScoredCircle]]
) -> None:
    names = {
        name
        for row in connection.execute("SELECT first_name, last_name FROM users")
        for name in (str(row["first_name"]), str(row["last_name"]))
    }
    for _, item in all_items:
        words = set(re.findall(r"[A-Z][a-z]+", item.explanation))
        assert not words & names, item.explanation


def test_every_claim_in_an_explanation_is_backed_by_a_reason_code(
    all_items: list[tuple[Strategy, ScoredCircle]],
) -> None:
    for _, item in all_items:
        codes = {reason.code for reason in item.reasons}
        lowered = item.explanation.lower()
        for phrase, backing in PHRASE_EVIDENCE.items():
            if phrase in lowered:
                assert codes & backing, (item.explanation, codes)


def test_numbers_in_explanations_come_from_reason_details(
    all_items: list[tuple[Strategy, ScoredCircle]],
) -> None:
    for _, item in all_items:
        details = " ".join(reason.detail for reason in item.reasons)
        for number in re.findall(r"\d+", item.explanation):
            assert number in details, (item.explanation, details)


def test_personalized_explanations_use_the_top_two_reasons(
    all_items: list[tuple[Strategy, ScoredCircle]],
) -> None:
    for strategy, item in all_items:
        if strategy is not Strategy.COLD_START:
            assert item.explanation == compose_sentence(item.reasons)
            contributions = [reason.contribution for reason in item.reasons]
            assert contributions == sorted(contributions, reverse=True)


def test_activity_clause_is_placed_last_for_grammar() -> None:
    reasons = [
        Reason(
            ReasonCode.VERY_ACTIVE, "12 posts in the last 30 days", "members posted 12 times this month", 0.3
        ),
        Reason(ReasonCode.TOPIC_MATCH, "negotiation", "matches your interest in negotiation", 0.2),
    ]

    assert compose_sentence(reasons) == (
        "Matches your interest in negotiation, and members posted 12 times this month."
    )


def test_overlong_two_clause_sentence_falls_back_to_one_clause() -> None:
    long_phrase = "matches your interest in " + "a" * 120
    reasons = [
        Reason(ReasonCode.TOPIC_MATCH, "x", long_phrase, 0.3),
        Reason(ReasonCode.HAS_ROOM, "3 open spots", "has room for new members", 0.1),
    ]

    assert compose_sentence(reasons) == long_phrase[0].upper() + long_phrase[1:] + "."
