"""DataUpdateCoordinator for Linksys Velop."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, JnapError, LinksysVelopClient

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


class LinksysVelopCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate periodic fetches from the Velop router."""

    def __init__(self, hass: HomeAssistant, client: LinksysVelopClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Linksys Velop",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.get_full_status()
        except (CannotConnect, JnapError) as exc:
            raise UpdateFailed(str(exc)) from exc
