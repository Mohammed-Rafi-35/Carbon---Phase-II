from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorObject(BaseModel):
    code: str
    message: str


class StandardResponse(BaseModel):
    status: str
    data: Any | None = None
    error: ErrorObject | None = None
