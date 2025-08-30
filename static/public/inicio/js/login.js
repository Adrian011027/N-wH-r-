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

/* -------- Utilidad para decodificar JWT sin librerías externas -------- */
function decodeJWT(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch (e) {
    console.error("Error al decodificar JWT:", e);
    return {};
  }
}

/* -------- envío del formulario de login (JWT) -------- */
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const errorBox = document.getElementById("login-error");

  if (!username || !password) {
    errorBox.textContent = "⚠️ Por favor, completa todos los campos.";
    return;
  }

  try {
    const res = await fetch("/auth/login_client/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      // 🔑 Guardamos tokens en localStorage
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);

      // ✅ Decodificamos el access token para extraer datos del usuario
      const decoded = decodeJWT(data.access);
      if (decoded) {
        // 🔹 Guardamos user_id y role
        if (decoded.user_id) {
          localStorage.setItem("user_id", decoded.user_id);
        }
        localStorage.setItem("role", decoded.role || "cliente");

        // 🔹 Guardamos username si viene en el token
        if (decoded.username) {
          localStorage.setItem("username", decoded.username);
        } else {
          // fallback: usamos el username del form
          localStorage.setItem("username", username);
        }
      }

      // ✅ Recargar página o cerrar panel
      window.location.reload();
    } else {
      errorBox.textContent = `❌ ${data.error || "Error de autenticación"}`;
    }
  } catch (err) {
    errorBox.textContent = `❌ Error inesperado: ${err.message}`;
  }
});
