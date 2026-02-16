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
    // 🔐 JWT: Login de cliente
    const res = await fetch("/auth/login_client/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (res.ok) {
      // Guardar tokens JWT en localStorage (estandarizado)
      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);
      
      // Guardar user_id y username si existen
      if (data.user_id) {
        localStorage.setItem("user_id", data.user_id);
      }
      if (data.username) {
        localStorage.setItem("username", data.username);
      }
      if (data.nombre) {
        localStorage.setItem("nombre", data.nombre);
      }
      if (data.correo) {
        localStorage.setItem("correo", data.correo);
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
