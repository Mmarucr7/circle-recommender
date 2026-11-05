import json

from circle_recommender import config
from circle_recommender.recommender.dedupe import DedupeInput, are_near_duplicates, cluster_circles
from circle_recommender.recommender.text import name_tokens, overlap_coefficient


def test_name_tokens_drop_filler_and_stem() -> None:
    assert name_tokens("The Negotiation Table") == {"negoti"}
    assert name_tokens("Negotiate Like a Leader") == {"negoti", "lead"}
    assert name_tokens("Mentors & Sponsors") == {"mentor", "sponsor"}


def test_overlap_coefficient() -> None:
    assert overlap_coefficient(frozenset({"a"}), frozenset({"a", "b"})) == 1.0
    assert overlap_coefficient(frozenset({"a", "c"}), frozenset({"a", "b"})) == 0.5
    assert overlap_coefficient(frozenset(), frozenset({"a"})) == 0.0


def test_same_name_stem_but_different_topic_is_not_a_duplicate() -> None:
    lead = DedupeInput(5, "Women Who Lead", "leadership-skills")
    negotiate = DedupeInput(12, "Negotiate Like a Leader", "negotiation")

    assert not are_near_duplicates(lead, negotiate)


def test_circles_without_a_topic_never_cluster() -> None:
    assert not are_near_duplicates(DedupeInput(1, "Circle A", None), DedupeInput(2, "Circle A", None))


def test_seed_clusters_match_the_documented_groups() -> None:
    circles = json.loads((config.SEED_DATA_DIR / "circles.json").read_text(encoding="utf-8"))
    clusters = cluster_circles([DedupeInput(c["id"], c["name"], c["topic"]) for c in circles])
    groups: dict[int, set[int]] = {}
    for circle_id, cluster_id in clusters.items():
        groups.setdefault(cluster_id, set()).add(circle_id)

    multi = sorted(sorted(group) for group in groups.values() if len(group) > 1)
    assert multi == [[10, 11, 12], [13, 37]]
    assert clusters[11] == clusters[12] == 10
