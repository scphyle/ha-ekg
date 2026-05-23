from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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

# SensorStateClass / SensorDeviceClass added in HA 2021.12
try:
    from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
    _TEMP_CLASS = SensorDeviceClass.TEMPERATURE
    _MEASUREMENT = SensorStateClass.MEASUREMENT
    _TOTAL_INC = SensorStateClass.TOTAL_INCREASING
except ImportError:
    _TEMP_CLASS = None
    _MEASUREMENT = None
    _TOTAL_INC = None

# UnitOfTemperature added in HA 2022.5
try:
    from homeassistant.const import UnitOfTemperature
    _CELSIUS = UnitOfTemperature.CELSIUS
except (ImportError, AttributeError):
    _CELSIUS = "°C"

# Static sensors always present on every device
_STATIC_SENSORS = {
    "cpu_percent":     ("CPU Usage",    "%",   "mdi:cpu-64-bit",    _MEASUREMENT, None),
    "memory_percent":  ("Memory Usage", "%",   "mdi:memory",        _MEASUREMENT, None),
    "memory_used_gb":  ("Memory Used",  "GiB", "mdi:memory",        _MEASUREMENT, None),
    "memory_total_gb": ("Memory Total", "GiB", "mdi:memory",        None,         None),
    "uptime_hours":    ("Uptime",       "h",   "mdi:clock-outline", _TOTAL_INC,   None),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: EKGCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data
    metrics = data.get("metrics", {})

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=data.get("device", "unknown").title(),
        model=data.get("device_type", "unknown").title(),
        sw_version=data.get("version"),
        manufacturer="EKG",
    )

    entities: list[SensorEntity] = []

    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            if key in _STATIC_SENSORS:
                name, unit, icon, state_class, dev_class = _STATIC_SENSORS[key]
            elif "_rx_kbps" in key or "_tx_kbps" in key:
                direction = "RX" if "_rx_kbps" in key else "TX"
                iface = key.replace("net_", "").replace("_rx_kbps", "").replace("_tx_kbps", "")
                name, unit, icon, state_class, dev_class = (
                    f"{iface} {direction}", "kB/s", "mdi:ethernet", _MEASUREMENT, None
                )
            else:
                continue
            entities.append(EKGNumericSensor(
                coordinator, entry, key, name, unit, icon, state_class, dev_class, device_info
            ))

        elif isinstance(value, dict):
            if "temperature" in value:
                friendly = key.replace("temp_", "").replace("_", " ").title()
                entities.append(EKGTemperatureSensor(
                    coordinator, entry, key, f"Temp {friendly}", device_info
                ))
            elif "used_percent" in value:
                mount = value.get("mount", key.replace("disk_", "/"))
                entities.append(EKGDiskSensor(
                    coordinator, entry, key, f"Disk {mount}", device_info
                ))

    async_add_entities(entities)


class EKGNumericSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, unit, icon, state_class, dev_class, device_info):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_state_class = state_class
        self._attr_device_class = dev_class
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.data.get("metrics", {}).get(self._key)


class EKGDiskSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, device_info):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:harddisk"
        self._attr_state_class = _MEASUREMENT
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.data.get("metrics", {}).get(self._key, {}).get("used_percent")

    @property
    def extra_state_attributes(self):
        disk = self.coordinator.data.get("metrics", {}).get(self._key, {})
        return {
            "used_gb": disk.get("used_gb"),
            "total_gb": disk.get("total_gb"),
            "mount": disk.get("mount"),
        }


class EKGTemperatureSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, device_info):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = _CELSIUS
        self._attr_device_class = _TEMP_CLASS
        self._attr_state_class = _MEASUREMENT
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.data.get("metrics", {}).get(self._key, {}).get("temperature")

    @property
    def extra_state_attributes(self):
        temp = self.coordinator.data.get("metrics", {}).get(self._key, {})
        return {"high": temp.get("high"), "critical": temp.get("critical")}
