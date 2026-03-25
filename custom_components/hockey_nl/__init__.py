"""Hockey NL integration."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HockeyNLApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the Lovelace card as a frontend resource."""
    hass.data.setdefault(DOMAIN, {})

    resource_url = f"/hockey_nl/hockey-nl-card.js"
    card_path = hass.config.path(f"custom_components/{DOMAIN}/www/hockey-nl-card.js")

    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths([
            StaticPathConfig(resource_url, card_path, cache_headers=False)
        ])
        _LOGGER.debug("Registered Hockey NL card at %s", resource_url)
    except Exception as err:
        _LOGGER.warning("Could not register Hockey NL card: %s", err)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    session = async_get_clientsession(hass)
    api = HockeyNLApi(session)
    await api.ensure_authenticated()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
