/* episodes.js - JavaScript for the episodes page of the Homero app.
 * This script handles the loading of episodes and updates the UI accordingly.
 */

const COOLDOWN_MS = 200;  // Prevent spamming
let cooldownTimer = null;
let busy = false;

async function setUp() {
    // Check DRY_RUN mode in order to show dummy responses in the UI
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
}

function setAllButtonsDisabled(status) {
    document.querySelectorAll("button[data-index]").forEach((btn) => {
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

async function loadEpisode(index) {
    // Prevent multiple clicks while the action is processing
    if (busy) return;
    busy = true;

    // 1. Disable all buttons to prevent spamming
    setAllButtonsDisabled(true);

    // 2. Send the load command and wait for the response
    const r = await fetch("/api/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index: Number(index) }),
    });

    const j = await r.json();
    console.log(j);

    // Update the lastAction element with the response (only if DRY_RUN)
    const out = document.getElementById("lastAction");
    out.textContent = JSON.stringify(j, null, 2);

    // 3. Re-enable buttons after cooldown
    startCooldown();
    busy = false;
}


setUp();
document.querySelectorAll(".btnLoad").forEach((btn) => {
    btn.addEventListener("click", () => loadEpisode(btn.dataset.index));
});
