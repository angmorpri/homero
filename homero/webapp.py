# 2026/01/30
"""
webapp.py - Web App for SimpsonsTV.

"""

import json
import os
import socket
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

# Paths
PATH_LOCAL_EPISODES = Path(__file__).parent.parent / "data" / "loop.m3u"


# Config
MPV_SOCKET = os.getenv("MPV_SOCKET", "/run/mpv/socket")
EPISODES_FILE = os.getenv("PATH_HOMERO_EPISODES", PATH_LOCAL_EPISODES)
DRY_RUN = os.getenv("HOMERO_DRY_RUN", "0") == "1"
COOLDOWN_MS = int(os.getenv("HOMERO_COOLDOWN_MS", "350"))

# Cooldown simple
_last_action_ts = {}

# FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

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


