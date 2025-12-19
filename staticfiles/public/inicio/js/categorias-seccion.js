export function setupNavigationButtons() {
  const botones = document.querySelectorAll(".btn-seleccion");

  botones.forEach((boton) => {
    boton.addEventListener("click", function () {
      const seccion = this.getAttribute("data-seccion");
      if (seccion) {
        const url = `/coleccion/${seccion}/`;  // Ajusta si tu URL es diferente
        window.location.href = url;
      }
    });
  });
}
