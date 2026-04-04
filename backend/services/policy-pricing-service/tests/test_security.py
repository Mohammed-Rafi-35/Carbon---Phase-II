from __future__ import annotations

import pytest

from app.core.exceptions import AppError
from app.core.security import decode_access_token


def test_decode_invalid_token_raises():
    with pytest.raises(AppError) as exc:
        decode_access_token("not-a-valid-token")

    assert exc.value.error_code == "INVALID_TOKEN"
