export function setupNavigationButtons() {
  document.querySelectorAll('.btn-seleccion').forEach(btn => {
    btn.addEventListener('click', () => {
      const seccion = btn.dataset.seccion;
      localStorage.setItem('origenSeccion', seccion);
      window.location.href = `/coleccion/${seccion}/`;

    });
  });
}
