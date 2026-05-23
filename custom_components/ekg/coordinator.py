import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EKGCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self._url = f"http://{host}:{port}"
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        try:
            async with self._session.get(
                f"{self._url}/",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except asyncio.TimeoutError as e:
            raise UpdateFailed("Connection timed out") from e
        except aiohttp.ClientError as e:
            raise UpdateFailed(str(e)) from e

    async def async_send_command(self, command: str) -> bool:
        try:
            async with self._session.post(
                f"{self._url}/command",
                json={"command": command},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                return resp.status in (200, 202)
        except Exception as e:
            _LOGGER.error("Failed to send command %s: %s", command, e)
            return False
