from datetime import timedelta
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

# Define update interval (2 minutes for switches to catch changes faster)
SCAN_INTERVAL = timedelta(minutes=2)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rémi bedtime/alarm switches based on a config entry."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]
    bedtime_settings = hass.data[DOMAIN].get("bedtime_settings", {})

    switches = []
    
    for device in devices:
        device_id = device["objectId"]
        device_name = device.get("name", "Unknown Device")
        device_settings = bedtime_settings.get(device_id, [])
        
        _LOGGER.info("Found %d bedtime settings for device %s", len(device_settings), device_name)
        
        # Log the settings for debugging
        for i, setting in enumerate(device_settings):
            _LOGGER.info("Setting %d: %s", i, setting)
        
        # Create a switch for each bedtime setting
        for setting in device_settings:
            switch = RemiBedtimeSwitch(api, device, setting)
            switches.append(switch)
        
        # If no settings found, create a placeholder switch
        if not device_settings:
            _LOGGER.warning("No bedtime settings found for device %s, creating placeholder", device_name)
            placeholder_switch = RemiBedtimeSwitch(api, device, None)
            switches.append(placeholder_switch)

    async_add_entities(switches, update_before_add=True)

class RemiBedtimeSwitch(SwitchEntity):
    """Representation of a Rémi bedtime/alarm setting switch."""

    def __init__(self, api, device, setting):
        self._api = api
        self._device = device
        self._setting = setting
        self._device_id = device["objectId"]
        self._device_name = device.get("name", "Unknown Device")
        
        if setting:
            self._setting_id = setting.get("objectId", "unknown")
            self._setting_name = setting.get("name", f"Bedtime Setting {self._setting_id}")
            self._is_on = setting.get("enabled", False)
            self._time = setting.get("time", "Unknown")
            self._days = setting.get("days", [])
        else:
            # Placeholder for when settings can't be loaded
            self._setting_id = "placeholder"
            self._setting_name = f"{self._device_name} Bedtime Setting"
            self._is_on = False
            self._time = "Unknown"
            self._days = []

    @property
    def device_info(self):
        """Return device information to link the entity to the integration."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"Rémi {self._device_name}",
            "manufacturer": "UrbanHello",
            "model": "Rémi Clock",
            "via_device": (DOMAIN, self._device_id),
        }

    @property
    def name(self):
        """Return the name of the switch."""
        name = f"Rémi {self._device_name} - {self._setting_name}"
        if self._setting and self._setting.get("simulated"):
            name += " (Simulated)"
        elif self._setting and not self._setting.get("simulated"):
            name += " (Event)"
        return name

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"{self._device_id}_{self._setting_id}"

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._is_on

    @property
    def icon(self):
        """Return the icon for the switch."""
        return "mdi:alarm" if self._is_on else "mdi:alarm-off"

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {
            "time": self._time,
            "days": self._days,
            "setting_id": self._setting_id,
        }
        if self._setting and self._setting.get("simulated"):
            attrs["simulated"] = True
        elif self._setting:
            # Add additional Event-specific attributes
            attrs.update({
                "recurrence": self._setting.get("recurrence", []),
                "event_time": self._setting.get("event_time", []),
                "cmd": self._setting.get("cmd", 0),
                "brightness": self._setting.get("brightness", 100),
                "volume": self._setting.get("volume", 0),
                "length_min": self._setting.get("length_min", 0),
                "lightnight": self._setting.get("lightnight", [255, 255, 255])
            })
        return attrs

    async def async_turn_on(self, **kwargs):
        """Turn on the bedtime setting."""
        if self._setting_id == "placeholder":
            _LOGGER.warning("Cannot toggle placeholder bedtime setting")
            return
            
        try:
            await self._api.toggle_bedtime_setting(self._setting_id, True)
            self._is_on = True
            _LOGGER.info("Turned on bedtime setting %s for %s", self._setting_name, self._device_name)
        except Exception as e:
            _LOGGER.error("Failed to turn on bedtime setting %s: %s", self._setting_name, e)

    async def async_turn_off(self, **kwargs):
        """Turn off the bedtime setting."""
        if self._setting_id == "placeholder":
            _LOGGER.warning("Cannot toggle placeholder bedtime setting")
            return
            
        try:
            await self._api.toggle_bedtime_setting(self._setting_id, False)
            self._is_on = False
            _LOGGER.info("Turned off bedtime setting %s for %s", self._setting_name, self._device_name)
        except Exception as e:
            _LOGGER.error("Failed to turn off bedtime setting %s: %s", self._setting_name, e)

    async def async_update(self):
        """Fetch the latest bedtime setting state from the API."""
        if self._setting_id == "placeholder":
            return
            
        try:
            # First try to get from cached data (from refresh service)
            from homeassistant.core import HomeAssistant
            hass = HomeAssistant.instance()
            if hass and DOMAIN in hass.data and "bedtime_settings" in hass.data[DOMAIN]:
                cached_settings = hass.data[DOMAIN]["bedtime_settings"].get(self._device_id, [])
                for setting in cached_settings:
                    if setting.get("objectId") == self._setting_id:
                        self._update_from_setting(setting)
                        return
            
            # Fallback to API call if no cached data
            settings = await self._api.get_bedtime_settings(self._device_id)
            for setting in settings:
                if setting.get("objectId") == self._setting_id:
                    self._update_from_setting(setting)
                    break
        except Exception as e:
            _LOGGER.error("Failed to update bedtime setting %s: %s", self._setting_name, e)

    def _update_from_setting(self, setting):
        """Update entity state from setting data."""
        self._setting = setting
        self._is_on = setting.get("enabled", False)
        self._time = setting.get("time", "Unknown")
        self._days = setting.get("days", [])
        
        # Update the setting name in case it changed in the app
        new_name = setting.get("name", f"Event {self._time}")
        if new_name != self._setting_name:
            old_name = self._setting_name
            self._setting_name = new_name
            _LOGGER.info("Updated setting name from app: '%s' -> '%s'", old_name, new_name)
