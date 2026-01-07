// static/shared/js/productos_genero.js

window.addEventListener('load', () => {
  // 1. Fade-in dinámico de sección (PRIMERO - antes de cualquier validación)
  const sections = document.querySelectorAll('.dama-section, .caballero-section, .hombre-section, .mujer-section');
  console.log('Secciones encontradas:', sections.length);
  sections.forEach(sec => {
    console.log('Agregando fade-in a:', sec.className);
    sec.classList.add('fade-in');
  });

  const dropdown     = document.getElementById('dropdown');
  const selectedDiv  = dropdown?.querySelector('.selected');
  const optionsList  = dropdown?.querySelector('.options');
  const grid         = document.querySelector('.productos-grid');
  const allCards     = Array.from(grid?.querySelectorAll('.producto-card') || []);

  if (!dropdown || !selectedDiv || !optionsList || !grid) return;

  // 2. Toggle menú desplegable
  selectedDiv.addEventListener('click', () => dropdown.classList.toggle('open'));

  document.addEventListener('click', e => {
    if (!dropdown.contains(e.target)) dropdown.classList.remove('open');
  });

  // 2. Filtrar productos por categoría
  const renderProductos = categoria => {
    allCards.forEach(card => {
      const cat  = card.getAttribute('data-categoria');
      const show = categoria === 'all' || cat === categoria;
      card.style.display = show ? 'block' : 'none';
    });
  };

  renderProductos('all');

  optionsList.addEventListener('click', e => {
    const option = e.target.closest('.option');
    if (!option) return;

    optionsList.querySelectorAll('.option')
               .forEach(o => o.classList.remove('selected'));
    option.classList.add('selected');

    selectedDiv.childNodes[0].nodeValue = option.textContent.trim();
    renderProductos(option.dataset.value);
    dropdown.classList.remove('open');
  });

  // 3. Guardar en localStorage
  allCards.forEach(card => {
    const link = card.querySelector('a');
    if (!link) return;

    link.addEventListener('click', () => {
      const productoSeleccionado = {
        id     : card.dataset.id,
        nombre : card.dataset.nombre,
        precio : card.dataset.precio
      };
      localStorage.setItem('productoSeleccionado', JSON.stringify(productoSeleccionado));

      const seccion = document.body.classList.contains('caballero') ? 'caballero' : 'dama';
      localStorage.setItem('origenSeccion', seccion);
    });
  });
});

// 5. Zoom al hacer scroll
(() => {
  const onScrollProductos = () => {
    const cards = document.querySelectorAll('.producto-card');
    const windowHeight = window.innerHeight;

    cards.forEach(card => {
      const img = card.querySelector('.zoomable');
      if (!img) return;

      const rect         = card.getBoundingClientRect();
      const visibleRatio = Math.min(Math.max((windowHeight - rect.top) / windowHeight, 0), 1);

      img.style.transform  = `scale(${1 + visibleRatio * 0.2})`;
      img.style.transition = 'transform 0.2s ease-out';
    });
  };

  window.addEventListener('scroll', onScrollProductos, { passive: true });
  onScrollProductos();
})();
