// header.js
export function setupHeaderScroll() {
  window.addEventListener('scroll', () => {
    document.querySelector('header')
            .classList.toggle('scrolled', window.scrollY > 10);
  });
}

export function setupHeaderPanels() {
  document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.querySelector('.page-overlay');
    const clientePanel = document.getElementById('cliente-panel');
    const wishlistPanel = document.getElementById('wishlist-panel');
    const contactPanel  = document.getElementById('contact-panel');

    const closeAllPanels = () => {
      document.querySelectorAll('.login-panel').forEach(p => p.classList.remove('open'));
      overlay.classList.remove('active');
      document.body.classList.remove('no-scroll');
    };

    const openPanel = (panel) => {
      closeAllPanels();
      if (panel) {
        panel.classList.add('open');
        overlay.classList.add('active');
        document.body.classList.add('no-scroll');
      }
    };

    // Wishlist desde menú cliente
    document.getElementById('link-wishlist')?.addEventListener('click', (e) => {
      e.preventDefault();
      openPanel(wishlistPanel);
    });

    // Contacto desde menú cliente
    document.querySelector('#cliente-panel .quick-links a[href="/contacto/"]')
      ?.addEventListener('click', (e) => {
        e.preventDefault();
        openPanel(contactPanel);
      });

        const wishlistBtnInsideClientePanel = document.getElementById('link-wishlist');
  if (wishlistBtnInsideClientePanel) {
    wishlistBtnInsideClientePanel.addEventListener('click', (e) => {
      e.preventDefault();
      // Muestra el wishlist desde aquí correctamente
      window.renderWishlistPanel?.();
      document.getElementById('wishlist-panel')?.classList.add('open');
      document.querySelector('.page-overlay')?.classList.add('active');
      document.body.classList.add('no-scroll');
    });
  }

  });
}
