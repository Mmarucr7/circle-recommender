from collections.abc import Mapping
from datetime import datetime

from pydantic import BaseModel, Field

from circle_recommender.recommender.models import CircleFormat, ScoredCircle, Strategy
from circle_recommender.services.recommendations import RecommendationRun


class TopicOut(BaseModel):
    slug: str
    label: str


class CircleOut(BaseModel):
    id: int
    name: str
    description: str | None
    format: CircleFormat
    location: str | None = Field(description="Area an in-person or hybrid Circle meets in, when known.")
    member_count: int
    topics: list[TopicOut]
    cover_image_url: str | None


class ReasonOut(BaseModel):
    code: str
    detail: str


class ItemDebug(BaseModel):
    score: float
    features: dict[str, float]
    contributions: dict[str, float]
    dedupe_cluster_id: int


class RecommendationOut(BaseModel):
    rank: int
    circle: CircleOut
    explanation: str
    reasons: list[ReasonOut]
    debug: ItemDebug | None = None


class FilteredOut(BaseModel):
    circle_id: int
    reasons: list[str]


class ResponseDebug(BaseModel):
    confidence: float
    weights: dict[str, float]
    filtered_out: list[FilteredOut]
    diversified_out: list[int]


class RecommendationsResponse(BaseModel):
    user_id: int
    reference_time: datetime
    strategy: Strategy
    recommendations: list[RecommendationOut]
    debug: ResponseDebug | None = None


class HealthResponse(BaseModel):
    status: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, object]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody


def circle_topics(item: ScoredCircle, labels: Mapping[str, str]) -> list[TopicOut]:
    circle = item.circle
    slugs = ([circle.primary_topic] if circle.primary_topic else []) + [
        tag for tag in circle.tags if tag != circle.primary_topic
    ]
    return [TopicOut(slug=slug, label=labels.get(slug, slug)) for slug in slugs]


def recommendation_out(
    rank: int, item: ScoredCircle, labels: Mapping[str, str], debug: bool
) -> RecommendationOut:
    circle = item.circle
    location = circle.location_label if circle.format is not CircleFormat.VIRTUAL else None
    out = RecommendationOut(
        rank=rank,
        circle=CircleOut(
            id=circle.id,
            name=circle.name,
            description=circle.description,
            format=circle.format,
            location=location,
            member_count=circle.member_count,
            topics=circle_topics(item, labels),
            cover_image_url=circle.cover_image_url,
        ),
        explanation=item.explanation,
        reasons=[ReasonOut(code=reason.code.value, detail=reason.detail) for reason in item.reasons],
    )
    if debug:
        out.debug = ItemDebug(
            score=item.score,
            features=item.features.as_dict(),
            contributions=item.contributions,
            dedupe_cluster_id=circle.cluster_id,
        )
    return out


def recommendations_response(run: RecommendationRun, debug: bool) -> RecommendationsResponse:
    result = run.result
    response = RecommendationsResponse(
        user_id=run.user_id,
        reference_time=run.reference_time,
        strategy=result.strategy,
        recommendations=[
            recommendation_out(rank, item, run.topic_labels, debug)
            for rank, item in enumerate(result.items, start=1)
        ],
    )
    if debug:
        response.debug = ResponseDebug(
            confidence=result.confidence,
            weights=result.weights,
            filtered_out=[
                FilteredOut(circle_id=f.circle_id, reasons=[r.value for r in f.reasons])
                for f in result.filtered
            ],
            diversified_out=list(result.diversified_out),
        )
    return response
