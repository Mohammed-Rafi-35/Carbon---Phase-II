from __future__ import annotations

from fastapi.responses import JSONResponse


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "data": None,
            "error": {
                "code": code,
                "message": message,
            },
        },
        headers=headers,
    )
