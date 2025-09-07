// login.js

document.addEventListener("DOMContentLoaded", () => {
  // Tabs toggle
  const loginTab = document.getElementById("loginTab");
  const signupTab = document.getElementById("signupTab");
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  function showLogin(){
    loginTab.classList.add("active");
    signupTab.classList.remove("active");
    loginForm.style.display = "block";
    signupForm.style.display = "none";
  }
  function showSignup(){
    signupTab.classList.add("active");
    loginTab.classList.remove("active");
    signupForm.style.display = "block";
    loginForm.style.display = "none";
  }
  if (loginTab && signupTab){
    loginTab.addEventListener('click', showLogin);
    signupTab.addEventListener('click', showSignup);
  }
  // Login logic
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;
      const err = document.getElementById('loginError');
      err.style.display = 'none';
      err.textContent = '';
      if (!email || !password){
        err.textContent = 'Email and password are required';
        err.style.display = 'block';
        return;
      }
      const btn = loginForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Signing in...'; }
      // Always login as student for this page
      try {
        const res = await api("/api/auth/login", { method: "POST", data: { username: email, password } });
        const redirect = res && res.redirect ? res.redirect : "/profiles/";
        location.href = redirect;
      } catch (e) {
        const status = e.status || 0;
        let msg = e.json?.error || 'Login failed';
        if (status === 401) msg = 'Invalid email or password';
        if (status === 403) msg = 'Your account is disabled or pending approval';
        err.textContent = msg;
        err.style.display = 'block';
      }
      finally { if (btn) { btn.disabled = false; btn.textContent = 'Get Started!'; } }
    });
  }

  // Forgot password link -> redirect
  const forgot = document.getElementById('forgotPassword');
  if (forgot) {
    forgot.addEventListener('click', (e)=>{ e.preventDefault(); location.href = '/forgot-password/'; });
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
      const err = document.getElementById('signupError');
      err.style.display = 'none';
      err.textContent = '';
      // client validation
      if (!name){ err.textContent = 'Name is required'; err.style.display='block'; return; }
      if (!surname){ err.textContent = 'Surname is required'; err.style.display='block'; return; }
      if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){ err.textContent='Valid email is required'; err.style.display='block'; return; }
      if (!password || password.length < 6){ err.textContent='Password must be at least 6 characters'; err.style.display='block'; return; }
      if (password !== confirm) {
        err.textContent = 'Passwords do not match';
        err.style.display = 'block';
        return; 
      }
      // Always register as student for this page
      const btn = signupForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Creating account...'; }
      try {
        const resp = await api("/api/auth/register", {
          method: "POST",
          data: {
            username: email,
            password,
            email,
            display_name: `${name} ${surname}`.trim(),
            first_name: name,
            last_name: surname,
            role: isTutor ? 'tutor' : 'student'
          }
        });
        // Registration now requires admin activation. Show a banner and switch to login tab.
        const notice = document.getElementById('pendingNotice');
        const text = document.getElementById('pendingNoticeText');
        if (text) {
          text.textContent = resp?.message || 'Registration successful. Your account is pending admin approval.';
        }
        if (notice) { notice.style.display = 'block'; }
        // Switch to login tab
        const loginTab = document.getElementById("loginTab");
        const signupTab = document.getElementById("signupTab");
        const loginForm = document.getElementById("loginForm");
        const signupForm = document.getElementById("signupForm");
        if (loginTab) loginTab.classList.add("active");
        if (signupTab) signupTab.classList.remove("active");
        if (loginForm) loginForm.style.display = "block";
        if (signupForm) signupForm.style.display = "none";
      } catch (e) {
        const status = e.status || 0;
        let msg = e.json?.error || 'Signup failed';
        // Prefer server message; otherwise provide a helpful default for conflicts
        if (status === 409 && !e.json?.error) msg = 'An account with this email already exists';
        err.textContent = msg;
        err.style.display = 'block';
      }
      finally { if (btn) { btn.disabled = false; btn.textContent = 'Create Account'; } }
    });
  }
});
