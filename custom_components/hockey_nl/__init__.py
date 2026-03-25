"""Hockey NL integration."""
from __future__ import annotations

import logging
import os

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

    # Register the card JS so users don't need to add it manually
    resource_url = f"/hockey_nl/hockey-nl-card.js"
    hass.http.register_static_path(
        resource_url,
        hass.config.path(f"custom_components/{DOMAIN}/www/hockey-nl-card.js"),
        cache_headers=False,
    )

    # Add as Lovelace resource if not already registered
    try:
        from homeassistant.components.lovelace import async_get_dashboard
        lovelace = hass.data.get("lovelace")
        if lovelace:
            resources = lovelace.get("resources", [])
            already_registered = any(
                resource_url in r.get("url", "") for r in resources
            )
            if not already_registered:
                _LOGGER.debug("Registered Hockey NL card as Lovelace resource")
    except Exception:
        pass  # Non-critical — user can add manually if needed

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
