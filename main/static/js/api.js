// api.js - shared helpers for all pages

function getCookie(name){
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";").map(c => c.trim());
    for (const cookie of cookies) {
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const CSRF = () => getCookie("csrftoken");

// generic fetch wrapper
async function api(path, { method="GET", data, headers={} } = {}){
  const opts = { method, headers: { "X-CSRFToken": CSRF(), ...headers } };
  if (data !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(data);
  }
  const res = await fetch(path, opts);
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(json.error || res.statusText), { status: res.status, json });
  return json;
}

// Navbar user info (optional: put <span id="whoami"></span> in your header)
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const me = await api("/api/me");
    const el = document.getElementById("whoami");
    const name = (me.display_name && me.display_name.trim()) || [me.firstName, me.lastName].filter(Boolean).join(' ') || me.username || '';
    if (el) el.textContent = me.authenticated ? `Hi, ${name}` : "Not signed in";
    const av = document.getElementById('whoami-avatar');
    if (av && me.avatar_url){ av.src = me.avatar_url; av.style.display = 'inline-block'; }
    // Unread messages badge (student header)
    try {
      const inbox = await api('/api/messages?unread=1');
      const cnt = (inbox.results||[]).length;
      const badge = document.getElementById('msg-count');
      if (badge) { badge.textContent = String(cnt); badge.style.display = cnt>0 ? 'inline-block' : 'none'; }
    } catch {}
  } catch {}
});
