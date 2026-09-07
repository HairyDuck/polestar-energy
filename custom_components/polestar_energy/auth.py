"""Auth0 PKCE helpers for Polestar Energy (Jedlix B2B)."""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from aiohttp import ClientError, ClientSession

from .const import (
    AUTH0_AUDIENCE,
    AUTH0_CLIENT_ID,
    AUTH0_CONNECTION,
    AUTH0_DOMAIN,
    AUTH0_SCOPE,
    AUTH_REDIRECT_URI,
    USER_ID_CLAIM_CANDIDATES,
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge)."""
    verifier = _b64url(secrets.token_bytes(64))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def build_authorize_url(*, state: str, code_challenge: str) -> str:
    """Build the Polestar ID / Auth0 authorize URL."""
    query = urlencode(
        {
            "client_id": AUTH0_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": AUTH_REDIRECT_URI,
            "scope": AUTH0_SCOPE,
            "audience": AUTH0_AUDIENCE,
            "connection": AUTH0_CONNECTION,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"https://{AUTH0_DOMAIN}/authorize?{query}"


def extract_code_from_redirect(redirect_url: str) -> tuple[str, str | None]:
    """Extract authorization code (and optional state) from a pasted redirect URL."""
    parsed = urlparse(redirect_url.strip())
    params = parse_qs(parsed.query)
    if parsed.fragment:
        params.update(parse_qs(parsed.fragment))
    if "error" in params:
        description = params.get("error_description", params["error"])[0]
        raise ValueError(f"OAuth error: {description}")
    if "code" not in params:
        raise ValueError("No authorization code found in the redirect URL")
    state = params.get("state", [None])[0]
    return params["code"][0], state


@dataclass(slots=True)
class TokenSet:
    """OAuth tokens."""

    access_token: str
    refresh_token: str | None
    expires_in: int
    id_token: str | None = None
    token_type: str = "Bearer"
    scope: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> TokenSet:
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=int(data.get("expires_in") or 3600),
            id_token=data.get("id_token"),
            token_type=data.get("token_type") or "Bearer",
            scope=data.get("scope"),
        )


async def exchange_code(
    session: ClientSession,
    *,
    code: str,
    code_verifier: str,
) -> TokenSet:
    """Exchange an authorization code for tokens."""
    data = {
        "grant_type": "authorization_code",
        "client_id": AUTH0_CLIENT_ID,
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": AUTH_REDIRECT_URI,
    }
    async with session.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    ) as resp:
        payload = await resp.json(content_type=None)
        if resp.status >= 400:
            raise ClientError(f"Token exchange failed ({resp.status}): {payload}")
        return TokenSet.from_response(payload)


async def refresh_tokens(
    session: ClientSession,
    *,
    refresh_token: str,
) -> TokenSet:
    """Refresh access token."""
    data = {
        "grant_type": "refresh_token",
        "client_id": AUTH0_CLIENT_ID,
        "refresh_token": refresh_token,
    }
    async with session.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    ) as resp:
        payload = await resp.json(content_type=None)
        if resp.status >= 400:
            raise ClientError(f"Token refresh failed ({resp.status}): {payload}")
        tokens = TokenSet.from_response(payload)
        if not tokens.refresh_token:
            tokens.refresh_token = refresh_token
        return tokens


def decode_jwt_claims(token: str) -> dict[str, Any]:
    """Decode JWT payload without verifying signature."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        import json

        return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except Exception:  # noqa: BLE001 - best-effort claim parse
        return {}


def extract_user_id(*tokens: str | None) -> str | None:
    """Extract Jedlix user id from access/id token claims."""
    for token in tokens:
        if not token:
            continue
        claims = decode_jwt_claims(token)
        for key in USER_ID_CLAIM_CANDIDATES:
            value = claims.get(key)
            if not value:
                continue
            text = str(value)
            # Only strip Auth0 social prefixes from `sub`-style values.
            if key == "sub" and "|" in text:
                text = text.rsplit("|", 1)[-1]
            return text
    return None
