# 2026/02/08
"""
mpv.py - MPV IPC interface for SimpsonsTV.

"""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any


#
# MPV Templates
#
@dataclass
class MPVCommand:
    command: list[str]
    request_id: int

    def to_json(self) -> str:
        return json.dumps({"command": self.command, "request_id": self.request_id})


@dataclass
class MPVResponse:
    error: str
    data: Any
    request_id: int

    @staticmethod
    def from_json(json_str: str) -> MPVResponse:
        obj = json.loads(json_str)
        return MPVResponse(
            error=obj.get("error", ""),
            data=obj.get("data"),
            request_id=obj.get("request_id", 0),
        )


#
# Main class
#
class MPVClient:
    """MPV Client for sending commands to MPV via IPC socket."""

    _REQUEST_COUNTER = 100

    def __init__(self, socket_path: str, dry_run: bool = False) -> None:
        self.socket_path = socket_path
        self.dry_run = dry_run

    def send(self, command: str) -> tuple[MPVCommand, MPVResponse]:
        """Builds and sends a command to MPV, returns the command and response
        objects.

        """
        # Prepare command
        mpv_command = MPVCommand(
            command=list(command.split()),
            request_id=MPVClient._REQUEST_COUNTER,
        )
        MPVClient._REQUEST_COUNTER += 1

        # If DRY_RUN, return command and a dummy response
        if self.dry_run:
            return mpv_command, MPVResponse(
                error="dry_run",
                data=None,
                request_id=mpv_command.request_id,
            )

        # Send command to MPV
        data = (mpv_command.to_json() + "\n").encode("utf-8")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(self.socket_path)
            client.sendall(data)

            # Read response
            response = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response += chunk

        # Parse response
        res = response.split(b"\n")[0].decode("utf-8", errors="replace").strip()
        if not res:
            return mpv_command, MPVResponse(
                error="Empty response from MPV",
                data=None,
                request_id=mpv_command.request_id,
            )
        try:
            mpv_response = MPVResponse.from_json(res)
            return mpv_command, mpv_response
        except json.JSONDecodeError as e:
            return mpv_command, MPVResponse(
                error=f"Invalid JSON response from MPV: {e}",
                data=res,
                request_id=mpv_command.request_id,
            )
