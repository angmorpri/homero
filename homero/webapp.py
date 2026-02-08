# 2026/01/30
"""
webapp.py - Web App for SimpsonsTV.

"""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from homero.episodes import load_episodes
from homero.mpv import MPVClient

# Paths
PATH_BASE = Path(__file__).resolve().parent
PATH_TEMPLATES = PATH_BASE / "templates"
PATH_STATIC = PATH_BASE / "static"


# Config
DRY_RUN = os.getenv("DRY_RUN", "1").lower() in ("1", "true", "yes")
MPV_SOCKET = os.getenv("MPV_SOCKET", "/run/mpv/socket")

# MPV Client
mpv_client = MPVClient(socket_path=MPV_SOCKET, dry_run=DRY_RUN)

# FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory=str(PATH_TEMPLATES))
app.mount("/static", StaticFiles(directory=str(PATH_STATIC)), name="static")


#
# Views
#
@app.get("/")
def index(request: Request):
    """Renders the index page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dry_run": DRY_RUN,
        },
    )


@app.get("/episodes")
def episodes(request: Request):
    """Renders the episodes page."""
    episodes = load_episodes()
    return templates.TemplateResponse(
        "episodes.html",
        {
            "request": request,
            "seasons": episodes,
            "dry_run": DRY_RUN,
        },
    )


#
# API
#
@app.post("/api/action")
async def api_action(payload: dict):
    """Performs an action on MPV.

    Expects JSON payload with "action": str

    """
    action = payload.get("action", "")
    if action == "toggle_pause":
        return mpv_client.send("cycle pause")
    elif action == "toggle_mute":
        return mpv_client.send("cycle mute")
    elif action == "next":
        return mpv_client.send("playlist-next force")
    elif action == "prev":
        return mpv_client.send("playlist-prev force")
    else:
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

    Expects JSON payload with "filepath": str

    """
    # Get episode index
    idx = payload.get("index", None)
    if idx is not None:
        return JSONResponse(
            status_code=400,
            content={
                "error": "index_not_supported",
            },
        )
    try:
        idx = int(idx)
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_index",
            },
        )

    # Get all episodes
    episodes = load_episodes()
    target = next((e for e in episodes if e.index == idx), None)
    if target is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "episode_not_found",
                "index": idx,
            },
        )

    # Prepare command
    resp = mpv_client.send(f"loadfile {str(target.filepath)} replace")
    return {
        "action": "load",
        "episode": {
            "index": target.index,
            "label": target.label,
            "path": str(target.filepath),
        },
        "mpv": resp,
    }
