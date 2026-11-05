from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations

from circle_recommender import config
from circle_recommender.recommender.text import name_tokens, overlap_coefficient


@dataclass(frozen=True, slots=True)
class DedupeInput:
    circle_id: int
    name: str
    primary_topic: str | None


def are_near_duplicates(left: DedupeInput, right: DedupeInput) -> bool:
    if left.primary_topic is None or left.primary_topic != right.primary_topic:
        return False
    similarity = overlap_coefficient(name_tokens(left.name), name_tokens(right.name))
    return similarity >= config.DEDUPE_NAME_OVERLAP_MIN


def cluster_circles(circles: Sequence[DedupeInput]) -> dict[int, int]:
    parent = {circle.circle_id: circle.circle_id for circle in circles}

    def root(circle_id: int) -> int:
        while parent[circle_id] != circle_id:
            parent[circle_id] = parent[parent[circle_id]]
            circle_id = parent[circle_id]
        return circle_id

    for left, right in combinations(circles, 2):
        if are_near_duplicates(left, right):
            low, high = sorted((root(left.circle_id), root(right.circle_id)))
            parent[high] = low
    return {circle_id: root(circle_id) for circle_id in parent}
