export function setupContactPanel() {
  const btnContacto        = document.getElementById('btn-contacto');
  const contactPanel       = document.getElementById('contact-panel');
  const closeContactPanel  = document.getElementById('close-contact-panel');
  const pageOverlay        = document.querySelector('.page-overlay');
  const btnBurger          = document.getElementById('btn-burger');

  if (!btnContacto || !contactPanel || !closeContactPanel || !pageOverlay) return;

  const abrirPanel = () => {
    contactPanel.classList.add('open');
    pageOverlay.classList.add('active');
  };

  const cerrarPanel = () => {
    contactPanel.classList.remove('open');

    // Oculta overlay solo si no hay otros paneles abiertos
    const navMenu      = document.querySelector('.nav-menu');
    const clientePanel = document.getElementById('cliente-panel');

    const algoAbierto = navMenu?.classList.contains('open') ||
                        clientePanel?.classList.contains('open');

    if (!algoAbierto) {
      pageOverlay.classList.remove('active');
    }
  };

  btnContacto.addEventListener('click', (e) => {
    e.stopPropagation();
    abrirPanel();
  });

  closeContactPanel.addEventListener('click', cerrarPanel);

  document.addEventListener('click', (e) => {
    if (
      contactPanel.classList.contains('open') &&
      !contactPanel.contains(e.target) &&
      !btnContacto.contains(e.target) &&
      !(btnBurger && btnBurger.contains(e.target))
    ) {
      cerrarPanel();
    }
  });

  pageOverlay.addEventListener('click', cerrarPanel);

  contactPanel.addEventListener('click', (e) => e.stopPropagation());
}
