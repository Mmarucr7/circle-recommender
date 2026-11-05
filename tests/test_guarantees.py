import sqlite3

from conftest import RunFor

from circle_recommender.db import queries


def test_every_member_gets_a_non_empty_list(connection: sqlite3.Connection, run_for: RunFor) -> None:
    empty = [user_id for user_id in queries.fetch_user_ids(connection) if not run_for(user_id).result.items]

    assert empty == []


def test_results_are_deterministic(connection: sqlite3.Connection, run_for: RunFor) -> None:
    for user_id in queries.fetch_user_ids(connection):
        first, second = run_for(user_id).result, run_for(user_id).result
        assert first == second


def test_debug_mode_does_not_change_the_ranking(connection: sqlite3.Connection, run_for: RunFor) -> None:
    for user_id in queries.fetch_user_ids(connection):
        normal = [item.circle.id for item in run_for(user_id).result.items]
        debug = [item.circle.id for item in run_for(user_id, include_unavailable=True).result.items]
        assert normal == debug


def test_sparse_profiles_get_full_length_lists(connection: sqlite3.Connection, run_for: RunFor) -> None:
    sparse = [
        user_id
        for user_id in queries.fetch_user_ids(connection)
        if (member := queries.fetch_member(connection, user_id)) and member.profile_completeness <= 0.4
    ]

    assert sparse
    assert all(len(run_for(user_id).result.items) == 10 for user_id in sparse)
