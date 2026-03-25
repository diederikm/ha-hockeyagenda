"""API client for app.hockeyweerelt.nl."""
from __future__ import annotations

import hashlib
import logging
import math
import re
import time
import uuid
from urllib.parse import urlparse, parse_qs

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://app.hockeyweerelt.nl"
API_VERSION = "7"


class HockeyNLApi:
    """Client for the HockeyWeerelt API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._device_uuid: str | None = None
        self._device_token: str | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def ensure_authenticated(self) -> None:
        """Register device and obtain JWT token if not already done."""
        if self._device_token:
            return
        self._device_uuid = str(uuid.uuid4())
        async with self._session.post(
            f"{BASE_URL}/device/register",
            json={"uuid": self._device_uuid, "os": "Web"},
        ) as resp:
            data = await resp.json()
        self._device_token = data["token"]
        _LOGGER.debug("Registered device %s", self._device_uuid)

    def _signature(self, path: str) -> tuple[str, str]:
        """Return (timestamp, sha1_signature) for a given path."""
        parsed = urlparse(path)
        pathname = re.sub(r"[^a-zA-Z0-9\-/]+", "", parsed.path)
        timestamp = str(math.floor(time.time()))
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        query_str = "".join(
            f"{re.sub(r'[^a-zA-Z0-9-/=]+', '', k)}"
            f"={re.sub(r'[^a-zA-Z0-9-/=]+', '', ''.join(v))}"
            for k, v in query_params.items()
            if k
        )
        reversed_uuid = self._device_uuid[::-1]
        to_hash = f"{timestamp}{pathname}{query_str}{reversed_uuid}"
        sha1 = hashlib.sha1(to_hash.encode()).hexdigest()
        return timestamp, sha1

    async def _get(self, path: str) -> dict:
        """Authenticated GET request."""
        await self.ensure_authenticated()
        timestamp, sig = self._signature(path)
        headers = {
            "X-HAPI-Authorization": self._device_token,
            "X-HAPI-Timestamp": timestamp,
            "X-HAPI-Signature": sig,
            "X-HAPI-Version": API_VERSION,
            "Accept": "application/json",
        }
        _LOGGER.debug("GET %s", BASE_URL + path)
        async with self._session.get(BASE_URL + path, headers=headers) as resp:
            _LOGGER.debug("Response %s for %s", resp.status, path)
            resp.raise_for_status()
            return await resp.json()

    # ------------------------------------------------------------------
    # Public interface — stable regardless of underlying API changes
    # ------------------------------------------------------------------

    async def get_clubs(self) -> list[dict]:
        """Return list of clubs: [{id, name, federation_reference_id}]."""
        data = await self._get("/clubs")
        return [
            {
                "id": c["federation_reference_id"],
                "name": c["name"],
            }
            for c in data.get("data", [])
        ]

    async def get_teams(self, club_id: str) -> list[dict]:
        """Return teams for a club: [{id, name, poule_id}]."""
        data = await self._get(f"/clubs/{club_id}")
        teams = []
        for t in data.get("data", {}).get("teams", []):
            poule_id = t.get("recent_poule_id")
            if not poule_id:
                continue
            teams.append(
                {
                    "id": t["id"],
                    "name": t["name"],
                    "poule_id": poule_id,
                    "logo": t.get("logo", ""),
                }
            )
        return teams

    async def get_matches(self, poule_id: int, team_id: int) -> list[dict]:
        """Return all matches for a team, normalised to a stable schema."""
        data = await self._get(f"/poules/{poule_id}/teams/{team_id}")
        _LOGGER.debug("get_matches response keys: %s", list(data.keys()) if data else None)
        data_obj = data.get("data") or {}
        poule_obj = data_obj.get("poule") or {}
        raw_matches = poule_obj.get("matches") or []
        _LOGGER.debug("Found %d raw matches for team %s", len(raw_matches), team_id)

        matches = []
        for m in raw_matches:
            home = m.get("home", {})
            away = m.get("away", {})
            if home.get("id") != team_id and away.get("id") != team_id:
                continue  # not our team
            loc = m.get("location", {})
            facility = loc.get("facility", {})
            field = loc.get("field", {})
            is_home = home.get("id") == team_id
            opponent = away if is_home else home
            matches.append(
                {
                    "id": m["id"],
                    "date": m["date"],
                    "status": m.get("status"),
                    "is_home": is_home,
                    "home_team": home.get("name", ""),
                    "home_logo": home.get("logo", ""),
                    "away_team": away.get("name", ""),
                    "away_logo": away.get("logo", ""),
                    "opponent": opponent.get("name", ""),
                    "opponent_logo": opponent.get("logo", ""),
                    "score_home": m.get("score", {}).get("home"),
                    "score_away": m.get("score", {}).get("away"),
                    "facility_name": facility.get("name", ""),
                    "facility_address": facility.get("address", ""),
                    "field_name": field.get("name", ""),
                    "field_type": field.get("type", ""),
                    "round": m.get("round"),
                    "remarks": m.get("remarks", {}).get("official", ""),
                    "poule_id": m.get("poule_id"),
                }
            )
        matches.sort(key=lambda x: x["date"])
        return matches

    async def get_next_match(self, poule_id: int, team_id: int) -> dict | None:
        """Return the next upcoming match, or None."""
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        matches = await self.get_matches(poule_id, team_id)
        upcoming = [
            m for m in matches
            if m["date"] >= now and m["status"] != "final"
        ]
        return upcoming[0] if upcoming else None
