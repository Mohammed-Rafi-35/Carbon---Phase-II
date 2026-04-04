from __future__ import annotations

from app.core.constants import NotificationType
from app.core.exceptions import AppError


class TemplateService:
    _templates = {
        NotificationType.CLAIM_UPDATE: "Claim status update: {message}",
        NotificationType.PAYOUT: "Payout update: {message}",
        NotificationType.POLICY: "Policy update: {message}",
        "default": "{message}",
    }

    def render(self, *, type_: str, message: str | None, template_name: str | None, variables: dict[str, str]) -> str:
        if message:
            variables = {**variables, "message": message}

        if template_name:
            template = self._templates.get(template_name)
            if not template:
                raise AppError("Unknown template name.", "INVALID_TEMPLATE", 400)
        else:
            template = self._templates.get(type_, self._templates["default"])

        try:
            return template.format(**variables)
        except KeyError as exc:
            raise AppError("Template variables are incomplete.", "INVALID_TEMPLATE_VARIABLES", 400) from exc
