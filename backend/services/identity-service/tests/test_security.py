from __future__ import annotations

from app.core.exceptions import AppError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing_roundtrip():
    plain = "SecurePass123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_expired_token_rejected():
    token, _jti, _exp = create_access_token("abc", role="worker", expires_delta_seconds=-1)
    try:
        decode_access_token(token)
        assert False, "Expected token decoding to fail for expired token"
    except AppError as exc:
        assert exc.error_code == "TOKEN_EXPIRED"
