from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EKGCoordinator

# DeviceInfo moved in HA 2023.x
try:
    from homeassistant.helpers.device_registry import DeviceInfo
except ImportError:
    from homeassistant.helpers.entity import DeviceInfo  # type: ignore[no-redef]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: EKGCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=data.get("device", "unknown").title(),
        model=data.get("device_type", "unknown").title(),
        sw_version=data.get("version"),
        manufacturer="EKG",
    )

    async_add_entities([EKGCommandSelect(coordinator, entry, device_info)])


class EKGCommandSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: EKGCoordinator, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        super().__init__(coordinator)
        self._attr_name = "Command"
        self._attr_icon = "mdi:console"
        self._attr_unique_id = f"{entry.entry_id}_command"
        self._attr_device_info = device_info

    @property
    def options(self) -> list[str]:
        return self.coordinator.data.get("commands", ["idle"])

    @property
    def current_option(self) -> str:
        return self.coordinator.data.get("command", "idle")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_send_command(option)
        await self.coordinator.async_request_refresh()
