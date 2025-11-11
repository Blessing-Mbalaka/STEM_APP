// login.js

const getCsrfToken = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || "";

const showInlineError = (target, message = "") => {
  if (!target) return;
  target.textContent = message;
  target.style.display = message ? "block" : "none";
};

const formatApiError = (error, fallbackMessage) => {
  if (!error) return fallbackMessage;
  const status = error.status || 0;
  const payload = error.json || {};

  if (!navigator.onLine || (status === 0 && error.name !== "AbortError")) {
    return "Unable to reach the server. Please check your internet connection and try again.";
  }

  if (status >= 500) {
    return "The server encountered an unexpected issue. Please try again shortly.";
  }

  let message =
    payload.error ||
    payload.detail ||
    payload.message ||
    error.message ||
    fallbackMessage;

  if (status === 409 && (!payload.error && !payload.message)) {
    message = "An account with this email already exists";
  }

  if (payload.details && typeof payload.details === "object") {
    const extras = [];
    Object.keys(payload.details).forEach((key) => {
      const value = payload.details[key];
      if (Array.isArray(value)) {
        value.forEach((item) => {
          if (item) extras.push(item);
        });
      } else if (value) {
        extras.push(value);
      }
    });
    if (extras.length) {
      message = `${message} ${extras.join(" ")}`.trim();
    }
  }

  return message || fallbackMessage;
};

const ensureApiHelper = () => {
  if (typeof window.api === "function") {
    return true;
  }
  console.error("api.js helper was not loaded before login.js");
  return false;
};

const callApi = async (path, options = {}) => {
  if (ensureApiHelper()) {
    return api(path, options);
  }
  const { method = "GET", data, headers = {}, credentials } = options;
  const init = {
    method,
    headers: { "X-CSRFToken": getCsrfToken(), ...headers },
    credentials: credentials || "include",
  };
  if (data !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(data);
  }
  const res = await fetch(path, init);
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(json.error || res.statusText), { status: res.status, json });
  return json;
};

