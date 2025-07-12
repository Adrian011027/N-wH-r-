/* ============================================================
   Animaciones de tarjetas y bloque de introducción
   ============================================================ */

/* ─────────────────────────────────────────────────────────────
   1. Tarjetas de categoría (.categoria-card)
   ──────────────────────────────────────────────────────────── */
export function setupCategoriaCards() {
  const cards = document.querySelectorAll('.categoria-card');
  console.log('🟢 Encontradas:', cards.length, 'tarjetas');

  if (!cards.length) return;

  const cardObserver = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const card  = entry.target;
        const index = [...cards].indexOf(card);
        const delay = index * 150;

        /* animación escalonada */
        card.style.transitionDelay = `${delay}ms`;

        const overlay = card.querySelector('.overlay-text');
        if (overlay) overlay.style.transitionDelay = `${delay + 500}ms`;

        card.classList.add('visible');
        obs.unobserve(card);
        console.log('🔵 Animación tarjeta:', card);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => cardObserver.observe(card));
}

/* ─────────────────────────────────────────────────────────────
   2. Texto de introducción (.promo-intro__title / __subtitle)
   ──────────────────────────────────────────────────────────── */
export function setupIntroAnimation() {
  const introItems = document.querySelectorAll(
    '.promo-intro__title, .promo-intro__subtitle'
  );
  console.log('🟢 Encontrados:', introItems.length, 'elementos de intro');

  if (!introItems.length) return;

  const introObserver = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        obs.unobserve(entry.target);
        console.log('🔵 Animación intro:', entry.target);
      }
    });
  }, {
    threshold: 0,                 // basta con que asome 1 px
    rootMargin: '0px 0px -30% 0px'// dispara cuando ha entrado ~70 %
  });

  introItems.forEach(el => introObserver.observe(el));
}

/* ─────────────────────────────────────────────────────────────
   3. Inicialización global
   ──────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setupCategoriaCards();
  setupIntroAnimation();
});
