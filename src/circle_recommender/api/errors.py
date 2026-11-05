from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from circle_recommender.api.schemas import ErrorBody, ErrorResponse
from circle_recommender.db.connection import DatabaseNotReadyError
from circle_recommender.services.recommendations import UserNotFoundError

HTTP_ERROR_CODES = {
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
}


def error_response(
    status_code: int, code: str, message: str, details: list[dict[str, object]]
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def handle_user_not_found(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_404_NOT_FOUND, "user_not_found", str(exc), [])


async def handle_validation(_: Request, exc: Exception) -> JSONResponse:
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    details: list[dict[str, object]] = [
        {"location": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in errors
    ]
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", "Request parameters are invalid.", details
    )


async def handle_http(_: Request, exc: Exception) -> JSONResponse:
    status_code = exc.status_code if isinstance(exc, HTTPException) else status.HTTP_500_INTERNAL_SERVER_ERROR
    message = str(exc.detail) if isinstance(exc, HTTPException) else "Unexpected error."
    return error_response(status_code, HTTP_ERROR_CODES.get(status_code, "http_error"), message, [])


async def handle_database_not_ready(_: Request, exc: Exception) -> JSONResponse:
    return error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "database_not_ready", str(exc), [])


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(UserNotFoundError, handle_user_not_found)
    app.add_exception_handler(RequestValidationError, handle_validation)
    app.add_exception_handler(HTTPException, handle_http)
    app.add_exception_handler(DatabaseNotReadyError, handle_database_not_ready)
