"""Sensor platform for Linksys Velop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LinksysVelopCoordinator


@dataclass(frozen=True)
class VelopSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = lambda _: None
    attr_fn: Callable[[dict], dict] = lambda _: {}


SENSOR_DESCRIPTIONS: tuple[VelopSensorDescription, ...] = (
    VelopSensorDescription(
        key="wan_ip",
        name="WAN IP Address",
        icon="mdi:ip-network",
        value_fn=lambda d: d.get("wan", {}).get("wanStatus", {}).get("ipAddress"),
    ),
    VelopSensorDescription(
        key="wan_status",
        name="WAN Connection Status",
        icon="mdi:wan",
        value_fn=lambda d: d.get("wan", {}).get("wanStatus", {}).get("wanStatus"),
    ),
    VelopSensorDescription(
        key="connected_devices",
        name="Connected Devices",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="devices",
        value_fn=lambda d: len(d.get("dhcp", {}).get("leases", [])),
        attr_fn=lambda d: {
            "devices": [
                {
                    "hostname": l.get("hostName", ""),
                    "ip": l.get("ipAddress", ""),
                    "mac": l.get("macAddress", ""),
                }
                for l in d.get("dhcp", {}).get("leases", [])
            ]
        },
    ),
    VelopSensorDescription(
        key="lan_ip",
        name="LAN IP Address",
        icon="mdi:lan",
        value_fn=lambda d: d.get("lan", {}).get("ipAddress"),
    ),
    VelopSensorDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:package-up",
        value_fn=lambda d: (
            d.get("firmware", {}).get("latestFirmwareVersion")
            or d.get("firmware", {}).get("firmwareVersion")
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LinksysVelopCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VelopSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
    )


class VelopSensor(CoordinatorEntity[LinksysVelopCoordinator], SensorEntity):
    """A sensor representing one data point from the Velop mesh."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LinksysVelopCoordinator,
        entry: ConfigEntry,
        description: VelopSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Linksys",
            "model": "Velop MX4000",
        }

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict:
        return self.entity_description.attr_fn(self.coordinator.data or {})
