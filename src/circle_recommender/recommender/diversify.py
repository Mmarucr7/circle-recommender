from collections import Counter
from collections.abc import Sequence

from circle_recommender import config
from circle_recommender.recommender.models import ScoredCircle, Strategy

NO_TOPIC_BUCKET = "no-topic"


def topic_cap(strategy: Strategy) -> int:
    return config.COLD_START_MAX_PER_TOPIC if strategy is Strategy.COLD_START else config.MAX_PER_TOPIC


def diversify(
    ranked: Sequence[ScoredCircle], strategy: Strategy, uncapped_topics: frozenset[str]
) -> tuple[list[ScoredCircle], list[int]]:
    cap = topic_cap(strategy)
    seen_clusters: set[int] = set()
    per_topic: Counter[str] = Counter()
    kept: list[ScoredCircle] = []
    dropped: list[int] = []
    for item in ranked:
        circle = item.circle
        topic = circle.primary_topic or NO_TOPIC_BUCKET
        over_cap = topic not in uncapped_topics and per_topic[topic] >= cap
        if circle.cluster_id in seen_clusters or over_cap:
            dropped.append(circle.id)
            continue
        seen_clusters.add(circle.cluster_id)
        per_topic[topic] += 1
        kept.append(item)
    return kept, dropped
