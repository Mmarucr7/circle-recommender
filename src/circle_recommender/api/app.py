from pathlib import Path

from fastapi import FastAPI

from circle_recommender import config
from circle_recommender.api.errors import register_error_handlers
from circle_recommender.api.routes import router


def create_app(database_path: Path | None = None) -> FastAPI:
    application = FastAPI(
        title="Lean In Circle Recommendations",
        version="0.1.0",
        description="Recommends Circles a member can join, with a short explanation for each one.",
    )
    application.state.database_path = database_path or config.database_path()
    register_error_handlers(application)
    application.include_router(router)
    return application


app = create_app()
