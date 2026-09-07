"""Async API client for Polestar Energy (Jedlix mobile gateway)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .auth import TokenSet, extract_user_id, refresh_tokens
from .const import (
    API_KEY,
    CLIENT_NAME,
    CLIENT_VERSION,
    MOBILE_GATEWAY_BASE,
)
from .models import ChargeSession, ChargingLocation, PolestarEnergyData

_LOGGER = logging.getLogger(__name__)


class PolestarEnergyAuthError(Exception):
    """Authentication / reauth required."""


class PolestarEnergyApiError(Exception):
    """API failure."""


class PolestarEnergyClient:
    """Talk to Jedlix mobile gateway used by Polestar Energy."""

    def __init__(
        self,
        session: ClientSession,
        *,
        access_token: str,
        refresh_token: str | None,
        expires_at: float | None = None,
        user_id: str | None = None,
        home_location_ids: list[str] | None = None,
        home_location_names: list[str] | None = None,
        token_listener: Any | None = None,
    ) -> None:
        self._session = session
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_at = expires_at or 0.0
        self._user_id = user_id
        self._home_location_ids = set(home_location_ids or [])
        self._home_location_names = set(home_location_names or [])
        self._token_listener = token_listener

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    @property
    def expires_at(self) -> float:
        return self._expires_at

    def apply_tokens(self, tokens: TokenSet) -> None:
        """Store refreshed tokens."""
        now = datetime.now(timezone.utc).timestamp()
        self._access_token = tokens.access_token
        if tokens.refresh_token:
            self._refresh_token = tokens.refresh_token
        self._expires_at = now + max(tokens.expires_in - 60, 30)
        if not self._user_id:
            self._user_id = extract_user_id(tokens.access_token, tokens.id_token)

    async def _ensure_token(self) -> None:
        now = datetime.now(timezone.utc).timestamp()
        if self._access_token and now < self._expires_at:
            return
        if not self._refresh_token:
            raise PolestarEnergyAuthError("Access token expired and no refresh token")
        try:
            tokens = await refresh_tokens(
                self._session, refresh_token=self._refresh_token
            )
        except ClientError as err:
            raise PolestarEnergyAuthError(str(err)) from err
        self.apply_tokens(tokens)
        if self._token_listener:
            await self._token_listener(tokens)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "ApiKey": API_KEY,
            "Accept": "application/json",
            "Jedlix-ClientName": CLIENT_NAME,
            "Jedlix-ClientVersion": CLIENT_VERSION,
            "User-Agent": f"{CLIENT_NAME}/{CLIENT_VERSION}",
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        await self._ensure_token()
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json_body,
                timeout=45,
            ) as resp:
                text = await resp.text()
                if resp.status in (401, 403):
                    raise PolestarEnergyAuthError(
                        f"Unauthorized ({resp.status}) for {url}: {text[:300]}"
                    )
                if resp.status >= 400:
                    raise PolestarEnergyApiError(
                        f"HTTP {resp.status} for {url}: {text[:300]}"
                    )
                if not text:
                    return None
                try:
                    return await resp.json(content_type=None)
                except Exception:  # noqa: BLE001
                    return text
        except ClientResponseError as err:
            raise PolestarEnergyApiError(str(err)) from err

    async def resolve_user_id(self) -> str:
        """Resolve Jedlix user id from token claims or vehicles."""
        if self._user_id:
            return self._user_id

        await self._ensure_token()
        user_id = extract_user_id(self._access_token)
        if user_id:
            self._user_id = user_id
            return user_id

        vehicles = await self.get_vehicles()
        for vehicle in vehicles:
            raw = vehicle if isinstance(vehicle, dict) else {}
            if raw.get("userId"):
                self._user_id = str(raw["userId"])
                return self._user_id

        raise PolestarEnergyApiError("Unable to resolve Jedlix user id from token/API")

    async def get_vehicles(self) -> list[dict[str, Any]]:
        """Fetch vehicles."""
        payload = await self._request("GET", f"{MOBILE_GATEWAY_BASE}/vehicles")
        return payload if isinstance(payload, list) else []

    async def get_locations(self) -> list[ChargingLocation]:
        """Fetch charging addresses (home locations)."""
        payload = await self._request("GET", f"{MOBILE_GATEWAY_BASE}/addresses")
        items = payload if isinstance(payload, list) else []
        locations = [
            ChargingLocation.from_api(item) for item in items if isinstance(item, dict)
        ]
        if not self._home_location_ids:
            # Polestar Energy addresses are the user's configured home chargers.
            for loc in locations:
                if loc.location_id:
                    self._home_location_ids.add(loc.location_id)
                if loc.name:
                    self._home_location_names.add(loc.name)
        return locations

    async def get_sessions(self, *, days: int = 45) -> list[ChargeSession]:
        """Fetch recent charge sessions."""
        payload = await self._request("GET", f"{MOBILE_GATEWAY_BASE}/sessions")
        items = payload if isinstance(payload, list) else []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        sessions = [
            ChargeSession.from_api(
                item,
                home_location_ids=self._home_location_ids,
                home_location_names=self._home_location_names,
            )
            for item in items
            if isinstance(item, dict)
        ]
        sessions = [
            s
            for s in sessions
            if s.start is None or (s.start if s.start.tzinfo else s.start.replace(tzinfo=timezone.utc)) >= cutoff
        ]
        sessions.sort(
            key=lambda s: s.start or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return sessions

    async def async_update(self) -> PolestarEnergyData:
        """Fetch locations + sessions and compute aggregates."""
        locations = await self.get_locations()
        sessions = await self.get_sessions()
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        energy_today = 0.0
        energy_month = 0.0
        for session in sessions:
            if session.energy_kwh is None:
                continue
            # Prefer end time so overnight sessions count on the morning they finish.
            when = session.end or session.start
            if when and when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when and when >= today_start:
                energy_today += session.energy_kwh
            if when and when >= month_start:
                energy_month += session.energy_kwh

        last = sessions[0] if sessions else None
        active = next((s for s in sessions if s.is_in_progress), None)
        return PolestarEnergyData(
            user_id=await self.resolve_user_id(),
            sessions=sessions,
            locations=locations,
            last_session=last,
            energy_today_kwh=round(energy_today, 3),
            energy_month_kwh=round(energy_month, 3),
            session_active=active is not None,
            # Live "charging at home" only while a session is open at a home address.
            charging_at_home=bool(active and active.is_home),
        )
