/* -------- Mostrar/Ocultar contraseña -------- */
document.addEventListener("DOMContentLoaded", () => {
  const pwd = document.getElementById("password");
  const btn = document.querySelector(".toggle-password");

  if (pwd && btn) {
    const icon = btn.querySelector("i");

    btn.addEventListener("click", () => {
      const oculto = pwd.type === "password";
      pwd.type = oculto ? "text" : "password";

      icon.classList.toggle("fa-eye");
      icon.classList.toggle("fa-eye-slash");

      btn.setAttribute(
        "aria-label",
        oculto ? "Ocultar contraseña" : "Mostrar contraseña"
      );
    });
  }
});

/* -------- envío del formulario de login con JWT -------- */
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const errorBox = document.getElementById("login-error");

  if (!username || !password) {
    errorBox.textContent = "⚠️ Por favor, completa todos los campos.";
    return;
  }

  try {
    // 🔐 JWT: Usa fetch normal para login (endpoint público)
    const res = await fetch("/api/auth/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (res.ok) {
      // Guardar tokens JWT en localStorage
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Guardar clienteId si existe
      if (data.user.cliente_id) {
        localStorage.setItem("clienteId", data.user.cliente_id);
      }

      // Redirigir al inicio
      window.location.href = "/";
    } else {
      errorBox.textContent = `❌ ${data.error || "Credenciales inválidas"}`;
    }
  } catch (err) {
    errorBox.textContent = `❌ Error inesperado: ${err.message}`;
  }
});
