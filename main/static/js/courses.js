// courses.js

async function loadCourses(){
  const list = document.getElementById("course-list");
  if (!list) return;

  const data = await api("/api/courses");
  list.innerHTML = "";
  (data.results || []).forEach(c => {
    const row = document.createElement("div");
    row.innerHTML = `
      <h4>${c.title}</h4>
      <p>${c.summary || ""}</p>
      <button data-slug="${c.slug}" class="btn-enroll">Enroll</button>
    `;
    list.appendChild(row);
  });

  list.addEventListener("click", async e => {
    if (e.target.classList.contains("btn-enroll")){
      const slug = e.target.getAttribute("data-slug");
      try { await api(`/api/courses/${slug}/enroll`, { method:"POST" }); alert("Enrolled!"); }
      catch (err){ alert(err.json?.error || "Failed to enroll"); }
    }
  });
}
document.addEventListener("DOMContentLoaded", loadCourses);
