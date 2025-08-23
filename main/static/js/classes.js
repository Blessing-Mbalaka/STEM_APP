// classes.js

async function loadClasses(){
  const container = document.getElementById("classes-list");
  if (!container) return;

  const data = await api("/api/classes");
  container.innerHTML = "";
  (data.results || []).forEach(s => {
    const d = document.createElement("div");
    d.innerHTML = `
      <strong>${s.title}</strong> (${s.starts_at} → ${s.ends_at})
      <button class="reserve" data-id="${s.id}">Reserve</button>
    `;
    container.appendChild(d);
  });

  container.addEventListener("click", async e => {
    if (e.target.classList.contains("reserve")){
      const id = e.target.getAttribute("data-id");
      try { await api(`/api/classes/${id}/reserve`, { method:"POST" }); alert("Reserved!"); }
      catch (err){ alert(err.json?.error || "Failed"); }
    }
  });
}
document.addEventListener("DOMContentLoaded", loadClasses);
