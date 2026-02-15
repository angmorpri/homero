/* app.js - JavaScript for the main page of the Homero app.
 * This script handles the sending of commands to the backend and updates the
 * UI accordingly.
 */

const COOLDOWN_MS = 200;  // Prevent spamming
let cooldownTimer = null;
let busy = false;

async function setUp() {
    // Right now, only checks DRY_RUN, in order to show or hide the element
    // that shows the last command and response.
    const r = await fetch("/api/config");
    const config = await r.json();
    console.log("Config:", config);

    // lastAction element
    const out = document.getElementById("lastAction");
    if (config.dry_run) {
        out.style.display = "block";
    } else {
        out.style.display = "none";
    }

    // Status element (this will change)
    const status = document.getElementById("statusLine");
    if (config.dry_run) {
        status.textContent = "DRY RUN MODE - No commands will be sent to MPV";
    } else {
        status.textContent = "Ready to send commands to MPV";
    }
}

function setAllButtonsDisabled(status) {
    document.querySelectorAll("button[data-action]").forEach((btn) => {
        btn.disabled = status;
    });
}

function startCooldown() {
    if (cooldownTimer) clearTimeout(cooldownTimer);
    setAllButtonsDisabled(true);
    cooldownTimer = setTimeout(() => {
        setAllButtonsDisabled(false);
        cooldownTimer = null;
    }, COOLDOWN_MS);
}

async function doAction(action, btn) {
    // Prevent multiple clicks while the action is processing
    if (busy) return;
    busy = true;

    // 1. Disable the button to prevent spamming
    setAllButtonsDisabled(true);

    // 2. Launch the action and wait for the response
    const r = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    });

    const j = await r.json();
    console.log(j);

    // Update the lastAction element with the response (only if DRY_RUN)
    const out = document.getElementById("lastAction");
    out.textContent = JSON.stringify(j, null, 2);

    // 3. Change button icon
    if (action === "toggle_pause") {
        if (btn.textContent === "⏸") {
            btn.textContent = "▶";
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

    // 4. Re-enable buttons after cooldown
    startCooldown();
    busy = false;
}

function wireButtons() {
    document.querySelectorAll("button[data-action]").forEach((btn) => {
        btn.addEventListener("click", () => doAction(btn.dataset.action, btn));
    });
}


setUp();
wireButtons();