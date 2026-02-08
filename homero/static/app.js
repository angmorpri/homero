async function doAction(action, btn) {
    // 1. Disable the button to prevent spamming
    btn.disabled = true;

    // 2. Launch the action
    const r = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    });

    const j = await r.json();
    const out = document.getElementById("lastAction");
    out.textContent = JSON.stringify(j, null, 2);

    // 3. Change button icon
    if (action === "toggle_pause") {
        if (btn.textContent === "⏸") {
            btn.textContent = "▶️";
        } else {
            btn.textContent = "⏸";
        }
    } else if (action === "toggle_mute") {
        if (btn.textContent === "🔊") {
            btn.textContent = "🔇";
        } else {
            btn.textContent = "🔊";
        }
    }

    // 4. Re-enable the button after the action is complete
    btn.disabled = false;
}

function wireButtons() {
    document.querySelectorAll("button[data-action]").forEach((btn) => {
        btn.addEventListener("click", () => doAction(btn.dataset.action, btn));
    });
}

wireButtons();
