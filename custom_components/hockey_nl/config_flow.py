"""Config flow for Hockey NL."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HockeyNLApi
from .const import (
    DOMAIN,
    CONF_CLUB_ID,
    CONF_CLUB_NAME,
    CONF_TEAM_ID,
    CONF_TEAM_NAME,
    CONF_POULE_ID,
    CONF_DISPLAY_NAME,
    CONF_TEAMS,
)

_LOGGER = logging.getLogger(__name__)


class HockeyNLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Hockey NL."""

    VERSION = 1

    def __init__(self) -> None:
        self._api: HockeyNLApi | None = None
        self._clubs: list[dict] = []
        self._teams: list[dict] = []
        self._selected_club_id: str | None = None
        self._selected_club_name: str | None = None
        self._configured_teams: list[dict] = []

    def _get_api(self) -> HockeyNLApi:
        if self._api is None:
            session = async_get_clientsession(self.hass)
            self._api = HockeyNLApi(session)
        return self._api

    # ------------------------------------------------------------------
    # Step 1: Select club
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors = {}

        if user_input is not None:
            search = user_input.get("club_search", "").strip().lower()
            matches = [c for c in self._clubs if search in c["name"].lower()]
            if len(matches) == 0:
                errors["club_search"] = "no_clubs_found"
            elif len(matches) == 1:
                self._selected_club_id = matches[0]["id"]
                self._selected_club_name = matches[0]["name"]
                return await self.async_step_team()
            else:
                # Multiple matches — show a dropdown
                club_map = {c["name"]: c["id"] for c in matches}
                if user_input.get("club_name"):
                    self._selected_club_id = club_map[user_input["club_name"]]
                    self._selected_club_name = user_input["club_name"]
                    return await self.async_step_team()
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Optional("club_search", default=user_input.get("club_search", "")): str,
                            vol.Optional("club_name"): vol.In(list(club_map.keys())),
                        }
                    ),
                    errors=errors,
                )

        # Load clubs on first visit
        if not self._clubs:
            try:
                self._clubs = await self._get_api().get_clubs()
            except Exception as err:
                _LOGGER.exception("Failed to load clubs: %s", err)
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({"club_search": str}),
                    errors={"base": "cannot_connect"},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("club_search"): str,
                }
            ),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 2: Select team
    # ------------------------------------------------------------------

    async def async_step_team(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors = {}

        if not self._teams:
            try:
                self._teams = await self._get_api().get_teams(self._selected_club_id)
            except Exception as err:
                _LOGGER.exception("Failed to load teams: %s", err)
                return self.async_abort(reason="cannot_connect")

        if not self._teams:
            return self.async_abort(reason="no_teams_found")

        team_names = [t["name"] for t in self._teams]
        team_map = {t["name"]: t for t in self._teams}

        if user_input is not None:
            team = team_map[user_input["team_name"]]
            display_name = user_input.get("display_name", "").strip() or team["name"]
            self._configured_teams.append(
                {
                    CONF_TEAM_ID: team["id"],
                    CONF_TEAM_NAME: team["name"],
                    CONF_POULE_ID: team["poule_id"],
                    CONF_DISPLAY_NAME: display_name,
                }
            )
            if user_input.get("add_another"):
                return await self.async_step_team(None)
            return self._create_entry()

        return self.async_show_form(
            step_id="team",
            data_schema=vol.Schema(
                {
                    vol.Required("team_name"): vol.In(team_names),
                    vol.Optional("display_name"): str,
                    vol.Optional("add_another", default=False): bool,
                }
            ),
            description_placeholders={"club_name": self._selected_club_name},
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Finish
    # ------------------------------------------------------------------

    def _create_entry(self) -> config_entries.FlowResult:
        title = (
            self._configured_teams[0][CONF_DISPLAY_NAME]
            if len(self._configured_teams) == 1
            else self._selected_club_name
        )
        return self.async_create_entry(
            title=title,
            data={
                CONF_CLUB_ID: self._selected_club_id,
                CONF_CLUB_NAME: self._selected_club_name,
                CONF_TEAMS: self._configured_teams,
            },
        )
