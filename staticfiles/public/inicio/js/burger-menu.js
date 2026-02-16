// Maneja apertura/cierre del menú lateral
export function setupBurgerMenu() {
  const btnBurger = document.getElementById('btn-burger');
  const navMenu   = document.querySelector('.nav-menu');
  const overlay   = document.querySelector('.page-overlay');
  const label     = document.querySelector('.menu-label');

  function toggleMenu(open) {
    navMenu.classList.toggle('open',   open);
    overlay.classList.toggle('active', open);
    btnBurger.classList.toggle('active', open);
  }

  // Abre o cierra al hacer clic en el botón
  btnBurger.addEventListener('click', () => {
    toggleMenu(!navMenu.classList.contains('open'));
  });

  // Cierra al hacer clic fuera
  overlay.addEventListener('click', () => toggleMenu(false));

  // Cierra con ESC
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') toggleMenu(false);
  });
}
