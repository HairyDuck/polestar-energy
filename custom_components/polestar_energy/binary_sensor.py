"""Binary sensors for Polestar Energy."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PolestarEnergyCoordinator
from .models import PolestarEnergyData

BINARY_SENSORS: tuple[tuple[BinarySensorEntityDescription, Callable[[PolestarEnergyData], bool]], ...] = (
    (
        BinarySensorEntityDescription(
            key="session_active",
            name="Session active",
            device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        ),
        lambda data: data.session_active,
    ),
    (
        BinarySensorEntityDescription(
            key="charging_at_home",
            name="Charging at home",
            device_class=BinarySensorDeviceClass.PLUG,
        ),
        lambda data: data.charging_at_home,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolestarEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PolestarEnergyBinarySensor(coordinator, description, value_fn)
        for description, value_fn in BINARY_SENSORS
    )


class PolestarEnergyBinarySensor(
    CoordinatorEntity[PolestarEnergyCoordinator], BinarySensorEntity
):
    """Polestar Energy binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PolestarEnergyCoordinator,
        description: BinarySensorEntityDescription,
        value_fn,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._value_fn = value_fn
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": coordinator.entry.title,
            "manufacturer": "HairyDuck",
            "model": "Polestar Energy",
        }

    @property
    def is_on(self) -> bool:
        data: PolestarEnergyData = self.coordinator.data
        return bool(self._value_fn(data))
