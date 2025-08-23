// login.js

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btnLogin");
  if (!btn) return; // run only if login page

  btn.addEventListener("click", async () => {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    try {
      await api("/api/auth/login", { method:"POST", data:{ username, password } });
      location.href = "/profiles/";
    } catch(e){
      alert(e.json?.error || "Login failed");
    }
  });
});
