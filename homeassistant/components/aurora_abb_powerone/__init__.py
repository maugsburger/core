"""The Aurora ABB Powerone PV inverter sensor integration."""

# Reference info:
# https://s1.solacity.com/docs/PVI-3.0-3.6-4.2-OUTD-US%20Manual.pdf
# http://www.drhack.it/images/PDF/AuroraCommunicationProtocol_4_2.pdf
#
# Developer note:
# vscode devcontainer: use the following to access USB device:
# "runArgs": ["-e", "GIT_EDITOR=code --wait", "--device=/dev/ttyUSB0"],
# and add the following to the end of script/bootstrap:
# sudo chmod 777 /dev/ttyUSB0

import logging

from aurorapy.client import AuroraError, AuroraSerialClient, AuroraTimeoutError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SCAN_INTERVAL

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aurora ABB PowerOne from a config entry."""

    comport = entry.data[CONF_PORT]
    address = entry.data[CONF_ADDRESS]
    coordinator = AuroraAbbDataUpdateCoordinator(hass, comport, address)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    # It should not be necessary to close the serial port because we close
    # it after every use in sensor.py, i.e. no need to do entry["client"].close()
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class AuroraAbbDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AuroraAbbPowerone data."""

    def __init__(self, hass: HomeAssistant, comport: str, address: int) -> None:
        """Initialize the data update coordinator."""
        self.available_prev: bool = False
        self.available: bool = False
        self.client = AuroraSerialClient(address, comport, parity="N", timeout=1)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    def _update_data(self) -> dict[str, float]:
        """Fetch new state data for the sensor.

        This is the only function that should fetch new data for Home Assistant.
        """
        data: dict[str, float] = {}
        try:
            self.available_prev = self.available
            self.client.connect()

            # read ADC channel 3 (grid power output)
            power_watts = self.client.measure(3, True)
            data["instantaneouspower"] = round(power_watts, 1)

            temperature_c = self.client.measure(21)
            data["temp"] = round(temperature_c, 1)

            energy_wh = self.client.cumulated_energy(5)
            data["totalenergy"] = round(energy_wh / 1000, 2)
            self.available = True

        except AuroraTimeoutError:
            data = {}
            self.available = False
            _LOGGER.debug("No response from inverter (could be dark)")
        except AuroraError as error:
            data = {}
            self.available = False
            raise error
        finally:
            if self.available != self.available_prev:
                if self.available:
                    _LOGGER.info("Communication with %s back online", self.name)
                else:
                    _LOGGER.warning(
                        "Communication with %s lost",
                        self.name,
                    )
            if self.client.serline.isOpen():
                self.client.close()

        return data

    async def _async_update_data(self) -> dict[str, float]:
        """Update inverter data in the executor."""
        return await self.hass.async_add_executor_job(self._update_data)
