/* static/js/courses.js — API-only renderer with inline Video, Audio, EPUB & PDF */
(() => {
  "use strict";

  /* =============== Utilities =============== */

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
      el.style.cssText =
        "margin:16px auto;max-width:900px;padding:12px 16px;border-radius:10px;background:#fff3cd;color:#856404;border:1px solid #ffeeba;box-shadow:0 2px 6px rgba(0,0,0,.05);";
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

    const ct = (res.headers.get("content-type") || "").toLowerCase();
    const isJSON = ct.includes("application/json") || ct.includes("json");
    if (!isJSON) {
      const text = await res.text().catch(() => "");
      const looksLikeLogin =
        text.toLowerCase().includes("login") || text.toLowerCase().includes("<form");
      throw new Error(
        `Expected JSON from ${path} but got "${ct || "unknown"}"${
          looksLikeLogin ? " (this looks like a login page)" : ""
        }.`
      );
    }

    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(json?.error || res.statusText);
    return json;
  };

  /* =============== State =============== */

  let subjects = {};   // { key: { name, visual[], auditory[], readwrite[] } }
  let currentSubject = "";
  const hasSubjects = () => Object.keys(subjects).length > 0;

  function inferCategory(key) {
    const k = (key || "").toLowerCase();
    if (k.includes("stem")) return "stem";
    if (k.includes("steam")) return "steam";
    return "general";
  }

  /* =============== Type detection & thumbs =============== */

  function extractYouTubeId(u) {
    try {
      const url = new URL(u);
      if (url.hostname.includes("youtu.be")) return url.pathname.slice(1);
      if (url.hostname.includes("youtube.com")) {
        const v = url.searchParams.get("v");
        if (v) return v;
        const parts = url.pathname.split("/");
        const i = parts.findIndex(p => p === "embed" || p === "shorts");
        if (i !== -1 && parts[i + 1]) return parts[i + 1];
      }
    } catch { /* ignore */ }
    return null;
  }

  function isVideoFile(u) { return /\.((mp4)|(webm)|(ogg))(\?.*)?$/i.test(u || ""); }
  function isAudioFile(u) { return /\.(mp3|m4a|aac|ogg|wav)(\?.*)?$/i.test(u || ""); }
  function isEpub(u)     { return /\.epub(\?.*)?$/i.test(u || ""); }
  function isPdf(u)      { return /\.pdf(\?.*)?$/i.test(u || ""); }

  function videoThumbnailFor(res) {
    if (res.thumbnail) return res.thumbnail;
    const url = res.url || "";
    const isYT = /(?:youtube\.com|youtu\.be)/i.test(url);
    if (res.resource_type === "youtube" || isYT) {
      const id = extractYouTubeId(url);
      if (id) return `https://img.youtube.com/vi/${id}/hqdefault.jpg`;
    }
    return null;
  }

  function buildYouTubeEmbedSrc(url) {
    const id = extractYouTubeId(url);
    if (!id) return null;
    return `https://www.youtube-nocookie.com/embed/${id}?rel=0&modestbranding=1`;
  }

  /* =============== Inline players (video) =============== */

  function mountInlinePlayer(container) {
    if (!container || container.dataset.mounted === "1") return;

    const kind = container.dataset.kind;               // 'youtube' | 'file'
    const src  = container.dataset.src || "";
    const poster = container.dataset.poster || "";

    if (kind === "youtube" && src) {
      container.innerHTML = `
        <iframe
          src="${src}&autoplay=1"
          title="YouTube video"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen
          style="width:100%;height:150px;display:block;border:0;border-radius:8px"
        ></iframe>`;
    } else if (kind === "file" && src) {
      container.innerHTML = `
        <video
          src="${src}"
          ${poster ? `poster="${poster}"` : ""}
          controls autoplay playsinline
          style="width:100%;height:150px;display:block;object-fit:cover;border-radius:8px"
        ></video>`;
    }
    container.dataset.mounted = "1";
  }

  /* =============== EPUB Reader (overlay) =============== */

  let epubLoaded = false;
  let currentBook = null;
  let currentRendition = null;
  let currentFont = 100;

  function loadEpubJs() {
    if (epubLoaded || window.ePub) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "https://unpkg.com/epubjs/dist/epub.min.js";
      s.async = true;
      s.onload = () => { epubLoaded = true; resolve(); };
      s.onerror = () => reject(new Error("Failed to load epub.js"));
      document.head.appendChild(s);
    });
  }

  function ensureEpubOverlay() {
    if (document.getElementById("epub-overlay")) return;

    const overlay = document.createElement("div");
    overlay.id = "epub-overlay";
    overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;display:none;align-items:center;justify-content:center;";
    overlay.innerHTML = `
      <div id="epub-modal" style="background:#fff;width:92%;max-width:980px;height:80vh;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.2);display:flex;flex-direction:column;overflow:hidden;">
        <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #eee">
          <button id="epub-close" aria-label="Close" style="margin-right:auto;padding:6px 10px;border:0;border-radius:8px;background:#eee;cursor:pointer">Close</button>
          <button id="epub-prev"  style="padding:6px 10px;border:0;border-radius:8px;background:#eee;cursor:pointer">&larr; Prev</button>
          <button id="epub-next"  style="padding:6px 10px;border:0;border-radius:8px;background:#eee;cursor:pointer">Next &rarr;</button>
          <div style="margin-left:12px;display:flex;align-items:center;gap:6px">
            <button id="epub-smaller" style="padding:6px 10px;border:0;border-radius:8px;background:#eee;cursor:pointer">A-</button>
            <button id="epub-bigger"  style="padding:6px 10px;border:0;border-radius:8px;background:#eee;cursor:pointer">A+</button>
          </div>
        </div>
        <div id="epub-view" style="flex:1;min-height:0;background:#fafafa"></div>
      </div>`;
    document.body.appendChild(overlay);

    overlay.addEventListener("click", (e) => {
      if (e.target.id === "epub-overlay") closeEpub();
    });
    document.getElementById("epub-close").addEventListener("click", closeEpub);
    document.getElementById("epub-prev").addEventListener("click", () => currentRendition && currentRendition.prev());
    document.getElementById("epub-next").addEventListener("click", () => currentRendition && currentRendition.next());
    document.getElementById("epub-smaller").addEventListener("click", () => setEpubFont(currentFont - 10));
    document.getElementById("epub-bigger").addEventListener("click",  () => setEpubFont(currentFont + 10));
  }

  function setEpubFont(size) {
    currentFont = Math.max(60, Math.min(180, size));
    if (currentRendition) currentRendition.themes.fontSize(currentFont + "%");
  }

  async function openEpub(url) {
    try {
      ensureEpubOverlay();
      await loadEpubJs();
      if (!window.ePub) throw new Error("epub.js is not available");

      if (currentRendition && currentRendition.destroy) currentRendition.destroy();
      currentBook = window.ePub(url);
      currentRendition = currentBook.renderTo("epub-view", {
        width: "100%",
        height: "100%",
        flow: "paginated"
      });
      currentRendition.display();
      setEpubFont(currentFont);

      document.getElementById("epub-overlay").style.display = "flex";
    } catch (err) {
      console.error("EPUB open failed:", err);
      showBanner("Couldn't open EPUB. If it's hosted on another domain, enable CORS for it.");
      window.open(url, "_blank", "noopener,noreferrer");
    }
  }

  function closeEpub() {
    const overlay = document.getElementById("epub-overlay");
    if (overlay) overlay.style.display = "none";
    if (currentRendition && currentRendition.destroy) currentRendition.destroy();
    currentBook = null;
    currentRendition = null;
  }

  /* =============== PDF Viewer (overlay) =============== */

  function ensurePdfOverlay() {
    if (document.getElementById("pdf-overlay")) return;

    const overlay = document.createElement("div");
    overlay.id = "pdf-overlay";
    overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;display:none;align-items:center;justify-content:center;";
    overlay.innerHTML = `
      <div id="pdf-modal" style="background:#fff;width:92%;max-width:1100px;height:85vh;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.2);display:flex;flex-direction:column;overflow:hidden;">
        <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #eee">
          <button id="pdf-close" aria-label="Close" style="margin-right:auto;padding:6px 10px;border:0;border-radius:8px;background:#eee;cursor:pointer">Close</button>
          <a id="pdf-open-tab" href="#" target="_blank" rel="noopener" style="padding:6px 10px;border:0;border-radius:8px;background:#eee;text-decoration:none;color:#333;cursor:pointer">Open in new tab</a>
        </div>
        <div style="flex:1;min-height:0;background:#fafafa">
          <!-- Let the browser's built-in PDF viewer handle controls -->
          <iframe id="pdf-frame" src="about:blank" title="PDF" style="border:0;width:100%;height:100%"></iframe>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    overlay.addEventListener("click", (e) => {
      if (e.target.id === "pdf-overlay") closePdf();
    });
    document.getElementById("pdf-close").addEventListener("click", closePdf);
  }

  function openPdf(url) {
  ensurePdfOverlay();
  const origin = window.location.origin.replace(/\/$/, "");
  const mediaPrefixAbs = origin + "/media/";
  let src = url;

  // If it's a local media file, use the embed-safe endpoint
  if (url.startsWith(mediaPrefixAbs)) {
    const rel = url.slice(mediaPrefixAbs.length);        // course_resources/xyz.pdf
    src = origin + "/media-pdf/" + rel;                  // our exempt route
  } else if (url.startsWith("/media/")) {                // relative form
    src = origin + "/media-pdf/" + url.slice("/media/".length);
  }

  document.getElementById("pdf-frame").src = src + "#view=FitH";
  document.getElementById("pdf-open-tab").href = url;    // keep “Open in new tab” to the real URL
  document.getElementById("pdf-overlay").style.display = "flex";
}


  function closePdf() {
    const overlay = document.getElementById("pdf-overlay");
    if (overlay) overlay.style.display = "none";
    const frame = document.getElementById("pdf-frame");
    if (frame) frame.src = "about:blank";
  }

  /* =============== API -> State =============== */

  async function hydrateFromAPI() {
    const data = await api("/api/courses/"); // trailing slash required

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
      return;
    }

    if (Array.isArray(data?.results) && data.results.length > 0) {
      const obj = {};
      for (const r of data.results) {
        const key = ((r.subject || r.title || "general") + "").toLowerCase();
        if (!obj[key]) obj[key] = { name: r.title || key, visual: [], auditory: [], readwrite: [] };
      }
      subjects = obj;
      return;
    }

    subjects = {};
  }

  /* =============== Grid & Filters =============== */

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

    courseGrid.addEventListener("click", (e) => {
      const btn = e.target.closest(".start-button");
      if (!btn) return;
      selectSubject(btn.dataset.subject);
    });

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
    document.querySelectorAll(".course-card").forEach(card => {
      card.style.display = (category === "all" || card.getAttribute("data-category") === category) ? "flex" : "none";
    });
  }

  /* =============== Subject Flow =============== */

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

  /* =============== Resources (Video + Audio + EPUB + PDF) =============== */

  function renderResources(subjectId) {
    const subject = subjects[subjectId];
    if (!subject) return;

    // VISUAL (videos)
    const videoGrid = document.querySelector("#visual-content .video-grid");
    if (videoGrid) {
      videoGrid.innerHTML = "";
      (subject.visual || []).forEach(v => {
        const href = v.url || v.file || "#";
        const thumb = videoThumbnailFor(v);

        let kind = "file";
        let embedSrc = "";
        if (v.resource_type === "youtube" || /(?:youtube\.com|youtu\.be)/i.test(v.url || "")) {
          kind = "youtube";
          embedSrc = buildYouTubeEmbedSrc(v.url || "") || "";
        } else if (isVideoFile(v.file || v.url)) {
          kind = "file";
          embedSrc = href;
        }

        videoGrid.insertAdjacentHTML("beforeend", `
          <div class="video-card">
            <div class="video-embed" data-kind="${kind}" data-src="${embedSrc}" data-poster="${thumb || ""}" style="position:relative;">
              <div class="video-thumbnail js-play-video" role="button" tabindex="0" aria-label="Play video"
                   style="cursor:pointer; ${thumb ? "background:none;padding:0" : ""}">
                ${ thumb
                    ? `<img src="${thumb}" alt="Video thumbnail"
                           style="display:block;width:100%;height:150px;object-fit:cover;border:0;border-radius:8px"/>`
                    : `<i class="fas fa-play"></i>` }
                <div class="play-overlay" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
                  <span style="display:inline-flex;width:56px;height:56px;border-radius:50%;background:rgba(0,0,0,.5);">
                    <svg viewBox="0 0 24 24" width="56" height="56" aria-hidden="true" focusable="false" style="margin:auto;fill:#fff">
                      <path d="M8 5v14l11-7z"></path>
                    </svg>
                  </span>
                </div>
              </div>
            </div>
            <div class="video-info">
              <div class="video-title">${v.title || ""}</div>
              <div class="video-duration">${v.duration || ""}</div>
            </div>
          </div>
        `);
      });
    }

    // AUDITORY (audio)
    const audioGrid = document.querySelector("#auditory-content .audio-grid");
    if (audioGrid) {
      audioGrid.innerHTML = "";
      (subject.auditory || []).forEach(a => {
        const href = a.url || a.file || "#";
        if (isAudioFile(href)) {
          audioGrid.insertAdjacentHTML("beforeend", `
            <div class="audio-card">
              <div class="audio-icon" style="background:#ffe08a">
                <i class="fas fa-headphones"></i>
              </div>
              <div class="audio-info" style="flex:1">
                <div class="audio-title">${a.title || ""}</div>
                <div class="audio-duration">${a.duration || ""}</div>
                <audio controls preload="none" style="width:100%;margin-top:8px">
                  <source src="${href}">
                  Your browser does not support the audio element.
                </audio>
              </div>
            </div>
          `);
        } else {
          // external platform (spotify/podcast page etc.)
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
        }
      });
    }

    // READ/WRITE (EPUB + PDF + others)
    const materialGrid = document.querySelector("#readwrite-content .material-grid");
    if (materialGrid) {
      materialGrid.innerHTML = "";
      (subject.readwrite || []).forEach(m => {
        const href = m.url || m.file || "#";
        const isBook = isEpub(href);
        const isPdfDoc = isPdf(href);
        materialGrid.insertAdjacentHTML("beforeend", `
          <div class="material-card">
            <a class="material-cover ${isBook ? "js-open-epub" : isPdfDoc ? "js-open-pdf" : ""}"
               href="${href}" ${(!isBook && !isPdfDoc) ? 'target="_blank" rel="noopener"' : ""}>
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

  // Delegated events
  function handlePlayClick(e) {
    const play = e.target.closest(".js-play-video");
    if (!play) return;
    const container = play.closest(".video-embed");
    mountInlinePlayer(container);
  }

  function handlePlayKeydown(e) {
    const play = e.target.closest(".js-play-video");
    if (!play) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      const container = play.closest(".video-embed");
      mountInlinePlayer(container);
    }
  }

  function handleEpubClick(e) {
    const a = e.target.closest("a.js-open-epub");
    if (!a) return;
    const href = a.getAttribute("href");
    if (!href) return;
    e.preventDefault();
    openEpub(href);
  }

  function handlePdfClick(e) {
    const a = e.target.closest("a.js-open-pdf");
    if (!a) return;
    const href = a.getAttribute("href");
    if (!href) return;
    e.preventDefault();
    openPdf(href);
  }

  /* =============== Boot =============== */

  document.addEventListener("DOMContentLoaded", async () => {
    if (!document.getElementById("course-selection")) return;

    try {
      await hydrateFromAPI();
      if (!hasSubjects()) {
        showEmptyState();
      } else {
        renderCourseGrid();
      }

      // expose for inline handlers in template
      window.selectSubject = selectSubject;
      window.showLearningStyle = showLearningStyle;
      window.goBackToCourses = goBackToCourses;
      window.api = api;

      // global listeners
      document.addEventListener("click", handlePlayClick);
      document.addEventListener("keydown", handlePlayKeydown);
      document.addEventListener("click", handleEpubClick);
      document.addEventListener("click", handlePdfClick);
    } catch (err) {
      console.error("[courses] API error:", err);
      showBanner(err.message);
      showEmptyState();
    }
  });
})();
