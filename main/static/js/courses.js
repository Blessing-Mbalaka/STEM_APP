(() => {
  "use strict";

  // --------- Helpers ----------
  function getCookie(name) {
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

  function showBanner(msg) {
    let el = document.getElementById("courses-error-banner");
    if (!el) {
      el = document.createElement("div");
      el.id = "courses-error-banner";
      el.style.cssText = "margin:16px auto;max-width:900px;padding:12px 16px;border-radius:10px;background:#fff3cd;color:#856404;border:1px solid #ffeeba;box-shadow:0 2px 6px rgba(0,0,0,.05);";
      const container = document.querySelector(".container") || document.body;
      container.insertBefore(el, container.firstChild.nextSibling);
    }
    el.textContent = msg;
  }

  function showEmptyState() {
    const grid = document.getElementById("course-selection");
    if (!grid) return;
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:24px;">
        <h3>No courses available yet</h3>
        <p style="opacity:.8">Once courses are added in the backend, they'll appear here automatically.</p>
      </div>
    `;
  }

  const api = async (path, { method = "GET", data } = {}) => {
    const csrftoken = getCookie("csrftoken");
    const opts = { method, headers: {} };
    if (csrftoken) opts.headers["X-CSRFToken"] = csrftoken;
    if (data !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(data);
    }
    const res = await fetch(path, opts);

    // Ensure JSON (login pages often return HTML with 200 OK)
    const ct = (res.headers.get("content-type") || "").toLowerCase();
    const isJSON = ct.includes("application/json") || ct.includes("json");
    const bodyText = isJSON ? null : await res.text().catch(() => "");

    if (!isJSON) {
      const snippet = bodyText ? bodyText.slice(0, 120).replace(/\s+/g, " ") : "";
      const hint = snippet.includes("<form") || snippet.toLowerCase().includes("login") ? " (looks like a login page?)" : "";
      const msg = `Expected JSON from ${path} but got "${ct || "unknown"}"${hint}.`;
      throw new Error(msg);
    }

    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(json?.error || res.statusText);
    }
    return json;
  };

  // --------- Data + rendering ----------
  let subjects = {}; // { key: { name, visual[], auditory[], readwrite[] } }
  let currentSubject = "";

  function inferCategory(key) {
    const k = (key || "").toLowerCase();
    if (k.includes("stem")) return "stem";
    if (k.includes("steam")) return "steam";
    return "general";
  }

  async function hydrateFromAPI() {
    // IMPORTANT: trailing slash
    const data = await api("/api/courses/");

    // Preferred shape
    if (data?.subjects && typeof data.subjects === "object" && Object.keys(data.subjects).length > 0) {
      subjects = {};
      for (const [key, incoming] of Object.entries(data.subjects)) {
        subjects[key] = {
          name: incoming?.name || key,
          visual: Array.isArray(incoming?.visual) ? incoming.visual : [],
          auditory: Array.isArray(incoming?.auditory) ? incoming.auditory : [],
          readwrite: Array.isArray(incoming?.readwrite) ? incoming.readwrite : []
        };
      }
      console.debug("[courses] Loaded subjects:", subjects);
      return;
    }

    // Fallback: results[] → derive subjects (still real data)
    if (Array.isArray(data?.results) && data.results.length > 0) {
      const obj = {};
      for (const r of data.results) {
        const key = ((r.subject || r.title || "general") + "").toLowerCase();
        if (!obj[key]) obj[key] = { name: r.title || key, visual: [], auditory: [], readwrite: [] };
      }
      subjects = obj;
      console.debug("[courses] Derived subjects from results:", subjects);
      return;
    }

    subjects = {};
    console.debug("[courses] API returned no subjects or results.");
  }

  function renderCourseGrid() {
    const courseGrid = document.getElementById("course-selection");
    if (!courseGrid) return;

    courseGrid.innerHTML = "";

    for (const [key, subject] of Object.entries(subjects)) {
      const category = inferCategory(key);
      const iconClass = category === "stem" ? "fa-square-root-alt"
                       : category === "steam" ? "fa-palette"
                       : "fa-book-open";
      const firstVisual = (subject.visual && subject.visual[0]) || {};
      const duration = firstVisual.duration || "";
      const level = firstVisual.level || "";

      courseGrid.insertAdjacentHTML("beforeend", `
        <div class="course-card ${category}" data-category="${category}">
          <div class="course-category ${category}">
            ${category.charAt(0).toUpperCase() + category.slice(1)}
          </div>
          <div class="course-icon ${category}">
            <i class="fas ${iconClass}"></i>
          </div>
          <h3 class="course-name">${subject.name}</h3>
          <p class="course-desc">${firstVisual.title ? String(firstVisual.title) : ""}</p>
          <div class="course-details">
            <div class="course-duration"><i class="far fa-clock"></i> ${duration}</div>
            <div class="course-level">${level}</div>
          </div>
          <button class="start-button" data-subject="${key}">Start Learning</button>
        </div>
      `);
    }

    // Start Learning
    courseGrid.addEventListener("click", e => {
      const btn = e.target.closest(".start-button");
      if (!btn) return;
      selectSubject(btn.dataset.subject);
    });

    // Filters
    const filters = document.querySelectorAll(".category-filter");
    filters.forEach(filter => {
      filter.addEventListener("click", function () {
        filters.forEach(f => f.classList.remove("active"));
        this.classList.add("active");
        filterCourses(this.getAttribute("data-category"));
      });
    });
  }

  function filterCourses(category) {
    const cards = document.querySelectorAll(".course-card");
    cards.forEach(card => {
      card.style.display = (category === "all" || card.getAttribute("data-category") === category) ? "flex" : "none";
    });
  }

  function selectSubject(subjectId) {
    currentSubject = subjectId;
    const sel = document.getElementById("course-selection");
    const pane = document.getElementById("learning-styles");
    const title = document.getElementById("selected-subject-title");

    if (sel) sel.style.display = "none";
    if (pane) pane.style.display = "block";
    if (title) title.textContent = `${subjects[subjectId]?.name || subjectId} Resources`;

    renderResources(subjectId);
  }

  function goBackToCourses() {
    const sel = document.getElementById("course-selection");
    const pane = document.getElementById("learning-styles");
    if (sel) sel.style.display = "grid";
    if (pane) pane.style.display = "none";
  }

  function showLearningStyle(a, b) {
    let styleId, evt;
    if (typeof a === "string") { styleId = a; evt = null; }
    else { evt = a; styleId = b; }

    document.querySelectorAll(".style-content").forEach(c => c.classList.remove("active"));
    document.querySelectorAll(".style-tab").forEach(t => t.classList.remove("active"));
    const target = document.getElementById(`${styleId}-content`);
    if (target) target.classList.add("active");
    if (evt?.currentTarget) evt.currentTarget.classList.add("active");
  }

  function renderResources(subjectId) {
    const subject = subjects[subjectId];
    if (!subject) return;

    // Visual
    const videoGrid = document.querySelector("#visual-content .video-grid");
    if (videoGrid) {
      videoGrid.innerHTML = "";
      (subject.visual || []).forEach(v => {
        const href = v.url || v.file || "#";
        videoGrid.insertAdjacentHTML("beforeend", `
          <div class="video-card">
            <a class="video-thumbnail" href="${href}" target="_blank" rel="noopener">
              <i class="fas fa-play"></i>
            </a>
            <div class="video-info">
              <div class="video-title">${v.title || ""}</div>
              <div class="video-duration">${v.duration || ""}</div>
            </div>
          </div>
        `);
      });
    }

    // Auditory
    const audioGrid = document.querySelector("#auditory-content .audio-grid");
    if (audioGrid) {
      audioGrid.innerHTML = "";
      (subject.auditory || []).forEach(a => {
        const href = a.url || a.file || "#";
        audioGrid.insertAdjacentHTML("beforeend", `
          <div class="audio-card">
            <a class="audio-icon" href="${href}" target="_blank" rel="noopener">
              <i class="fas fa-headphones"></i>
            </a>
            <div class="audio-info">
              <div class="audio-title">${a.title || ""}</div>
              <div class="audio-duration">${a.duration || ""}</div>
            </div>
          </div>
        `);
      });
    }

    // Read/Write
    const materialGrid = document.querySelector("#readwrite-content .material-grid");
    if (materialGrid) {
      materialGrid.innerHTML = "";
      (subject.readwrite || []).forEach(m => {
        const href = m.url || m.file || "#";
        materialGrid.insertAdjacentHTML("beforeend", `
          <div class="material-card">
            <a class="material-cover" href="${href}" target="_blank" rel="noopener">
              <i class="fas fa-book"></i>
            </a>
            <div class="material-info">
              <div class="material-title">${m.title || ""}</div>
              <div class="material-author">${m.author || ""}</div>
              <div class="material-pages">${m.pages || ""}</div>
            </div>
          </div>
        `);
      });
    }
  }

  // --------- Boot ---------
  document.addEventListener("DOMContentLoaded", async () => {
    if (!document.getElementById("course-selection")) return;

    try {
      await hydrateFromAPI();
      if (Object.keys(subjects).length === 0) {
        showEmptyState();
      } else {
        renderCourseGrid();
      }

      // expose for inline handlers
      window.selectSubject = selectSubject;
      window.showLearningStyle = showLearningStyle;
      window.goBackToCourses = goBackToCourses;

    } catch (err) {
      console.error("[courses] API error:", err);
      showBanner(err.message);
      showEmptyState();
    }
  });
})();
