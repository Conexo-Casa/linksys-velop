"""Button platform for Linksys Velop — provides a Reboot action."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LinksysVelopCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LinksysVelopCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VelopRebootButton(coordinator, entry)])


class VelopRebootButton(
    CoordinatorEntity[LinksysVelopCoordinator], ButtonEntity
):
    """Button that reboots the primary Velop node."""

    _attr_has_entity_name = True
    _attr_name = "Reboot Router"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:restart"

    def __init__(
        self,
        coordinator: LinksysVelopCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_reboot"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Linksys",
            "model": "Velop MX4000",
        }

    async def async_press(self) -> None:
        """Reboot the router."""
        _LOGGER.info("Rebooting Linksys Velop router")
        await self.coordinator.client.reboot()
