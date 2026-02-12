# Homero
## Web app for SimpsonsTV
Simple web application to launch MPV commands for simple actions on a Simpsons TV: pause, rewind, mute, change episode...

With `uv`, run via:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Envvars to be configured are:

* **`EPISODES_FILE`**: path to the M3U file used by `mpv`.
* **`MPV_SOCKET`**: path to the socket created for `mpv`.
* **`LOG_LEVEL`**: log level, by default, "DEBUG".

If **`DRY_RUN`** is set to **1**, `mpv` commands won't be run, just printed in the app.
