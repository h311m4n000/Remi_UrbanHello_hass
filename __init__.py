from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api import RemiAPI
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Remi integration."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Rémi from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Créez une instance de l'API
    api = RemiAPI(entry.data["username"], entry.data["password"])
    await api.login()
    hass.data[DOMAIN]["api"] = api

    # Récupérer et stocker les détails de tous les appareils Rémi
    devices = []
    for remi_id in api.remis:
        try:
            device_info = await api.get_remi_info(remi_id)
            device_info["objectId"] = remi_id  # Ajouter l'ID à l'objet
            devices.append(device_info)
        except Exception as e:
            _LOGGER.error("Failed to fetch device info for Remi ID %s: %s", remi_id, e)

    hass.data[DOMAIN]["devices"] = devices

    # Forward setup to the light and sensor platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["light", "sensor"])
    return True