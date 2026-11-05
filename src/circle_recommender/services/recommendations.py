import sqlite3
from dataclasses import dataclass
from datetime import datetime

from circle_recommender.db import queries
from circle_recommender.recommender.models import Recommendations
from circle_recommender.recommender.pipeline import recommend


class UserNotFoundError(LookupError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"User {user_id} does not exist.")
        self.user_id = user_id


@dataclass(frozen=True, slots=True)
class RecommendationRun:
    user_id: int
    reference_time: datetime
    topic_labels: dict[str, str]
    result: Recommendations


def recommend_for_user(
    connection: sqlite3.Connection, user_id: int, limit: int, include_unavailable: bool = False
) -> RecommendationRun:
    member = queries.fetch_member(connection, user_id)
    if member is None:
        raise UserNotFoundError(user_id)
    reference_time = queries.fetch_reference_time(connection)
    labels = queries.fetch_topic_labels(connection)
    circles = queries.fetch_circles(connection, include_unavailable=include_unavailable)
    result = recommend(member, circles, labels, reference_time, limit)
    return RecommendationRun(user_id, reference_time, labels, result)
