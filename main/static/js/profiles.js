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



  // --- Precise Addition: Translation Button Logic ---
  const translateToEnglish = document.getElementById("translateToEnglish");
  const translateToZulu = document.getElementById("translateToZulu");

  if (translateToEnglish) {
    translateToEnglish.addEventListener("click", () => {
      if (typeof window.applyTranslations === "function") {
        window.applyTranslations("en"); // Trigger translation to English
        setActiveLanguageButton("en");
      }
    });
  }

  if (translateToZulu) {
    translateToZulu.addEventListener("click", () => {
      if (typeof window.applyTranslations === "function") {
        window.applyTranslations("zu"); // Trigger translation to Zulu
        setActiveLanguageButton("zu");
      }
    });
  }

  // Helper function to set the active button
  function setActiveLanguageButton(lang) {
    const buttons = document.querySelectorAll(".language-toggle-btn");
    buttons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });
  }
  // ---

  document.addEventListener("DOMContentLoaded", () => {
  console.log("profiles.js loaded");
  setupEventListeners();
  loadProfile();
});