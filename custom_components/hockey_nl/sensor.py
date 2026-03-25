"""Sensor platform for Hockey NL."""
from __future__ import annotations

import logging
from datetime import timedelta, datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import HockeyNLApi
from .const import DOMAIN, CONF_TEAMS, CONF_TEAM_ID, CONF_POULE_ID, CONF_DISPLAY_NAME, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    api: HockeyNLApi = hass.data[DOMAIN][entry.entry_id]
    entities = [
        HockeyMatchSensor(api, team)
        for team in entry.data[CONF_TEAMS]
    ]
    async_add_entities(entities, update_before_add=True)


class HockeyMatchSensor(SensorEntity):
    """Sensor showing the next upcoming match for a team."""

    _attr_icon = "mdi:hockey-sticks"

    def __init__(self, api: HockeyNLApi, team: dict) -> None:
        self._api = api
        self._team_id: int = team[CONF_TEAM_ID]
        self._poule_id: int = team[CONF_POULE_ID]
        self._display_name: str = team[CONF_DISPLAY_NAME]
        self._match: dict | None = None

        self._attr_name = f"Hockey {self._display_name}"
        self._attr_unique_id = f"hockey_nl_{self._team_id}"

    @property
    def native_value(self) -> str | None:
        """State = ISO datetime of the next match, or None."""
        if self._match:
            return self._match["date"]
        return None

    @property
    def extra_state_attributes(self) -> dict:
        if not self._match:
            return {}
        m = self._match
        return {
            "display_name": self._display_name,
            "date": m["date"],
            "status": m["status"],
            "is_home": m["is_home"],
            "home_team": m["home_team"],
            "home_logo": m["home_logo"],
            "away_team": m["away_team"],
            "away_logo": m["away_logo"],
            "opponent": m["opponent"],
            "opponent_logo": m["opponent_logo"],
            "score_home": m["score_home"],
            "score_away": m["score_away"],
            "facility_name": m["facility_name"],
            "facility_address": m["facility_address"],
            "field_name": m["field_name"],
            "field_type": m["field_type"],
            "round": m["round"],
            "remarks": m["remarks"],
        }

    @property
    def entity_picture(self) -> str | None:
        """Show opponent logo as entity picture."""
        if self._match:
            return self._match.get("opponent_logo") or None
        return None

    async def async_update(self) -> None:
        try:
            self._match = await self._api.get_next_match(self._poule_id, self._team_id)
        except Exception as err:
            _LOGGER.error("Error updating Hockey NL sensor for %s: %s", self._display_name, err)
