"""Data models for Polestar Energy charge sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_energy_kwh(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace(",", ".")
    for suffix in ("kwh", "kw h", "kw·h"):
        text = text.replace(suffix, "")
    text = text.strip()
    try:
        return float(text.split()[0]) if text else None
    except (ValueError, IndexError):
        return None


def _parse_money(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
    try:
        return float(cleaned) if cleaned not in {"", "-", "."} else None
    except ValueError:
        return None


def _format_address(address: dict[str, Any] | None) -> str | None:
    if not address:
        return None
    house = address.get("houseNumber") or address.get("houseIdentifier")
    street = address.get("street") or address.get("addressline1")
    city = address.get("city")
    parts = [str(p).strip() for p in (house, street, city) if p not in (None, "")]
    return ", ".join(parts) if parts else None


@dataclass(slots=True)
class ChargeSession:
    """Normalised charge session."""

    session_id: str
    start: datetime | None = None
    end: datetime | None = None
    energy_kwh: float | None = None
    cost: float | None = None
    savings: float | None = None
    charging_location_id: str | None = None
    charging_location_name: str | None = None
    is_in_progress: bool = False
    is_smart_charging: bool = False
    battery_level_start: int | None = None
    battery_level_end: int | None = None
    is_home: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(
        cls,
        payload: dict[str, Any],
        *,
        home_location_ids: set[str] | None = None,
        home_location_names: set[str] | None = None,
    ) -> ChargeSession:
        """Build from Jedlix mobile gateway session JSON."""
        home_ids = home_location_ids or set()
        home_names = {n.casefold() for n in (home_location_names or set())}

        session_id = str(
            payload.get("sessionId")
            or payload.get("id")
            or payload.get("session_id")
            or ""
        )

        address_obj = payload.get("address")
        if not isinstance(address_obj, dict):
            address_obj = None

        location_id = payload.get("addressId") or payload.get("chargingLocationId")
        location_name = _format_address(address_obj) or payload.get(
            "chargingLocationName"
        )

        savings_amount = None
        cost_amount = None
        savings_raw = payload.get("savings")
        if isinstance(savings_raw, list) and savings_raw:
            first = savings_raw[0]
            if isinstance(first, dict):
                savings_amount = first.get("amount")
                cost_amount = first.get("costs")
        elif isinstance(savings_raw, (int, float)):
            savings_amount = savings_raw

        energy = payload.get("energyAdded")
        if energy is None:
            energy = payload.get("formattedChargedEnergy") or payload.get("chargedEnergy")

        status = str(payload.get("status") or "").strip().lower()
        in_progress = status in {
            "inprogress",
            "in_progress",
            "active",
            "charging",
            "started",
            "ongoing",
        } or bool(payload.get("isInProgress"))

        location_id_str = str(location_id) if location_id else None
        location_name_str = str(location_name) if location_name else None
        is_home = False
        if location_id_str and location_id_str in home_ids:
            is_home = True
        elif location_name_str and location_name_str.casefold() in home_names:
            is_home = True
        elif home_ids and location_id_str is None and len(home_ids) == 1:
            # Single home address accounts: treat unnamed matches carefully.
            is_home = False

        return cls(
            session_id=session_id,
            start=_parse_dt(payload.get("startTime") or payload.get("start")),
            end=_parse_dt(payload.get("endTime") or payload.get("end")),
            energy_kwh=_parse_energy_kwh(energy),
            cost=_parse_money(cost_amount if cost_amount is not None else payload.get("formattedCosts")),
            savings=_parse_money(
                savings_amount if savings_amount is not None else payload.get("formattedSavings")
            ),
            charging_location_id=location_id_str,
            charging_location_name=location_name_str,
            is_in_progress=in_progress,
            is_smart_charging=bool(payload.get("isManaged") or payload.get("isSmartCharging")),
            battery_level_start=_as_int(
                payload.get("stateOfChargeStart") or payload.get("batteryLevelStart")
            ),
            battery_level_end=_as_int(
                payload.get("stateOfChargeEnd") or payload.get("batteryLevelEnd")
            ),
            is_home=is_home,
            raw=payload,
        )


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class ChargingLocation:
    """Charging location (home address)."""

    location_id: str
    name: str | None = None
    is_home: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> ChargingLocation:
        location_id = str(payload.get("id") or payload.get("addressId") or "")
        name = _format_address(payload)
        return cls(
            location_id=location_id,
            name=name,
            # Configured Polestar Energy addresses are home charging locations.
            is_home=True,
            raw=payload,
        )


@dataclass(slots=True)
class PolestarEnergyData:
    """Coordinator payload."""

    user_id: str
    sessions: list[ChargeSession] = field(default_factory=list)
    locations: list[ChargingLocation] = field(default_factory=list)
    last_session: ChargeSession | None = None
    energy_today_kwh: float = 0.0
    energy_month_kwh: float = 0.0
    session_active: bool = False
    charging_at_home: bool = False
