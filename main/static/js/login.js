// login.js

document.addEventListener("DOMContentLoaded", () => {
  // Login logic
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;
      // Always login as student for this page
      try {
        await api("/api/login", { method: "POST", data: { username: email, password } });
        location.href = "/profiles/";
      } catch (e) {
        alert(e.json?.error || "Login failed");
      }
    });
  }

  // Signup logic
  const signupForm = document.getElementById("signupForm");
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("signupName").value.trim();
      const email = document.getElementById("signupEmail").value.trim();
      const password = document.getElementById("signupPassword").value;
      const confirm = document.getElementById("confirmPassword").value;
      if (password !== confirm) {
        alert("Passwords do not match");
        return;
      }
      // Always register as student for this page
      try {
        await api("/api/register", {
          method: "POST",
          data: {
            username: email,
            password,
            email,
            display_name: name
          }
        });
        location.href = "/profiles/";
      } catch (e) {
        alert(e.json?.error || "Signup failed");
      }
    });
  }
});