function initLoginPage() {
  try {
  // Tabs toggle
  const loginTab = document.getElementById("loginTab");
  const signupTab = document.getElementById("signupTab");
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const pendingNotice = document.getElementById("pendingNotice");

  const setAuthView = (view) => {
    const showSignup = view === "signup";
    if (loginTab) loginTab.classList.toggle("active", !showSignup);
    if (signupTab) signupTab.classList.toggle("active", showSignup);
    if (loginForm) loginForm.style.display = showSignup ? "none" : "block";
    if (signupForm) signupForm.style.display = showSignup ? "block" : "none";
    if (pendingNotice) {
      if (showSignup) {
        pendingNotice.style.display = "none";
      } else if (pendingNotice.dataset.forceShow === "1") {
        pendingNotice.style.display = "block";
      } else {
        pendingNotice.style.display = "none";
      }
    }
  };

  function showLogin(){
    setAuthView("login");
  }
  function showSignup(){
    setAuthView("signup");
  }
  if (loginTab && signupTab){
    loginTab.addEventListener('click', (e) => { e.preventDefault(); showLogin(); });
    signupTab.addEventListener('click', (e) => { e.preventDefault(); showSignup(); });
  }
  setAuthView(signupTab && signupTab.classList.contains("active") ? "signup" : "login");
  // Login logic
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;
      const err = document.getElementById("loginError");
      showInlineError(err);
      if (!email || !password){
        showInlineError(err, 'Email and password are required');
        return;
      }
      const btn = loginForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Signing in...'; }
      // Always login as student for this page
      try {
        const res = await callApi("/api/auth/login", { method: "POST", data: { username: email, password } });
        const redirect = res && res.redirect ? res.redirect : "/index/";
        location.href = redirect;
      } catch (e) {
        const status = e.status || 0;
        let msg = formatApiError(e, 'Login failed');
        if (status === 401) msg = 'Invalid email or password';
        if (status === 403) {
          const payload = e && e.json ? e.json : {};
          if (payload.redirect) {
            location.href = payload.redirect;
            return;
          }
          msg = 'Your account is disabled or pending approval';
        }
        showInlineError(err, msg);
      }
      finally { if (btn) { btn.disabled = false; btn.textContent = 'Get Started!'; } }
    });
  }

  // Forgot password link -> redirect
  const forgot = document.getElementById('forgotPassword');
  if (forgot) {
    forgot.addEventListener('click', (e)=>{ e.preventDefault(); location.href = '/forgot-password/'; });
  }

  const signupStudent = document.getElementById("signupChildRole");
  const signupTutor = document.getElementById("signupParentRole");
  const tutorExtras = document.getElementById("tutorExtras");
  const idDocumentEl = document.getElementById("tutorIdDocument");
  const qualificationDocumentsEl = document.getElementById("tutorQualificationDocuments");
  const supportingDocumentsEl = document.getElementById("tutorSupportingDocuments");
  const saceDocumentsEl = document.getElementById("tutorSaceDocuments");

  function setSignupRole(isTutor) {
    if (!signupStudent || !signupTutor) return;
    const form = document.getElementById("signupForm");
    if (isTutor) {
      signupTutor.classList.add("active");
      signupStudent.classList.remove("active");
      if (tutorExtras) tutorExtras.style.display = "block";
    } else {
      signupStudent.classList.add("active");
      signupTutor.classList.remove("active");
      if (tutorExtras) tutorExtras.style.display = "none";
    }
    if (form) {
      form.classList.toggle("tutor-mode", Boolean(isTutor));
    }
  }

  if (signupStudent && signupTutor) {
    signupStudent.addEventListener("click", (event) => {
      event.preventDefault();
      setSignupRole(false);
    });
    signupTutor.addEventListener("click", (event) => {
      event.preventDefault();
      setSignupRole(true);
    });
    setSignupRole(signupTutor.classList.contains("active"));
  }

  // Signup logic
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("signupName").value.trim();
      const surname = document.getElementById("signupSurname").value.trim();
      const email = document.getElementById("signupEmail").value.trim();
      const password = document.getElementById("signupPassword").value;
      const confirm = document.getElementById("confirmPassword").value;
      // role from toggle (purely cosmetic until backend reads it)
      const tutorToggle = document.getElementById('signupParentRole');
      const isTutor = tutorToggle && tutorToggle.classList.contains('active');
      const motivationEl = document.getElementById("tutorMotivation");
      const err = document.getElementById('signupError');
      showInlineError(err);
      // client validation
      if (!name){ showInlineError(err, 'Name is required'); return; }
      if (!surname){ showInlineError(err, 'Surname is required'); return; }
      if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){ showInlineError(err, 'Valid email is required'); return; }
      if (!password || password.length < 6){ showInlineError(err, 'Password must be at least 6 characters'); return; }
      if (password !== confirm) {
        showInlineError(err, 'Passwords do not match');
        return; 
      }
      if (isTutor) {
        const idFile = idDocumentEl && idDocumentEl.files ? idDocumentEl.files[0] : null;
        const qualificationFiles = qualificationDocumentsEl && qualificationDocumentsEl.files
          ? Array.from(qualificationDocumentsEl.files)
          : [];
        if (!idFile) {
          showInlineError(err, 'An identity document is required for aspiring tutors.');
          return;
        }
        if (!qualificationFiles.length) {
          showInlineError(err, 'Please upload at least one qualification document.');
          return;
        }
      }

      const btn = signupForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Creating account...'; }
      try {
        let resp;
        if (isTutor) {
          const fd = new FormData();
          fd.append("username", email);
          fd.append("password", password);
          fd.append("email", email);
          fd.append("display_name", `${name} ${surname}`.trim());
          fd.append("first_name", name);
          fd.append("last_name", surname);
          fd.append("role", "tutor");
          fd.append("motivation", motivationEl ? motivationEl.value.trim() : "");
          if (idDocumentEl && idDocumentEl.files.length) {
            fd.append("id_document", idDocumentEl.files[0]);
          }
          const qualificationFiles = qualificationDocumentsEl ? Array.from(qualificationDocumentsEl.files || []) : [];
          qualificationFiles.forEach((file) => fd.append("qualification_documents", file));
          const supportingFiles = supportingDocumentsEl ? Array.from(supportingDocumentsEl.files || []) : [];
          supportingFiles.forEach((file) => fd.append("supporting_documents", file));
          const saceFiles = saceDocumentsEl ? Array.from(saceDocumentsEl.files || []) : [];
          saceFiles.forEach((file) => fd.append("sace_documents", file));

          const res = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
            credentials: "same-origin",
            body: fd,
          });
          const json = await res.json().catch(() => ({}));
          if (!res.ok) throw { status: res.status, json };
          resp = json;
        } else {
          resp = await callApi("/api/auth/register", {
            method: "POST",
            data: {
              username: email,
              password,
              email,
              display_name: `${name} ${surname}`.trim(),
              first_name: name,
              last_name: surname,
              role: 'student'
            }
          });
        }

        if (resp && resp.redirect) {
          location.href = resp.redirect;
          return;
        }

        const notice = document.getElementById('pendingNotice');
        const text = document.getElementById('pendingNoticeText');
        if (text) {
          const message = resp && resp.message ? resp.message : 'Registration successful. Your account is pending admin approval.';
          text.textContent = message;
        }
        if (notice) {
          notice.style.display = 'block';
          notice.dataset.forceShow = "1";
        }
        if (loginTab) loginTab.classList.add("active");
        if (signupTab) signupTab.classList.remove("active");
        if (loginForm) loginForm.style.display = "block";
        if (signupForm) signupForm.style.display = "none";
      } catch (e) {
        const msg = formatApiError(e, 'Signup failed');
        showInlineError(err, msg);
      }
      finally { if (btn) { btn.disabled = false; btn.textContent = 'Create Account'; } }
    });
  }
  window.__stemLoginReady = true;
  } catch (err) {
    console.error("Failed to initialize login page script", err);
    const fallbackError = document.getElementById("loginError") || document.getElementById("signupError");
    showInlineError(fallbackError, "Something unexpected happened while loading the page. Please refresh and try again.");
    window.__stemLoginReady = false;
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLoginPage);
} else {
  initLoginPage();
}
