"""Config flow for Polestar Energy."""

from __future__ import annotations

import logging
import time
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PolestarEnergyApiError, PolestarEnergyAuthError, PolestarEnergyClient
from .auth import (
    PolestarEnergyLoginError,
    extract_user_id,
    login_with_polestar_id,
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

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_NAME, default="Polestar Energy"): str,
    }
)


class PolestarEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Polestar Energy config flow (Polestar ID email + password)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                tokens = await login_with_polestar_id(
                    session,
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
                user_id = extract_user_id(tokens.access_token, tokens.id_token)
                client = PolestarEnergyClient(
                    session,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    expires_at=time.time() + tokens.expires_in,
                    user_id=user_id,
                )
                data = await client.async_update()
                unique_id = data.user_id
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                home_ids = [
                    loc.location_id for loc in data.locations if loc.is_home
                ] or [
                    loc.location_id
                    for loc in data.locations[:1]
                    if loc.location_id
                ]
                home_names = [
                    loc.name for loc in data.locations if loc.is_home and loc.name
                ] or [loc.name for loc in data.locations[:1] if loc.name]

                title = user_input.get(CONF_NAME) or "Polestar Energy"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_ACCESS_TOKEN: client.access_token,
                        CONF_REFRESH_TOKEN: client.refresh_token,
                        CONF_EXPIRES_AT: client.expires_at,
                        CONF_USER_ID: unique_id,
                        CONF_HOME_LOCATION_IDS: home_ids,
                        CONF_HOME_LOCATION_NAMES: home_names,
                        CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                    },
                )
            except PolestarEnergyLoginError as err:
                _LOGGER.warning("Polestar Energy login failed: %s", err)
                errors["base"] = "auth_failed"
            except PolestarEnergyAuthError:
                errors["base"] = "auth_failed"
            except (PolestarEnergyApiError, Exception):  # noqa: BLE001
                _LOGGER.exception("Polestar Energy setup failed after login")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        entry_id = self.context["entry_id"]
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return self.async_abort(reason="reauth_successful")
        username = entry.data.get(CONF_USERNAME, "")

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                tokens = await login_with_polestar_id(
                    session,
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
                new_data = {
                    **entry.data,
                    CONF_ACCESS_TOKEN: tokens.access_token,
                    CONF_REFRESH_TOKEN: tokens.refresh_token,
                    CONF_EXPIRES_AT: time.time() + tokens.expires_in,
                    CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                }
                self.hass.config_entries.async_update_entry(entry, data=new_data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            except PolestarEnergyLoginError:
                errors["base"] = "auth_failed"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Polestar Energy reauth failed")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=username): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
