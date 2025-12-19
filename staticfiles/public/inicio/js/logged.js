export function setupClientePanel() {
  const userIcon = document.getElementById("btn-user-menu");
  const clientePanel = document.getElementById("cliente-panel");
  const closeClientePanel = document.getElementById("close-cliente-panel");
  const pageOverlay = document.querySelector(".page-overlay");
  const btnBurger = document.getElementById("btn-burger"); // ⬅️ añadido

  if (userIcon && clientePanel && closeClientePanel) {
    // Abrir panel cliente
    userIcon.addEventListener("click", (e) => {
      e.stopPropagation();
      clientePanel.classList.add("open");
      pageOverlay.classList.add("active");
    });

    // Cerrar con botón cerrar
    closeClientePanel.addEventListener("click", () => {
      clientePanel.classList.remove("open");
      pageOverlay.classList.remove("active");
    });

    // Cerrar si haces clic fuera (pero ignorar si fue en el burger)
    document.addEventListener("click", (e) => {
      if (
        clientePanel.classList.contains("open") &&                          // ✅ sólo si está abierto
        !clientePanel.contains(e.target) &&
        !userIcon.contains(e.target) &&
        !(btnBurger && btnBurger.contains(e.target))                        // ✅ ignorar clic en burger
      ) {
        clientePanel.classList.remove("open");
        pageOverlay.classList.remove("active");
      }
    });

    // Evitar propagación dentro del panel
    clientePanel.addEventListener("click", (e) => e.stopPropagation());
  }
}
