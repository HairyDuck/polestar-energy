"""Data update coordinator for Polestar Energy."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PolestarEnergyApiError, PolestarEnergyAuthError, PolestarEnergyClient
from .auth import TokenSet
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    DEFAULT_SCAN_INTERVAL_SECONDS,
)
from .models import PolestarEnergyData

_LOGGER = logging.getLogger(__name__)


class PolestarEnergyCoordinator(DataUpdateCoordinator[PolestarEnergyData]):
    """Poll Polestar Energy session data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: PolestarEnergyClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Polestar Energy",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.client = client

        async def _persist_tokens(tokens: TokenSet) -> None:
            data = {**entry.data}
            data[CONF_ACCESS_TOKEN] = client.access_token
            data[CONF_REFRESH_TOKEN] = client.refresh_token
            data[CONF_EXPIRES_AT] = client.expires_at
            hass.config_entries.async_update_entry(entry, data=data)

        client._token_listener = _persist_tokens  # noqa: SLF001 - wire persistence

    async def _async_update_data(self) -> PolestarEnergyData:
        try:
            return await self.client.async_update()
        except PolestarEnergyAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PolestarEnergyApiError as err:
            raise UpdateFailed(str(err)) from err
