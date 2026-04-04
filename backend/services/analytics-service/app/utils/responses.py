from __future__ import annotations

from typing import Any


def success_response(data: Any, status: str = "success") -> dict[str, Any]:
    return {
        "status": status,
        "data": data,
        "error": None,
    }
