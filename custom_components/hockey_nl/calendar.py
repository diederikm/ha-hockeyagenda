"""Calendar platform for Hockey NL."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import HockeyNLApi
from .const import DOMAIN, CONF_TEAMS, CONF_TEAM_ID, CONF_POULE_ID, CONF_DISPLAY_NAME, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)
MATCH_DURATION = timedelta(minutes=70)  # typical field hockey match


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    api: HockeyNLApi = hass.data[DOMAIN][entry.entry_id]
    entities = [
        HockeyCalendar(api, team)
        for team in entry.data[CONF_TEAMS]
    ]
    async_add_entities(entities, update_before_add=True)


class HockeyCalendar(CalendarEntity):
    """Calendar with full season schedule for a team."""

    _attr_icon = "mdi:hockey-sticks"

    def __init__(self, api: HockeyNLApi, team: dict) -> None:
        self._api = api
        self._team_id: int = team[CONF_TEAM_ID]
        self._poule_id: int = team[CONF_POULE_ID]
        self._display_name: str = team[CONF_DISPLAY_NAME]
        self._matches: list[dict] = []

        self._attr_name = f"Hockey {self._display_name} Kalender"
        self._attr_unique_id = f"hockey_nl_calendar_{self._team_id}"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = dt_util.now()
        for match in self._matches:
            start = self._parse_dt(match["date"])
            if start and start >= now and match["status"] != "final":
                return self._to_event(match)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all events between start_date and end_date."""
        events = []
        for match in self._matches:
            start = self._parse_dt(match["date"])
            if start is None:
                continue
            end = start + MATCH_DURATION
            if start <= end_date and end >= start_date:
                events.append(self._to_event(match))
        return events

    def _to_event(self, match: dict) -> CalendarEvent:
        start = self._parse_dt(match["date"])
        end = start + MATCH_DURATION
        home_away = "Thuis" if match["is_home"] else "Uit"
        summary = f"{home_away}: {match['home_team']} - {match['away_team']}"
        location = match["facility_name"]
        if match["facility_address"]:
            location += f", {match['facility_address'].replace(chr(10), ', ')}"
        description = (
            f"Veld: {match['field_name']} ({match['field_type']})\n"
            f"Ronde: {match['round']}"
        )
        if match.get("remarks"):
            description += f"\n{match['remarks']}"
        return CalendarEvent(
            start=start,
            end=end,
            summary=summary,
            location=location,
            description=description,
        )

    def _parse_dt(self, date_str: str) -> datetime | None:
        try:
            return dt_util.parse_datetime(date_str)
        except Exception:
            return None

    async def async_update(self) -> None:
        try:
            self._matches = await self._api.get_matches(self._poule_id, self._team_id)
        except Exception as err:
            _LOGGER.error("Error updating Hockey NL calendar for %s: %s", self._display_name, err, exc_info=True)
