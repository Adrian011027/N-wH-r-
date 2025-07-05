/* -------------------------------------------------------------
   main.js – Home de NowHere
   ------------------------------------------------------------- */

import { setupScrollRestoration }  from './scroll-behavior.js';
import { setupHeaderScroll, setupHeaderPanels } from './header.js';
import { setupBurgerMenu }         from './burger-menu.js';
import { setupZoomEffect }         from './zoom-effect.js';
import { setupAccordion }          from './accordion.js';
import { setupNavigationButtons }  from './navigation.js';
import { setupContactPanel }       from './contact-panel.js';
import { setupLoginPanel }         from './usuario.js';
import { getCSRFToken }            from './login.js';
import { setupClientePanel }       from './logged.js';
import { initWishlist }            from './wishlist.js';
import { setupCategoriaCards }     from './categorias-gral.js';

/* —— Datos globales —— */
const IS_AUTH = window.IS_AUTHENTICATED === true;
const USER_ID = window.CLIENTE_ID ?? null;
const CSRF    = window.CSRF_TOKEN ?? null;

/* —— Categorías + animaciones iniciales —— */
document.addEventListener('DOMContentLoaded', () => {
  setupCategoriaCards();
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
    csrfToken       : CSRF,
    backendURL      : '/wishlist/',
    fetchProductoURL: '/api/productos_por_ids/?ids='
  });
});

/* —— Logout limpio (form cualquiera con "logout" en action) —— */
document.addEventListener('submit', async e => {
  const form = e.target.closest('form[action*="logout"]');
  if (!form) return;

  e.preventDefault();                       // detén recarga automática

  try {
    await fetch(form.action, {
      method : 'POST',
      headers: { 'X-CSRFToken': CSRF }
    });
  } catch {/* even on error, proceed */}

  wishlistAPI?.nukeAllKeys?.();             // 🧹 borra guest + users
  window.location.href = '/';               // refresca como invitado
});

/* —— Módulos de interfaz —— */
setupScrollRestoration();
setupHeaderScroll();
setupHeaderPanels()
setupBurgerMenu();
setupZoomEffect();
setupAccordion();
setupNavigationButtons();
setupContactPanel();
setupLoginPanel();
setupClientePanel();
getCSRFToken();


document.addEventListener('DOMContentLoaded', () => {

  const burger   = document.getElementById('btn-burger');      // ☰
  const navMenu  = document.querySelector('.nav-menu');        // panel
  const overlay  = document.querySelector('.page-overlay');    // vidrio
  const closeBtn = document.getElementById('btn-close-menu');  // × dentro

  function abrirMenu(){
    navMenu.classList.add('open');
    overlay.classList.add('active');
    burger.classList.add('active');
    document.body.classList.add('no-scroll');
  }

  function cerrarMenu(){
    navMenu.classList.remove('open');
    overlay.classList.remove('active');
    burger.classList.remove('active');
    document.body.classList.remove('no-scroll');
  }

  burger .addEventListener('click', abrirMenu);    // abre
  overlay.addEventListener('click', cerrarMenu);   // clic fuera
  closeBtn.addEventListener('click', cerrarMenu);  // clic ×

});