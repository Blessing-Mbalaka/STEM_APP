// classes.js

async function loadClasses(){
  const container = document.getElementById("classes-list");
  if (!container) return;

  const data = await api("/api/classes");
  container.innerHTML = "";
  (data.results || []).forEach(s => {
    const d = document.createElement("div");
    const start = new Date(s.starts_at).toLocaleString();
    const end = new Date(s.ends_at).toLocaleString();
    const link = s.location ? `<a href="${s.location}" target="_blank">Join</a>` : '';
    d.innerHTML = `
      <strong>${s.title}</strong> <span style="color:#666;">${s.course ? '• '+s.course : ''}</span><br/>
      <span style="color:#666;">${start} — ${end}</span><br/>
      ${link} <button class="reserve" data-id="${s.id}">Reserve</button>
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

