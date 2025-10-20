from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import service
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

    # Load bedtime settings for all devices
    try:
        bedtime_settings = await api.get_all_bedtime_settings()
        hass.data[DOMAIN]["bedtime_settings"] = bedtime_settings
        _LOGGER.info("Loaded bedtime settings for %d devices", len(bedtime_settings))
    except Exception as e:
        _LOGGER.warning("Failed to load bedtime settings: %s", e)
        hass.data[DOMAIN]["bedtime_settings"] = {}

    # Forward setup to the light, sensor, switch, and number platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["light", "sensor", "switch", "number"])
    
    # Register refresh service
    async def async_refresh_remi_data(call):
        """Refresh all Remi data from the API."""
        _LOGGER.info("Refreshing Remi data...")
        try:
            # Reload bedtime settings
            bedtime_settings = await api.get_all_bedtime_settings()
            hass.data[DOMAIN]["bedtime_settings"] = bedtime_settings
            _LOGGER.info("Refreshed bedtime settings for %d devices", len(bedtime_settings))
            
            # Use Home Assistant's built-in service to refresh all Remi entities
            # Get all Remi entities from the entity registry
            entity_registry = await hass.helpers.entity_registry.async_get_registry()
            remi_entities = []
            for entity_id, entity in entity_registry.entities.items():
                if entity.platform == DOMAIN:
                    remi_entities.append(entity_id)
            
            if remi_entities:
                await hass.services.async_call("homeassistant", "update_entity", {
                    "entity_id": remi_entities
                })
                _LOGGER.info("Triggered update for %d Remi entities", len(remi_entities))
            
            _LOGGER.info("Successfully refreshed all Remi data and triggered entity updates")
            
        except Exception as e:
            _LOGGER.error("Failed to refresh Remi data: %s", e)
    
    hass.services.async_register(DOMAIN, "refresh_data", async_refresh_remi_data)
    
    return True
