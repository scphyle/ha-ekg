import asyncio

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN


class EKGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovery: dict = {}

    async def _fetch_device_info(self, host: str, port: int) -> dict:
        session = async_get_clientsession(self.hass)
        async with session.get(
            f"http://{host}:{port}/",
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            return await resp.json()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            try:
                info = await self._fetch_device_info(host, port)
                device = info.get("device", host)
                await self.async_set_unique_id(f"ekg_{device}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=device.title(),
                    data={CONF_HOST: host, CONF_PORT: port},
                )
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }),
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info):
        host = str(discovery_info.host)
        port = int(discovery_info.port)
        device_name = str(discovery_info.name).replace("._ekg._tcp.local.", "").replace("._ekg._tcp.", "")

        await self.async_set_unique_id(f"ekg_{device_name}")
        # Update host/port on an existing entry so IP changes self-heal.
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self._discovery = {"host": host, "port": port, "name": device_name}
        self.context["title_placeholders"] = {"name": device_name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery["name"].title(),
                data={CONF_HOST: self._discovery["host"], CONF_PORT: self._discovery["port"]},
            )
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._discovery["name"]},
        )

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            try:
                await self._fetch_device_info(host, port)
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_HOST: host, CONF_PORT: port},
                )
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST, "")): str,
                vol.Optional(CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)): int,
            }),
            errors=errors,
        )