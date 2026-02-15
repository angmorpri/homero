# 2026/01/30
"""
episodes.py - Episode management for SimpsonsTV.

Episodes are loaded from an .episodes file, which is a text file where each
line must be the path to the episode and the duration in seconds, separated by
';;'. For example:

C:/path/to/episodes/S01E01_Title.mp4;;3600

The filename must follow the format SxxExx[_Title].ext, where Sxx is the season
number, Exx is the episode number, and Title is an optional title.

"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass(frozen=True)
class Episode:
    index: int
    filepath: Path
    season: int
    episode: int
    title: str  # Allows empty title
    label: str  # e.g., S01E01 - Title


def load_episodes(path: Path | str) -> tuple[list[Episode], int]:
    """Creates a list of Episode objects from the given .episodes file.

    Returns the list of episodes and the number of seasons.

    """
    # Check if the file exists and is valid
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"Invalid episodes file: {path}")

    # List of episodes
    episodes = []
    seasons = set()
    with path.open("r", encoding="utf-8") as f:
        for filepath in f:
            filepath = filepath.strip()
            if not filepath:
                continue  # Skip empty lines

            # Path parts
            name_part = Path(filepath).name.split(".", 1)[0]  # Remove extension
            parts = name_part.split("_", 1)
            se_ep = parts[0]
            title = parts[1] if len(parts) > 1 else ""

            if len(se_ep) < 4 or se_ep[0] != "S" or "E" not in se_ep:
                logger.warning(f"Skipping file with invalid format: {filepath}")
                continue

            try:
                season_str, episode_str = se_ep[1:].split("E", 1)
                season = int(season_str)
                episode = int(episode_str)
            except ValueError:
                logger.warning(
                    f"Skipping file with invalid season/episode format: {filepath}"
                )
                continue

            label = f"S{season:02d}E{episode:02d}"
            if title:
                label += f" - {title}"

            ep = Episode(
                index=len(episodes),
                season=season,
                episode=episode,
                title=title,
                filepath=Path(filepath),
                label=label,
            )
            episodes.append(ep)
            seasons.add(season)

    return episodes, len(seasons)
