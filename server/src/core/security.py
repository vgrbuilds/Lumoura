from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from src.core.config import JWT_ACCESS_TOKEN_EXPIRES_MINUTES, JWT_SECRET, PASSWORD_HASH_ITERATIONS


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return f"{salt}${_b64url_encode(dk)}"


def verify_password(password: str, stored_hash: str) -> bool:
    if "$" not in stored_hash:
        return False
    salt, hash_value = stored_hash.split("$", 1)
    expected = hash_password(password, salt)
    return hmac.compare_digest(expected, stored_hash)


def create_access_token(payload: dict[str, Any], expires_minutes: int | None = None) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")

    headers = {"alg": "HS256", "typ": "JWT"}
    now = datetime.now(timezone.utc)
    exp_minutes = expires_minutes or JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    body = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
    }

    header_segment = _b64url_encode(json.dumps(headers, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")

    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(_b64url_encode(expected_signature), signature_segment):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if datetime.now(timezone.utc).timestamp() > exp:
        raise ValueError("Token expired")

    return payload
