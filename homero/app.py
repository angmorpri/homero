# 2026/01/30
"""
webapp.py - Main code for the SimpsonsTV web application.

Initializes logging, handles configuration, MPV client, and defines the FastAPI
app.

"""

import os
import sys
from itertools import groupby
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from homero.episodes import load_episodes
from homero.mpv import MPVClient

#
# Paths
#
PATH_BASE = Path(__file__).resolve().parent
PATH_TEMPLATES = PATH_BASE / "templates"
PATH_STATIC = PATH_BASE / "static"
PATH_LOCAL_EPISODES = PATH_BASE.parent / "data" / "mock.m3u"
PATH_LOCAL_LOG = PATH_BASE.parent / "logs"
PATH_LOCAL_LOG.mkdir(parents=True, exist_ok=True)

#
# Config
#
DRY_RUN = os.getenv("DRY_RUN", "1").lower() in ("1", "true", "yes")
MPV_SOCKET = os.getenv("MPV_SOCKET", "/run/mpv/socket")
EPISODES_FILE = os.getenv("PATH_HOMERO_EPISODES", PATH_LOCAL_EPISODES)
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

#
# Logger
#
logger.remove()
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm}</green> | <level>{level}</level> | <level>{message}</level>",
    enqueue=True,
    backtrace=False,
    diagnose=False,
)
logger.add(
    PATH_LOCAL_LOG / "homero.log",
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm}</green> | <level>{level}</level> | <level>{message}</level>",
    rotation="10 MB",
    retention="7 days",
    enqueue=True,
)
logger.info("Welcome to SimpsonsTV!")
logger.info("DRY_RUN = {}", DRY_RUN)

#
# MPV Client
#
mpv_client = MPVClient(socket_path=MPV_SOCKET, dry_run=DRY_RUN)
logger.info(f"MPV Client initialized with socket: {MPV_SOCKET}")

#
# Episodes
#
episodes, n_seasons = load_episodes(EPISODES_FILE)
logger.info(
    f"Loaded {len(episodes)} episodes from {n_seasons} seasons from {EPISODES_FILE}"
)
episodes_per_season = {
    season: list(eps) for season, eps in groupby(episodes, key=lambda e: e.season)
}

#
# FastAPI app
#
app = FastAPI()
templates = Jinja2Templates(directory=str(PATH_TEMPLATES))
app.mount("/static", StaticFiles(directory=str(PATH_STATIC)), name="static")
logger.info(
    f"FastAPI app initialized with templates: {PATH_TEMPLATES} and static: {PATH_STATIC}"
)


# Views
@app.get("/")
def index(request: Request):
    """Renders the index page."""
    # Check current episode in MPV
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dry_run": DRY_RUN,
        },
    )


@app.get("/episodes")
def list_episodes(request: Request):
    """Renders the episodes page."""
    return templates.TemplateResponse(
        "episodes.html",
        {
            "request": request,
            "seasons": episodes_per_season,
            "dry_run": DRY_RUN,
        },
    )


# API
@app.get("/api/config")
async def api_config():
    """Returns the current configuration."""
    return {
        "mpv_socket": MPV_SOCKET,
        "episodes_file": EPISODES_FILE,
        "dry_run": DRY_RUN,
    }


@app.post("/api/action")
async def api_action(payload: dict):
    """Performs an action on MPV.

    Expects JSON payload with {"action": str}

    """
    logger.info(f"Received action request: {payload}")

    # Identify action, run associated MPV command
    action = payload.get("action", "")
    if action == "toggle_pause":
        return mpv_client.send("cycle pause")
    elif action == "toggle_mute":
        return mpv_client.send("cycle mute")
    elif action == "next":
        res1 = mpv_client.send("playlist-next force")
        res2 = mpv_client.send("set_property time-pos 0")
        return res1, res2
    elif action == "prev":
        return mpv_client.send("playlist-prev force")
    else:
        logger.warning(f"Unknown action requested: '{action}'")
        return JSONResponse(
            status_code=400,
            content={
                "error": "unknown_action",
                "action": action,
            },
        )


@app.post("/api/load")
async def api_load(payload: dict):
    """Loads an episode in MPV.

    Expects JSON payload with {"index": int}

    """
    logger.info(f"Received load request: {payload}")

    # Get episode index
    idx = payload.get("index", None)
    if idx is None:
        logger.warning(f"Episode index not supported in load API: {idx}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "episode_index_missing",
            },
        )
    try:
        idx = int(idx)
    except (TypeError, ValueError):
        logger.warning(f"Invalid index provided: {idx}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "episode_index_invalid",
            },
        )

    # Get all episodes
    try:
        target = episodes[idx]
    except IndexError:
        logger.warning(f"Episode not found for index: {idx}")
        return JSONResponse(
            status_code=404,
            content={
                "error": "episode_index_out_of_range",
                "index": idx,
            },
        )

    # Prepare command
    return mpv_client.send(["loadfile", str(target.filepath), "replace"])
