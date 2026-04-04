from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.log_context import reset_request_id, set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        context_token = set_request_id(request_id)

        try:
            response = await call_next(request)
        finally:
            reset_request_id(context_token)
        response.headers["X-Request-ID"] = request_id
        return response
