export function setupCategoriaCards() {
  const cards = document.querySelectorAll('.categoria-card');
  console.log('🟢 Encontradas:', cards.length, 'tarjetas');

  if (!cards.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const card = entry.target;
        const index = [...cards].indexOf(card);
        const delay = index * 150;

        // Animación escalonada para la tarjeta
        card.style.transitionDelay = `${delay}ms`;

        // Animación escalonada + 500ms para el texto
        const overlay = card.querySelector('.overlay-text');
        if (overlay) {
          overlay.style.transitionDelay = `${delay + 500}ms`;
        }

        card.classList.add('visible');
        observer.unobserve(card);

        console.log('🔵 Activando animación en:', card);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => observer.observe(card));

  
}

// animations.js

/**
 * Observa las tarjetas de categoría y el texto de introducción,
 * y dispara las animaciones cuando entran en el viewport.
 */
export function setupAnimations() {
  // ─── 1. Tarjetas de categoría ───────────────────────────────
  const cards = document.querySelectorAll('.categoria-card');
  console.log('🟢 Encontradas:', cards.length, 'tarjetas');

  if (cards.length) {
    const cardObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const card = entry.target;
          const index = Array.from(cards).indexOf(card);
          const delay = index * 150;

          // Animación escalonada para la tarjeta
          card.style.transitionDelay = `${delay}ms`;

          // Animación escalonada +500 ms para el texto superpuesto
          const overlay = card.querySelector('.overlay-text');
          if (overlay) {
            overlay.style.transitionDelay = `${delay + 500}ms`;
          }

          card.classList.add('visible');
          observer.unobserve(card);
          console.log('🔵 Animación tarjeta:', card);
        }
      });
    }, { threshold: 0.1 });

    cards.forEach(card => cardObserver.observe(card));
  }


  // ─── 2. Texto de introducción (título y subtítulo) ──────────
  const introItems = document.querySelectorAll(
    '.promo-intro__title, .promo-intro__subtitle'
  );
  console.log('🟢 Encontrados:', introItems.length, 'elementos de intro');

  if (introItems.length) {
    const introObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
          console.log('🔵 Animación intro:', entry.target);
        }
      });
    }, { threshold: 0.3 });

    introItems.forEach(el => introObserver.observe(el));
  }
}


// ─── Inicialización al cargar la página ───────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupAnimations();
});

