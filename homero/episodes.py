# 2026/01/30
"""
episodes.py - Episode management for SimpsonsTV.

Episodes are loaded from the same M3U file used by MPV. It is assumed that
they are sorted properly.

All episodes have the same format: "SxxExx[_Title].ext", where "Title" can
contain whitespaces and other characters.

"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass(frozen=True)
class Episode:
    index: int
    season: int
    episode: int
    title: str  # Allows empty title
    filepath: Path
    label: str  # e.g., S01E01 - Title


def load_episodes(path: Path | str) -> list[dict]:
    """Loads the episodes from the episodes file

    Returns a dict seasion -> [episodes], sorted. Each episode is a Episode
    object.

    """
    # List of episodes
    episodes = []
    with open(path, "r", encoding="utf-8") as f:
        for index, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            filename = Path(line).name
            name_part = filename.rsplit(".", 1)[0]  # Remove extension
            parts = name_part.split("_", 1)
            se_ep = parts[0]
            title = parts[1] if len(parts) > 1 else ""

            if len(se_ep) < 4 or se_ep[0] != "S" or "E" not in se_ep:
                continue

            try:
                season_str, episode_str = se_ep[1:].split("E", 1)
                season = int(season_str)
                episode = int(episode_str)
            except ValueError:
                continue

            label = f"S{season:02d}E{episode:02d}"
            if title:
                label += f" - {title}"

            ep = Episode(
                index=index,
                season=season,
                episode=episode,
                title=title,
                filepath=Path(line),
                label=label,
            )
            episodes.append(ep)

    # Dict season -> [episodes]
    seasons = {}
    for ep in episodes:
        seasons.setdefault(ep.season, []).append(ep)
        logger.debug(f"Loaded episode: {ep}")
    return seasons
