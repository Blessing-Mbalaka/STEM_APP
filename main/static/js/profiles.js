// profiles.js

document.addEventListener("DOMContentLoaded", async () => {
  const nameInput = document.getElementById("display_name");
  if (!nameInput) return; // run only if profile page

  const me = await api("/api/me");
  if (!me.authenticated) { location.href = "/login/"; return; }
  nameInput.value = me.display_name || me.username;

  document.getElementById("saveProfile")?.addEventListener("click", async () => {
    try {
      await api("/api/me", { method:"PATCH", data:{ display_name: nameInput.value.trim() }});
      alert("Saved");
    } catch (e){ alert(e.json?.error || "Failed to save"); }
  });
});
