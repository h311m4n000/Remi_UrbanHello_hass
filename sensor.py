from datetime import timedelta
from homeassistant.helpers.entity import Entity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

# Définir l'intervalle de mise à jour (1 minute)
SCAN_INTERVAL = timedelta(minutes=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up temperature sensors for Rémi devices."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    sensors = []
    for device in devices:
        sensors.append(RemiTemperatureSensor(api, device))

    async_add_entities(sensors, update_before_add=True)

class RemiTemperatureSensor(Entity):
    """Representation of a Rémi temperature sensor."""

    def __init__(self, api, device):
        self._api = api
        self._device = device
        self._name = f"Rémi {device.get('name', 'Unknown Device')} temperature"
        self._id = device["objectId"]
        self._temperature = None

    @property
    def device_info(self):
        """Return device information to link the entity to the integration."""
        return {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "UrbanHello",
            "model": "Rémi Clock",
            "via_device": (DOMAIN, self._id),
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._id}_temperature"

    @property
    def state(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "°C"

    async def async_update(self):
        """Fetch the latest temperature from the API."""
        try:
            info = await self._api.get_remi_info(self._id)
            self._temperature = info["temperature"] / 10.0
        except Exception as e:
            _LOGGER.error("Failed to update temperature for %s: %s", self._name, e)