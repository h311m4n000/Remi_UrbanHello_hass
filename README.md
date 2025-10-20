# Rémi UrbanHello Integration for Home Assistant

Home Assistant integration `remi_urbanhello_hass` is designed for Rémi UrbanHello.
This is not an official integration by UrbanHello.

## Note about this fork

This fork was created with cursor and Claude and built on top of the original code. So keep this in mind. I know my way around code, but I'm not a coder.

This fork adds the following functionality:
- Retrieves the alarms you set in the App. You can now toggle them on or off
- Allows you to set the illumination of Rémi with a slider (0 - 100)
- Allows you to set the volume of Rémi with a slide (0 - 100)

I have not yet found a way to update the Alarm names in HA automatically when you change them in the App. You will need to restart HA for the alarm names to change if this matters to you.

## Installation

Copy the content of the 'custom_components' folder to your home-assistant folder 'config/custom_components' or install through HACS.
After reboot of Home-Assistant, this integration can be configured through the integration setup UI

Click here to install over HACS:
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pdruart&repository=Remi_UrbanHello_hass&category=integration)
