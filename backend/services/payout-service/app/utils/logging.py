from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from app.utils.log_context import get_request_id


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.service = "payout-service"
        record.operation = getattr(record, "operation", record.funcName)
        return True


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.getMessage())
        if "Authorization" in message or "Bearer" in message:
            record.msg = "Authentication header redacted"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(request_id)s %(service)s %(operation)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]
