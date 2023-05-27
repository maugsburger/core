"""Support for Aurora ABB PowerOne Solar Photovoltaic (PV) inverter."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AuroraAbbDataUpdateCoordinator
from .const import (
    ATTR_DEVICE_NAME,
    ATTR_FIRMWARE,
    ATTR_MODEL,
    ATTR_SERIAL_NUMBER,
    DEFAULT_DEVICE_NAME,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = [
    SensorEntityDescription(
        key="instantaneouspower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        name="Power Output",
    ),
    SensorEntityDescription(
        key="temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        name="Temperature",
    ),
    SensorEntityDescription(
        key="totalenergy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Total Energy",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up aurora_abb_powerone sensor based on a config entry."""
    entities = []

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    data = config_entry.data

    for sens in SENSOR_TYPES:
        entities.append(AuroraSensor(coordinator, data, sens))

    _LOGGER.debug("async_setup_entry adding %d entities", len(entities))
    async_add_entities(entities, True)


class AuroraSensor(CoordinatorEntity[AuroraAbbDataUpdateCoordinator], SensorEntity):
    """Representation of a Sensor on a Aurora ABB PowerOne Solar inverter."""

    def __init__(
        self,
        coordinator: AuroraAbbDataUpdateCoordinator,
        data: Mapping[str, Any],
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._data = data
        self.entity_description = entity_description

    @property
    def native_value(self) -> StateType:
        """Get the value of the sensor from previously collected data."""
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def unique_id(self) -> str | None:
        """Return the unique id for this device."""
        if (serial := self._data.get(ATTR_SERIAL_NUMBER)) is None:
            return None
        return f"{serial}_{self.entity_description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes."""
        return {
            "identifiers": {(DOMAIN, self._data[ATTR_SERIAL_NUMBER])},
            "manufacturer": MANUFACTURER,
            "model": self._data[ATTR_MODEL],
            "name": self._data.get(ATTR_DEVICE_NAME, DEFAULT_DEVICE_NAME),
            "sw_version": self._data[ATTR_FIRMWARE],
        }
