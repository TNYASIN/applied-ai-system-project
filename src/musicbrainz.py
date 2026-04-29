"""
MusicBrainz songwriter credit lookup.
Fetches Written-by / Composed-by / Lyricist credits for a track title + artist.
Rate-limited to 1 request/second as required by MusicBrainz.
"""

import time
import requests
from typing import List, Dict, Optional

_BASE = "https://musicbrainz.org/ws/2"
_HEADERS = {
    "User-Agent": "Muze/1.0 (music-discovery-app; contact@muze-app.example)",
    "Accept": "application/json",
}
_WRITER_TYPES = {"written by", "composed by", "lyricist", "composer", "writer", "music", "words and music"}


def _get(path: str, params: dict) -> Optional[dict]:
    try:
        resp = requests.get(f"{_BASE}/{path}", params={**params, "fmt": "json"},
                            headers=_HEADERS, timeout=8)
        time.sleep(1.1)  # MusicBrainz rate limit: 1 req/sec
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


def lookup_writers(title: str, artist: str) -> List[Dict]:
    """
    Return list of {name, role} dicts for people credited as writers/composers.
    Returns [] if nothing found or on any error.
    """
    # Step 1 — find the recording MBID
    data = _get("recording/", {
        "query": f'recording:"{title}" AND artist:"{artist}"',
        "limit": 1,
    })
    if not data:
        return []
    recordings = data.get("recordings", [])
    if not recordings:
        return []
    rec_id = recordings[0]["id"]

    # Step 2 — get work relations for that recording
    data = _get(f"recording/{rec_id}", {"inc": "work-rels"})
    if not data:
        return []
    work_ids = [
        r["work"]["id"]
        for r in data.get("relations", [])
        if r.get("type") == "performance" and r.get("work")
    ]
    if not work_ids:
        return []

    # Step 3 — get artist relations for the first work (the composition)
    data = _get(f"work/{work_ids[0]}", {"inc": "artist-rels"})
    if not data:
        return []

    writers = []
    for rel in data.get("relations", []):
        rel_type = rel.get("type", "").lower()
        if rel_type in _WRITER_TYPES:
            name = rel.get("artist", {}).get("name", "")
            if name:
                writers.append({"name": name, "role": rel.get("type", "Written by").title()})
    return writers


def lookup_writers_bulk(tracks: List[Dict], limit: int = 5) -> Dict[str, List[Dict]]:
    """
    Look up writers for up to `limit` tracks.
    tracks: list of dicts with 'name' and 'artists' keys (Spotify track format).
    Returns {track_title: [{"name": ..., "role": ...}]}.
    """
    results = {}
    for track in tracks[:limit]:
        title = track.get("name", "")
        artist = (track.get("artists") or [{}])[0].get("name", "")
        if not title or not artist:
            continue
        writers = lookup_writers(title, artist)
        if writers:
            results[title] = writers
    return results
