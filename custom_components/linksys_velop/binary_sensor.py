"""Binary sensor platform for Linksys Velop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

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
from .coordinator import LinksysVelopCoordinator


@dataclass(frozen=True)
class VelopBinarySensorDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[dict], bool] = lambda _: False


BINARY_SENSOR_DESCRIPTIONS: tuple[VelopBinarySensorDescription, ...] = (
    VelopBinarySensorDescription(
        key="wan_connected",
        name="WAN Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda d: d.get("wan", {}).get("wanStatus", {}).get("wanStatus") == "Connected",
    ),
    VelopBinarySensorDescription(
        key="firmware_update_available",
        name="Firmware Update Available",
        device_class=BinarySensorDeviceClass.UPDATE,
        is_on_fn=lambda d: bool(
            d.get("firmware", {}).get("updateAvailableVersion")
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
        VelopBinarySensor(coordinator, entry, desc)
        for desc in BINARY_SENSOR_DESCRIPTIONS
    )


class VelopBinarySensor(
    CoordinatorEntity[LinksysVelopCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LinksysVelopCoordinator,
        entry: ConfigEntry,
        description: VelopBinarySensorDescription,
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
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self.coordinator.data or {})
