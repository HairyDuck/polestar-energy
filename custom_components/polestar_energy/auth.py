"""Auth0 PKCE helpers for Polestar Energy (Jedlix B2B)."""

from __future__ import annotations

import base64
import hashlib
import logging
import re
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

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

_LOGGER = logging.getLogger(__name__)

POLESTAR_ID_BASE = "https://polestarid.eu.polestar.com/"
_BROWSER_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Mobile Safari/537.36"
)


class PolestarEnergyLoginError(Exception):
    """Raised when Polestar ID / Auth0 login fails."""


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


def _abs(base: str, href: str) -> str:
    return urljoin(base, href)


def _resume_path(html: str) -> str | None:
    match = re.search(r'(?:url|action):\s*"([^"]+)"', html)
    return match.group(1) if match else None


def _consent_fields(html: str, base: str) -> tuple[str, list[tuple[str, str]]] | None:
    """Parse Auth0 consent form fields (supports duplicate scope names)."""
    if "name=\"action\"" not in html and "name='action'" not in html:
        if "Accept" not in html:
            return None
    action_match = re.search(r'<form[^>]+action=["\']([^"\']*)["\']', html, flags=re.I)
    action = (
        _abs(base, action_match.group(1))
        if action_match and action_match.group(1)
        else base
    )
    fields: list[tuple[str, str]] = []
    for match in re.finditer(r"<input[^>]+>", html, flags=re.I):
        tag = match.group(0)
        name_m = re.search(r'name=["\']([^"\']+)["\']', tag, flags=re.I)
        if not name_m:
            continue
        value_m = re.search(r'value=["\']([^"\']*)["\']', tag, flags=re.I)
        fields.append((name_m.group(1), value_m.group(1) if value_m else ""))
    fields = [(n, v) for n, v in fields if n != "action"]
    fields.append(("action", "accept"))
    return action, fields


async def _follow_get(
    session: ClientSession, url: str, *, max_hops: int = 20
) -> tuple[str, str]:
    current = url
    for _ in range(max_hops):
        if current.startswith("com.polestar.smartcharging://"):
            return current, ""
        async with session.get(
            current,
            allow_redirects=False,
            headers={"User-Agent": _BROWSER_UA},
            timeout=30,
        ) as resp:
            loc = resp.headers.get("Location")
            if loc:
                current = _abs(str(resp.url), loc)
                continue
            return str(resp.url), await resp.text()
    raise PolestarEnergyLoginError("Too many redirects during sign-in")


async def _post_follow(
    session: ClientSession,
    url: str,
    data: Any,
    *,
    params: dict[str, str] | None = None,
) -> tuple[str, str]:
    async with session.post(
        url,
        data=data,
        params=params,
        allow_redirects=False,
        headers={"User-Agent": _BROWSER_UA},
        timeout=30,
    ) as resp:
        loc = resp.headers.get("Location")
        if loc:
            next_url = _abs(str(resp.url), loc)
            if next_url.startswith("com.polestar.smartcharging://"):
                return next_url, ""
            return await _follow_get(session, next_url)
        return str(resp.url), await resp.text()


async def login_with_polestar_id(
    session: ClientSession,
    *,
    username: str,
    password: str,
) -> TokenSet:
    """Sign in with Polestar ID email/password and return Auth0 tokens.

    Mirrors the Polestar Energy app OAuth (Auth0 + Polestar ID federation).
    Does not require copying redirect URLs or using a phone.
    """
    verifier, challenge = create_pkce_pair()
    state = secrets.token_urlsafe(16)
    authorize = build_authorize_url(state=state, code_challenge=challenge)

    url, html = await _follow_get(session, authorize)
    resume = _resume_path(html)
    if not resume:
        raise PolestarEnergyLoginError("Polestar ID login form was not found")

    parsed = urlparse(url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    resume_url = urljoin(POLESTAR_ID_BASE, resume)

    url, html = await _post_follow(
        session,
        resume_url,
        {"pf.username": username.strip(), "pf.pass": password},
        params=params,
    )

    if "ERR001" in html or ("authMessage" in html and "ERR" in html):
        raise PolestarEnergyLoginError("Invalid Polestar ID email or password")

    if "code=" not in url and not url.startswith("com.polestar.smartcharging://"):
        uid_match = re.search(r"[?&]uid=([^&]+)", url)
        if uid_match or "pf.submit" in html:
            uid = uid_match.group(1) if uid_match else ""
            url, html = await _post_follow(
                session,
                resume_url,
                {"pf.submit": "true", "subject": uid},
                params=params,
            )

    for _ in range(8):
        if url.startswith("com.polestar.smartcharging://") or (
            "code=" in url and "com.polestar.smartcharging" in url
        ):
            break
        form = _consent_fields(html, url)
        if not form:
            meta = re.search(
                r'http-equiv=["\']refresh["\'][^>]+url=([^"\' >]+)',
                html,
                flags=re.I,
            )
            if meta:
                url, html = await _follow_get(session, _abs(url, meta.group(1)))
                continue
            _LOGGER.debug("OAuth stuck at %s", url[:200])
            raise PolestarEnergyLoginError("Could not complete Polestar Energy consent")
        action, fields = form
        url, html = await _post_follow(session, action, fields)
    else:
        raise PolestarEnergyLoginError("Timed out waiting for authorisation code")

    code, returned_state = extract_code_from_redirect(url)
    if returned_state and returned_state != state:
        raise PolestarEnergyLoginError("OAuth state mismatch")
    return await exchange_code(session, code=code, code_verifier=verifier)


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
