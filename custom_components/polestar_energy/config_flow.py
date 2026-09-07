"""Config flow for Polestar Energy."""

from __future__ import annotations

import secrets
import time
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PolestarEnergyApiError, PolestarEnergyAuthError, PolestarEnergyClient
from .auth import (
    build_authorize_url,
    create_pkce_pair,
    exchange_code,
    extract_code_from_redirect,
    extract_user_id,
    refresh_tokens,
)
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_EXPIRES_AT,
    CONF_HOME_LOCATION_IDS,
    CONF_HOME_LOCATION_NAMES,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    DOMAIN,
)


class PolestarEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Polestar Energy config flow (Auth0 PKCE paste-back)."""

    VERSION = 1

    def __init__(self) -> None:
        self._verifier: str | None = None
        self._challenge: str | None = None
        self._state: str | None = None
        self._authorize_url: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._authorize_url is None:
            self._verifier, self._challenge = create_pkce_pair()
            self._state = secrets.token_urlsafe(16)
            self._authorize_url = build_authorize_url(
                state=self._state, code_challenge=self._challenge
            )

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Optional("redirect_url"): str,
                        vol.Optional(CONF_REFRESH_TOKEN): str,
                        vol.Optional(CONF_NAME, default="Polestar Energy"): str,
                    }
                ),
                description_placeholders={"authorize_url": self._authorize_url},
            )

        errors: dict[str, str] = {}
        try:
            session = async_get_clientsession(self.hass)
            refresh = (user_input.get(CONF_REFRESH_TOKEN) or "").strip()
            redirect = (user_input.get("redirect_url") or "").strip()

            if refresh:
                tokens = await refresh_tokens(session, refresh_token=refresh)
            elif redirect:
                code, state = extract_code_from_redirect(redirect)
                if state and self._state and state != self._state:
                    raise ValueError("OAuth state mismatch")
                tokens = await exchange_code(
                    session, code=code, code_verifier=self._verifier or ""
                )
            else:
                raise ValueError("Provide redirect URL or refresh token")

            user_id = extract_user_id(tokens.access_token, tokens.id_token)
            client = PolestarEnergyClient(
                session,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token or refresh or None,
                expires_at=time.time() + tokens.expires_in,
                user_id=user_id,
            )
            data = await client.async_update()
            unique_id = data.user_id
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            home_ids = [loc.location_id for loc in data.locations if loc.is_home] or [
                loc.location_id for loc in data.locations[:1] if loc.location_id
            ]
            home_names = [
                loc.name for loc in data.locations if loc.is_home and loc.name
            ] or [loc.name for loc in data.locations[:1] if loc.name]

            return self.async_create_entry(
                title=user_input.get(CONF_NAME) or "Polestar Energy",
                data={
                    CONF_ACCESS_TOKEN: client.access_token,
                    CONF_REFRESH_TOKEN: client.refresh_token,
                    CONF_EXPIRES_AT: client.expires_at,
                    CONF_USER_ID: unique_id,
                    CONF_HOME_LOCATION_IDS: home_ids,
                    CONF_HOME_LOCATION_NAMES: home_names,
                },
            )
        except ValueError:
            errors["base"] = "invalid_redirect"
        except PolestarEnergyAuthError:
            errors["base"] = "auth_failed"
        except (PolestarEnergyApiError, Exception):  # noqa: BLE001
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("redirect_url"): str,
                    vol.Optional(CONF_REFRESH_TOKEN): str,
                    vol.Optional(CONF_NAME, default="Polestar Energy"): str,
                }
            ),
            errors=errors,
            description_placeholders={"authorize_url": self._authorize_url or ""},
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        return await self.async_step_user()
