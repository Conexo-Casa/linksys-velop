"""Linksys Velop JNAP API client."""
from __future__ import annotations

import base64
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

JNAP_URL_PATH = "/JNAP/"
JNAP_BASE = "http://linksys.com/jnap/"

JNAP_ACTION_DEVICE_INFO        = f"{JNAP_BASE}core/GetDeviceInfo"
JNAP_ACTION_TRANSACTION         = f"{JNAP_BASE}core/Transaction"
JNAP_ACTION_GET_WAN_STATUS      = f"{JNAP_BASE}router/GetWANStatus"
JNAP_ACTION_GET_LAN_SETTINGS    = f"{JNAP_BASE}router/GetLANSettings"
JNAP_ACTION_GET_DHCP_LEASES     = f"{JNAP_BASE}router/GetDHCPClientLeases"
JNAP_ACTION_GET_BACKHAUL        = f"{JNAP_BASE}nodes/diagnostics/GetBackhaulInfo"
JNAP_ACTION_GET_TOPOLOGY        = f"{JNAP_BASE}nodes/networkconfig/GetNetworkConfiguration"
JNAP_ACTION_REBOOT_NODE         = f"{JNAP_BASE}core/Reboot"
JNAP_ACTION_GET_FIRMWARE        = f"{JNAP_BASE}firmwareupdate/GetFirmwareUpdateStatus"
JNAP_ACTION_CHECK_UPDATES       = f"{JNAP_BASE}firmwareupdate/UpdateFirmwareNow"


class JnapError(Exception):
    """Raised when the router returns a non-OK result code."""


class CannotConnect(Exception):
    """Raised when we cannot reach the router."""


class InvalidAuth(Exception):
    """Raised when credentials are rejected."""


class LinksysVelopClient:
    """Async JNAP client for Linksys Velop mesh routers."""

    def __init__(
        self,
        host: str,
        password: str,
        session: aiohttp.ClientSession,
        port: int = 80,
    ) -> None:
        self._url = f"http://{host}:{port}{JNAP_URL_PATH}"
        self._auth = "Basic " + base64.b64encode(f"admin:{password}".encode()).decode()
        self._session = session

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    async def _request(self, action: str, payload: dict | None = None) -> dict:
        """Send a single JNAP request and return the response body."""
        headers = {
            "X-JNAP-Action": action,
            "X-JNAP-Authorization": self._auth,
            "Content-Type": "application/json",
        }
        try:
            async with self._session.post(
                self._url,
                json=payload or {},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuth
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except aiohttp.ClientConnectorError as exc:
            raise CannotConnect(str(exc)) from exc
        except aiohttp.ServerTimeoutError as exc:
            raise CannotConnect(str(exc)) from exc

        result = data.get("result", "")
        if result not in ("OK", "_success"):
            raise JnapError(f"JNAP error: {result}")
        return data.get("output", {})

    async def _transaction(self, actions: list[dict]) -> list[dict]:
        """Run a JNAP Transaction (batch multiple actions in one HTTP call)."""
        payload = {"actions": actions}
        headers = {
            "X-JNAP-Action": JNAP_ACTION_TRANSACTION,
            "X-JNAP-Authorization": self._auth,
            "Content-Type": "application/json",
        }
        try:
            async with self._session.post(
                self._url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuth
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except aiohttp.ClientConnectorError as exc:
            raise CannotConnect(str(exc)) from exc

        outer = data.get("result", "")
        if outer not in ("OK", "_success"):
            raise JnapError(f"Transaction error: {outer}")
        return data.get("responses", [])

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_device_info(self) -> dict:
        """Return router model, firmware version, and supported actions."""
        return await self._request(JNAP_ACTION_DEVICE_INFO)

    async def get_wan_status(self) -> dict:
        """Return WAN connectivity status and IP info."""
        return await self._request(JNAP_ACTION_GET_WAN_STATUS)

    async def get_lan_settings(self) -> dict:
        """Return LAN IP and DHCP range."""
        return await self._request(JNAP_ACTION_GET_LAN_SETTINGS)

    async def get_dhcp_leases(self) -> list[dict]:
        """Return list of current DHCP leases (connected devices)."""
        out = await self._request(JNAP_ACTION_GET_DHCP_LEASES)
        return out.get("leases", [])

    async def get_backhaul_info(self) -> list[dict]:
        """Return backhaul (node-to-node) link information."""
        try:
            out = await self._request(JNAP_ACTION_GET_BACKHAUL)
            return out.get("backhaulInfo", [])
        except JnapError:
            _LOGGER.debug("BackhaulInfo not available on this firmware")
            return []

    async def get_network_topology(self) -> dict:
        """Return node topology / mesh network configuration."""
        try:
            return await self._request(JNAP_ACTION_GET_TOPOLOGY)
        except JnapError:
            _LOGGER.debug("GetNetworkConfiguration not available")
            return {}

    async def get_firmware_status(self) -> dict:
        """Return firmware update status."""
        try:
            return await self._request(JNAP_ACTION_GET_FIRMWARE)
        except JnapError:
            return {}

    async def reboot(self) -> None:
        """Reboot the primary node."""
        await self._request(JNAP_ACTION_REBOOT_NODE)

    async def test_connection(self) -> dict:
        """Verify connectivity and credentials, return device info."""
        return await self.get_device_info()

    async def get_full_status(self) -> dict:
        """Batch-fetch all data used by the coordinator in one round-trip."""
        actions = [
            {"action": JNAP_ACTION_GET_WAN_STATUS, "request": {}},
            {"action": JNAP_ACTION_GET_LAN_SETTINGS, "request": {}},
            {"action": JNAP_ACTION_GET_DHCP_LEASES, "request": {}},
            {"action": JNAP_ACTION_GET_FIRMWARE, "request": {}},
        ]
        responses = await self._transaction(actions)
        result: dict[str, Any] = {}
        keys = ["wan", "lan", "dhcp", "firmware"]
        for key, resp in zip(keys, responses):
            if resp.get("result") in ("OK", "_success"):
                result[key] = resp.get("output", {})
            else:
                result[key] = {}
        # Backhaul is a separate non-transactable endpoint on some firmware
        result["backhaul"] = await self.get_backhaul_info()
        return result
