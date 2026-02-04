const COOLDOWN_MS = (window.HOMERO && window.HOMERO.cooldownMs) || 350;

function disableBriefly(btn) {
    btn.disabled = true;
    setTimeout(() => (btn.disabled = false), COOLDOWN_MS);
}

async function refreshStatus() {
    const el = document.getElementById("statusLine");
    try {
        const r = await fetch("/api/status");
        const j = await r.json();

        if (j.error) {
            el.textContent = "Error: " + j.error;
            return;
        }

        const paused = !!j.pause;
        const muted = !!j.mute;
        const title = j.media_title || "(sin título)";

        const btnPlayPause = document.getElementById("btnPlayPause");
        const btnMute = document.getElementById("btnMute");
        if (btnPlayPause) btnPlayPause.textContent = paused ? "▶" : "⏸";
        if (btnMute) btnMute.textContent = muted ? "🔇" : "🔊";

        el.textContent =
            (paused ? "Pausado" : "Reproduciendo") +
            " · " +
            (muted ? "Mute" : "Audio") +
            " · " +
            title;
    } catch (e) {
        el.textContent = "Error consultando estado: " + e;
    }
}

async function doAction(action, btn) {
    disableBriefly(btn);

    const r = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    });

    const j = await r.json();
    const out = document.getElementById("lastAction");

    if (j.cooldown_ms && j.cooldown_ms > 0) {
        out.textContent = "Cooldown activo. Espera " + j.cooldown_ms + "ms";
        return;
    }

    out.textContent = JSON.stringify(j, null, 2);
    setTimeout(refreshStatus, 120);
}

function wireButtons() {
    document.querySelectorAll("button[data-action]").forEach((btn) => {
        btn.addEventListener("click", () => doAction(btn.dataset.action, btn));
    });
}

wireButtons();
refreshStatus();
setInterval(refreshStatus, 1500);
