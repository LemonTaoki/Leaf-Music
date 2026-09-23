from typing import Optional

import httpx

from .config import JAMENDO_CLIENT_ID
from .models import Song

JAMENDO_SEARCH_URL = "https://api.jamendo.com/v3.0/tracks/"


async def search_song(query: str, added_by: str = "") -> Optional[Song]:
    if not JAMENDO_CLIENT_ID:
        raise RuntimeError(
            "JAMENDO_CLIENT_ID set nahi hai. https://devportal.jamendo.com/ par free "
            "account bana kar client_id lo aur env var me daalo."
        )

    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": 1,
        "namesearch": query,
        "audioformat": "mp32",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(JAMENDO_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None

    track = results[0]
    return Song(
        title=f'{track["name"]} - {track["artist_name"]}',
        url=track["audio"],
        source="jamendo",
        added_by=added_by,
        duration=float(track["duration"]) if track.get("duration") else None,
    )
