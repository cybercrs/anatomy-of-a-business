"""Compact, versioned encoding for refresh-safe activity progress."""

from __future__ import annotations

import base64
import json
from typing import Any


RESUME_STATE_VERSION = 1
MAX_RESUME_TOKEN_CHARS = 12_000
MAX_RESUME_PAYLOAD_BYTES = 9_000


def encode_resume_state(state: dict[str, Any]) -> str:
    """Encode a JSON-compatible progress snapshot for a URL query parameter."""

    envelope = {"version": RESUME_STATE_VERSION, "state": state}
    payload = json.dumps(
        envelope,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if len(payload) > MAX_RESUME_PAYLOAD_BYTES:
        raise ValueError("Resume state is too large to store safely in the URL.")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_resume_state(token: object) -> dict[str, Any] | None:
    """Decode a trusted shape from an untrusted URL value, or return ``None``."""

    if not isinstance(token, str) or not token or len(token) > MAX_RESUME_TOKEN_CHARS:
        return None

    try:
        padding = "=" * (-len(token) % 4)
        payload = base64.urlsafe_b64decode((token + padding).encode("ascii"))
        if len(payload) > MAX_RESUME_PAYLOAD_BYTES:
            return None
        envelope = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError):
        return None

    if not isinstance(envelope, dict):
        return None
    if envelope.get("version") != RESUME_STATE_VERSION:
        return None
    state = envelope.get("state")
    return state if isinstance(state, dict) else None
