"""Device tracker platform for Linksys Velop.

Each active DHCP lease appears as a device tracker entity, allowing
Home Assistant presence-detection automations based on network presence.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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

    tracked: set[str] = set()

    @callback
    def _add_new_devices() -> None:
        leases: list[dict] = coordinator.data.get("dhcp", {}).get("leases", []) if coordinator.data else []
        new_entities = []
        for lease in leases:
            mac = lease.get("macAddress", "").lower()
            if mac and mac not in tracked:
                tracked.add(mac)
                new_entities.append(VelopDeviceTracker(coordinator, entry, lease))
        if new_entities:
            async_add_entities(new_entities)

    coordinator.async_add_listener(_add_new_devices)
    if coordinator.data:
        _add_new_devices()


class VelopDeviceTracker(
    CoordinatorEntity[LinksysVelopCoordinator], ScannerEntity
):
    """Tracks a single device seen in the DHCP lease table."""

    _attr_source_type = SourceType.ROUTER

    def __init__(
        self,
        coordinator: LinksysVelopCoordinator,
        entry: ConfigEntry,
        lease: dict,
    ) -> None:
        super().__init__(coordinator)
        self._mac = lease.get("macAddress", "").lower()
        self._hostname = lease.get("hostName") or self._mac
        self._attr_unique_id = f"{entry.entry_id}_tracker_{self._mac}"
        self._attr_name = self._hostname
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Linksys",
            "model": "Velop MX4000",
        }

    @property
    def is_connected(self) -> bool:
        leases = (self.coordinator.data or {}).get("dhcp", {}).get("leases", [])
        return any(l.get("macAddress", "").lower() == self._mac for l in leases)

    @property
    def ip_address(self) -> str | None:
        leases = (self.coordinator.data or {}).get("dhcp", {}).get("leases", [])
        for l in leases:
            if l.get("macAddress", "").lower() == self._mac:
                return l.get("ipAddress")
        return None

    @property
    def mac_address(self) -> str:
        return self._mac

    @property
    def hostname(self) -> str | None:
        return self._hostname

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "mac_address": self._mac,
            "ip_address": self.ip_address,
            "hostname": self._hostname,
        }
