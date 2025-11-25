// header.js
function decodeJWT(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return {};
  }
}

export function setupHeaderScroll() {
  const header = document.querySelector("header");
  const logo = document.getElementById("Logo");
  
  window.addEventListener("scroll", () => {
    const scrollY = window.scrollY;
    
    // Toggle clase scrolled
    header.classList.toggle("scrolled", scrollY > 10);
    
    // Reducción gradual del logo SOLO EN WEB (desktop)
    if (logo && window.innerWidth > 768) {
      const maxScroll = 200;
      const minSize = 130;
      const maxSize = 200;
      
      if (scrollY <= maxScroll) {
        const progress = scrollY / maxScroll;
        const newSize = maxSize - (progress * (maxSize - minSize));
        logo.style.width = `${newSize}px`;
      } else {
        logo.style.width = `${minSize}px`;
      }
    }
    // En mobile y tablet, no aplicar ningún cambio de tamaño (usa el CSS)
  });
}

export function setupHeaderPanels() {
  document.addEventListener("DOMContentLoaded", () => {
    const overlay       = document.querySelector(".page-overlay");
    const clientePanel  = document.getElementById("cliente-panel");
    const loginPanel    = document.getElementById("login-panel");
    const wishlistPanel = document.getElementById("wishlist-panel");
    const contactPanel  = document.getElementById("contact-panel");

    const btnLogin   = document.getElementById("btn-login");
    const btnUser    = document.getElementById("btn-user-menu");
    const userSpan   = document.getElementById("cliente-username");

    const closeAllPanels = () => {
      document.querySelectorAll(".login-panel").forEach(p => p.classList.remove("open"));
      overlay.classList.remove("active");
      document.body.classList.remove("no-scroll");
    };

    const openPanel = (panel) => {
      closeAllPanels();
      if (panel) {
        panel.classList.add("open");
        overlay.classList.add("active");
        document.body.classList.add("no-scroll");
      }
    };

    // --- Mostrar botones según JWT ---
    const access = localStorage.getItem("access");
    if (access) {
      const decoded = decodeJWT(access);
      if (btnLogin) btnLogin.style.display = "none";
      if (btnUser) btnUser.style.display = "inline-flex";
      if (userSpan) userSpan.textContent = decoded.username || `Cliente #${decoded.user_id}`;
    } else {
      if (btnLogin) btnLogin.style.display = "inline-flex";
      if (btnUser) btnUser.style.display = "none";
    }

    // Abrir login panel al click en "btn-login"
    btnLogin?.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel(loginPanel);
    });

    // Abrir cliente panel al click en "btn-user-menu"
    btnUser?.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel(clientePanel);
    });

    // Wishlist
    document.getElementById("link-wishlist")?.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel(wishlistPanel);
      window.renderWishlistPanel?.();
    });

    // Perfil - redirigir con ID del cliente
    document.getElementById("link-perfil")?.addEventListener("click", (e) => {
      e.preventDefault();
      const userId = localStorage.getItem("user_id");
      if (userId) {
        window.location.href = `/perfil/${userId}/`;
      } else {
        alert("No se pudo obtener el ID del usuario");
      }
    });

    // Contacto
    document.querySelector('#cliente-panel .quick-links a[href="/contacto/"]')
      ?.addEventListener("click", (e) => {
        e.preventDefault();
        openPanel(contactPanel);
      });

    // --- 🔑 LOGIN con JWT ---
    document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
      const errorEl  = document.getElementById("login-error");

      try {
        const res = await fetch("/auth/login_client/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        if (!res.ok) throw new Error("Credenciales inválidas");
        const data = await res.json();

        // Guardamos tokens
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);

        const decoded = decodeJWT(data.access);
        if (decoded) {
          localStorage.setItem("user_id", decoded.user_id || "");
          localStorage.setItem("role", decoded.role || "cliente");
        }
        
        // Guardar username si viene en la respuesta
        if (data.username) {
          localStorage.setItem("username", data.username);
        }

        closeAllPanels();
        window.location.reload();
      } catch (err) {
        if (errorEl) errorEl.textContent = err.message;
      }
    });

    // --- 🔑 LOGOUT con JWT ---
    document.getElementById("link-logout")?.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        localStorage.clear();
      } finally {
        window.location.href = "/";
      }
    });
  });
}
