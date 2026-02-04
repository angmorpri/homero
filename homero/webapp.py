# 2026/01/30
"""
webapp.py - Web App for SimpsonsTV.

"""

import json
import os
import socket
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from homero.episodes import load_episodes

# Paths
PATH_BASE = Path(__file__).resolve().parent
PATH_TEMPLATES = PATH_BASE / "templates"
PATH_STATIC = PATH_BASE / "static"


# Config
MPV_SOCKET = os.getenv("MPV_SOCKET", "/run/mpv/socket")
DRY_RUN = True
COOLDOWN_MS = int(os.getenv("HOMERO_COOLDOWN_MS", "350"))

_last_action_ts = {}

# FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory=str(PATH_TEMPLATES))
app.mount("/static", StaticFiles(directory=str(PATH_STATIC)), name="static")


# MPV IPC
def _mpv_send(cmd_obj: dict) -> dict:
    """Sends a JSON command to MPV, returns the JSON response.

    If DRY_RUN is enabled, it just logs the command and returns an empty dict.

    """
    if DRY_RUN:
        return {"dry_run": True, "would_send": cmd_obj}

    data = (json.dumps(cmd_obj) + "\n").encode("utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(MPV_SOCKET)
        client.sendall(data)

        # Read response
        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk

    line = response.split(b"\n")[0].decode("utf-8", errors="replace").strip()
    if not line:
        return {"error": "Empty response from MPV"}
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response from MPV: {e}", "raw_response": line}


def mpv_command(*args: str) -> dict:
    """Sends a command to MPV via IPC"""
    return _mpv_send({"command": list(args)})


def mpv_get(prop: str) -> dict:
    """Gets a property from MPV via IPC"""
    return _mpv_send({"command": ["get_property", prop]})


def cooldown(action: str) -> tuple[bool, int]:
    """Checks if the action is in cooldown.

    Returns (allowed: bool, wait_ms: int)

    """
    now = time.monotonic()
    last = _last_action_ts.get(action, 0.0)
    elapsed = int((now - last) * 1000.0)
    if elapsed < COOLDOWN_MS:
        return False, (COOLDOWN_MS - elapsed)
    _last_action_ts[action] = now
    return True, 0


# Views
@app.get("/")
def index(request: Request):
    """Renders the index page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dry_run": DRY_RUN,
            "cooldown_ms": COOLDOWN_MS,
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


# API
@app.get("/api/config")
def api_config():
    """Returns the config as JSON."""
    return {
        "dry_run": DRY_RUN,
        "cooldown_ms": COOLDOWN_MS,
    }


@app.get("/api/status")
def api_status():
    """Returns the MPV status as JSON."""
    if DRY_RUN:
        return {
            "dry_run": True,
            "pause": False,
            "mute": False,
            "media_title": "Dry Run Mode",
        }

    pause = mpv_get("pause")
    mute = mpv_get("mute")
    title = mpv_get("media-title")

    def _val(resp, default=None):
        if isinstance(resp, dict) and resp.get("error") == "success":
            return resp.get("data", default)
        return default

    return {
        "dry_run": False,
        "pause": _val(pause, False),
        "mute": _val(mute, False),
        "media_title": _val(title, None),
    }


@app.post("/api/action")
async def api_action(payload: dict):
    """Performs an action on MPV.

    Expects JSON payload with "action": str

    """
    # Check cooldown
    action = payload.get("action", "")
    allowed, wait_ms = cooldown(action)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "cooldown",
                "cooldown_ms": wait_ms,
            },
        )

    # Perform action
    if action == "toggle_pause":
        return mpv_command("cycle", "pause")
    elif action == "toggle_unmute":
        return mpv_command("cycle", "mute")
    elif action == "next":
        return mpv_command("playlist-next", "force")
    elif action == "prev":
        return mpv_command("playlist-prev", "force")
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
    # Check cooldown
    allowed, wait_ms = cooldown("load_episode")
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "cooldown",
                "cooldown_ms": wait_ms,
            },
        )

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
    resp = mpv_command("loadfile", str(target.filepath), "replace")
    return {
        "action": "load",
        "episode": {
            "index": target.index,
            "label": target.label,
            "path": str(target.filepath),
        },
        "mpv": resp,
    }
