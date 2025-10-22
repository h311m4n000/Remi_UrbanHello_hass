from datetime import timedelta
from homeassistant.components.number import NumberEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    numbers = []
    for device in devices:
        numbers.append(RemiLuminosityNumber(api, device))
        numbers.append(RemiVolumeNumber(api, device))

    async_add_entities(numbers, update_before_add=True)

class BaseRemiNumber(NumberEntity):
    def __init__(self, api, device):
        self._api = api
        self._device = device
        self._device_id = device["objectId"]
        self._device_name = device.get("name", "Unknown Device")
        self._value = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"Rémi {self._device_name}",
            "manufacturer": "UrbanHello",
            "model": "Rémi Clock",
            "via_device": (DOMAIN, self._device_id),
        }

    @property
    def min_value(self):
        return 0

    @property
    def max_value(self):
        return 100

    @property
    def step(self):
        return 1

    @property
    def native_value(self):
        return self._value

class RemiLuminosityNumber(BaseRemiNumber):
    @property
    def name(self):
        return f"Rémi {self._device_name} luminosity"

    @property
    def unique_id(self):
        return f"{self._device_id}_luminosity_number"

    async def async_set_native_value(self, value: float) -> None:
        await self._api.set_brightness(self._device_id, int(value))
        self._value = int(value)

    async def async_update(self):
        try:
            info = await self._api.get_remi_info(self._device_id)
            self._value = int(info.get("luminosity", 0))
        except Exception as e:
            _LOGGER.error("Failed to update luminosity for %s: %s", self._device_name, e)

class RemiVolumeNumber(BaseRemiNumber):
    @property
    def name(self):
        return f"Rémi {self._device_name} volume"

    @property
    def unique_id(self):
        return f"{self._device_id}_volume_number"

    async def async_set_native_value(self, value: float) -> None:
        await self._api.set_volume(self._device_id, int(value))
        self._value = int(value)

    async def async_update(self):
        try:
            info = await self._api.get_remi_info(self._device_id)
            self._value = int(info.get("volume", 0))
        except Exception as e:
            _LOGGER.error("Failed to update volume for %s: %s", self._device_name, e)


