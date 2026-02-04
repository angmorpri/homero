async function loadEpisode(index) {
    const r = await fetch("/api/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index: Number(index) }),
    });
    const j = await r.json();
    document.getElementById("out").textContent = JSON.stringify(j, null, 2);
}

document.querySelectorAll(".btnLoad").forEach((btn) => {
    btn.addEventListener("click", () => loadEpisode(btn.dataset.index));
});
