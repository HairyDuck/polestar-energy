"""Sensor platform for Polestar Energy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PolestarEnergyCoordinator
from .models import PolestarEnergyData


def _session_attrs(data: PolestarEnergyData) -> dict[str, Any]:
    sessions = []
    for session in data.sessions[:20]:
        sessions.append(
            {
                "id": session.session_id,
                "start": session.start.isoformat() if session.start else None,
                "end": session.end.isoformat() if session.end else None,
                "energy_kwh": session.energy_kwh,
                "cost": session.cost,
                "savings": session.savings,
                "location": session.charging_location_name,
                "location_id": session.charging_location_id,
                "is_home": session.is_home,
                "is_in_progress": session.is_in_progress,
                "is_smart_charging": session.is_smart_charging,
            }
        )
    last = data.last_session
    return {
        "sessions": sessions,
        "session_id": last.session_id if last else None,
        "is_home": last.is_home if last else None,
        "last_session_at_home": last.is_home if last else None,
        "is_smart_charging": last.is_smart_charging if last else None,
        "battery_level_start": last.battery_level_start if last else None,
        "battery_level_end": last.battery_level_end if last else None,
        "cost_note": "App cost/savings are indicative only; prefer your charger meter for billing",
    }


@dataclass(frozen=True, kw_only=True)
class PolestarEnergySensorDescription(SensorEntityDescription):
    """Sensor description with value extractor."""

    value_fn: Callable[[PolestarEnergyData], float | str | datetime | None]
    attrs_fn: Callable[[PolestarEnergyData], dict[str, Any]] | None = None


SENSORS: tuple[PolestarEnergySensorDescription, ...] = (
    PolestarEnergySensorDescription(
        key="last_session_energy",
        name="Last session energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.last_session.energy_kwh if d.last_session else None,
        attrs_fn=_session_attrs,
    ),
    PolestarEnergySensorDescription(
        key="last_session_cost",
        name="Last session cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="GBP",
        value_fn=lambda d: d.last_session.cost if d.last_session else None,
    ),
    PolestarEnergySensorDescription(
        key="last_session_savings",
        name="Last session savings",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="GBP",
        value_fn=lambda d: d.last_session.savings if d.last_session else None,
    ),
    PolestarEnergySensorDescription(
        key="last_session_start",
        name="Last session start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.last_session.start if d.last_session else None,
    ),
    PolestarEnergySensorDescription(
        key="last_session_end",
        name="Last session end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.last_session.end if d.last_session else None,
    ),
    PolestarEnergySensorDescription(
        key="energy_today",
        name="Energy today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: d.energy_today_kwh,
    ),
    PolestarEnergySensorDescription(
        key="energy_month",
        name="Energy this month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: d.energy_month_kwh,
    ),
    PolestarEnergySensorDescription(
        key="last_session_location",
        name="Last session location",
        value_fn=lambda d: (
            d.last_session.charging_location_name if d.last_session else None
        ),
        attrs_fn=_session_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolestarEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PolestarEnergySensor(coordinator, description) for description in SENSORS
    )


class PolestarEnergySensor(CoordinatorEntity[PolestarEnergyCoordinator], SensorEntity):
    """Polestar Energy sensor."""

    entity_description: PolestarEnergySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PolestarEnergyCoordinator,
        description: PolestarEnergySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": coordinator.entry.title,
            "manufacturer": "LukeDev",
            "model": "Polestar Energy",
        }

    @property
    def native_value(self) -> float | str | datetime | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.entity_description.attrs_fn:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
