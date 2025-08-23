// games.js

async function loadGames(){
  const list = document.getElementById("games-list");
  if (!list) return;

  const data = await api("/api/games");
  list.innerHTML = "";
  (data.results || []).forEach(g => {
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>${g.title}</strong> — ${g.category || "General"} (${g.difficulty || "N/A"})
      <div>${g.description || ""}</div>
      ${g.url_or_embed ? `<a href="${g.url_or_embed}" target="_blank">Play</a>` : ""}
    `;
    list.appendChild(li);
  });
}
document.addEventListener("DOMContentLoaded", loadGames);
