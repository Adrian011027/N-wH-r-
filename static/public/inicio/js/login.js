/* -------- token desde el input oculto -------- */
export function getCSRFToken() {
  const input = document.querySelector('#loginForm input[name="csrfmiddlewaretoken"]');
  return input ? input.value : '';
}

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

/* -------- envío del formulario de login -------- */
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
    const res = await fetch("/login-client/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      const idRes = await fetch(`/api/cliente_id/${username}/`, {
        credentials: "same-origin",
      });
      if (idRes.ok) {
        const { id } = await idRes.json();
        localStorage.setItem("clienteId", id);
      } else {
        console.warn("No pude recuperar el clienteId");
      }

      window.location.reload();
    } else {
      errorBox.textContent = `❌ ${data.error || "Error desconocido"}`;
    }
  } catch (err) {
    errorBox.textContent = `❌ Error inesperado: ${err}`;
  }
});
