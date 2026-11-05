import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi import Path as PathParam

from circle_recommender import config
from circle_recommender.api.schemas import (
    ErrorResponse,
    HealthResponse,
    RecommendationsResponse,
    recommendations_response,
)
from circle_recommender.db.connection import read_only_connection
from circle_recommender.services.recommendations import recommend_for_user

router = APIRouter()


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    database_path: Path = request.app.state.database_path
    with read_only_connection(database_path) as connection:
        yield connection


Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse(status="ok")


@router.get(
    "/users/{user_id}/recommendations",
    response_model=RecommendationsResponse,
    response_model_exclude_unset=True,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    tags=["recommendations"],
)
def get_recommendations(
    connection: Connection,
    user_id: Annotated[int, PathParam(ge=1, description="Member to recommend Circles for.")],
    limit: Annotated[int, Query(ge=config.MIN_LIMIT, le=config.MAX_LIMIT)] = config.DEFAULT_LIMIT,
    debug: Annotated[bool, Query(description="Include scores, weights and filtered Circles.")] = False,
) -> RecommendationsResponse:
    """Ranked Circles for a member, each with a short explanation written for the member.

    `strategy` says how much the ranking relies on the member's profile: `personalized`, `blended`
    (profile signals mixed with popular, accessible Circles) or `cold_start`. Set `debug=true` to see
    each Circle's feature breakdown, the weights used, and every Circle that was filtered out with
    its reason codes.
    """
    run = recommend_for_user(connection, user_id, limit, include_unavailable=debug)
    return recommendations_response(run, debug)
