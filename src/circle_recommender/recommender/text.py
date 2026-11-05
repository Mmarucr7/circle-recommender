import re
from collections.abc import Iterable, Mapping

from circle_recommender import config

_WORD = re.compile(r"[a-z0-9]+")


def normalise_location(raw: str | None) -> tuple[str, str] | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned or cleaned.lower() in config.NON_METRO_LOCATIONS:
        return None
    key = "-".join(_WORD.findall(cleaned.lower()))
    label = cleaned.split(",")[0].strip()
    return key, label


def stem(token: str) -> str:
    for suffix in config.STEM_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= config.MIN_STEM_LENGTH:
            return token[: -len(suffix)]
    return token


def name_tokens(name: str) -> frozenset[str]:
    ignored = config.NAME_STOPWORDS | config.GENERIC_GROUP_NOUNS
    words = _WORD.findall(name.lower().replace("&", " and "))
    return frozenset(stem(word) for word in words if word not in ignored)


def overlap_coefficient(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def topics_from_text(text: str, keyword_topics: Mapping[str, Iterable[str]]) -> frozenset[str]:
    lowered = text.lower()
    found: set[str] = set()
    for keyword, topics in keyword_topics.items():
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            found.update(topics)
    return frozenset(found)


def join_labels(labels: Iterable[str]) -> str:
    items = list(labels)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]
