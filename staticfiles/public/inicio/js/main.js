/* -------------------------------------------------------------
   main.js – Home de NowHere (versión JWT completa)
------------------------------------------------------------- */

/* —— Imports de UI y lógica —— */
import { setupScrollRestoration }        from './scroll-behavior.js';
import { setupHeaderScroll, setupHeaderPanels } from './header.js';
import { setupBurgerMenu }               from './burger-menu.js';
import { setupZoomEffect }               from './zoom-effect.js';
import { setupAccordion }                from './accordion.js';
import { setupNavigationButtons }        from './navigation.js';
import { setupContactPanel }             from './contact-panel.js';
import { setupLoginPanel }               from './usuario.js';
import { setupClientePanel }             from './logged.js';
import { initWishlist }                  from './wishlist.js';
import { setupCategoriaCards, setupIntroAnimation } from './categorias-gral.js';

/* —— Datos globales JWT —— */
const IS_AUTH = !!localStorage.getItem("access");
const USER_ID = localStorage.getItem("user_id");

/* —— Animaciones iniciales —— */
document.addEventListener('DOMContentLoaded', () => {
  setupCategoriaCards();
  setupIntroAnimation();

  setTimeout(() => {
    document.querySelectorAll('.info-footer, .site-footer')
            .forEach(el => el.classList.add('fade-in-footer'));
  }, 4500);
});

/* —— Wishlist global —— */
let wishlistAPI;
document.addEventListener('DOMContentLoaded', () => {
  wishlistAPI = initWishlist({
    selector        : '.wishlist-btn',
    isAuthenticated : IS_AUTH,
    clienteId       : USER_ID,
    backendURL      : '/wishlist/',
    fetchProductoURL: '/api/productos_por_ids/?ids='
  });
});

/* —— Logout (con JWT) —— */
document.addEventListener('click', async e => {
  if (e.target.closest('#link-logout')) {
    e.preventDefault();
    try {
      const refresh = localStorage.getItem("refresh");
      if (refresh) {
        await fetch("/api/logout-client/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        });
      }
    } catch (err) {
      console.error("Error en logout:", err);
    } finally {
      wishlistAPI?.nukeAllKeys?.();
      localStorage.clear();
      window.location.href = "/";
    }
  }
});

/* —— Validar sesión y alternar login/cliente —— */
function mostrarBotonesLogin() {
  const btnLogin = document.getElementById("btn-login");
  const btnUser  = document.getElementById("btn-user-menu");
  if (btnLogin) btnLogin.style.display = "inline-flex";
  if (btnUser)  btnUser.style.display = "none";
}

async function validarSesion() {
  const access = localStorage.getItem("access");
  const role   = localStorage.getItem("role");

  // Sin token → nada que validar
  if (!access) return;

  // Si el JWT es de admin, no validar contra /clientes/
  if (role === "admin" || role === "user") return;

  // Solo validar tokens de cliente
  if (!USER_ID) return;

  try {
    const res = await fetchGet(`/clientes/${USER_ID}/`);
    if (!res.ok) throw new Error("Token inválido");
    const data = await res.json();
    document.getElementById("cliente-username").textContent = data.username || "";
  } catch {
    // Token inválido: limpiar y revertir UI
    localStorage.clear();
    mostrarBotonesLogin();
  }
}
document.addEventListener("DOMContentLoaded", validarSesion);

/* —— Módulos de interfaz —— */
setupScrollRestoration();
setupHeaderScroll();
setupHeaderPanels();
setupBurgerMenu();
setupZoomEffect();
setupAccordion();
setupNavigationButtons();
setupContactPanel();
setupLoginPanel();
setupClientePanel();

/* —— Menú hamburguesa overlay —— */
document.addEventListener('DOMContentLoaded', () => {
  const burger   = document.getElementById('btn-burger');
  const navMenu  = document.querySelector('.nav-menu');
  const overlay  = document.querySelector('.page-overlay');
  const closeBtn = document.getElementById('btn-close-menu');

  const abrirMenu  = () => {
    navMenu.classList.add('open');
    overlay.classList.add('active');
    burger.classList.add('active');
    document.body.classList.add('no-scroll');
  };
  const cerrarMenu = () => {
    navMenu.classList.remove('open');
    overlay.classList.remove('active');
    burger.classList.remove('active');
    document.body.classList.remove('no-scroll');
  };

  burger.addEventListener('click', abrirMenu);
  overlay.addEventListener('click', cerrarMenu);
  closeBtn.addEventListener('click', cerrarMenu);
});
