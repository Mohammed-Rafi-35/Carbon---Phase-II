from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


def _error_payload(code: str, message: str) -> dict:
    return {
        "status": "error",
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.error_code, exc.message),
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = str(exc.detail) if exc.detail else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload("HTTP_ERROR", message),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_error_payload("INVALID_INPUT", str(exc)),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
    )
