// forum.js

async function loadCategories(){
  const sel = document.getElementById("category");
  if (!sel) return;
  const data = await api("/api/forum/categories");
  sel.innerHTML = data.results.map(c => `<option value="${c.slug}">${c.name}</option>`).join("");
}

async function loadThreads(){
  const cat = document.getElementById("category");
  const list = document.getElementById("thread-list");
  if (!cat || !list) return;
  const data = await api(`/api/forum/threads?category=${encodeURIComponent(cat.value)}`);
  list.innerHTML = (data.results || []).map(t => `<li data-slug="${t.slug}">${t.title}</li>`).join("");
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadCategories(); 
  await loadThreads();
  document.getElementById("category")?.addEventListener("change", loadThreads);
});
