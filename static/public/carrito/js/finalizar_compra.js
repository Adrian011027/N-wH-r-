document.addEventListener('DOMContentLoaded', () => {
  const contenedor = document.getElementById('carrito-container');
  if (contenedor) {
    contenedor.offsetWidth;
    contenedor.classList.add('fade-in-carrito');
  }

  const form = document.querySelector('form[action*="enviar"]'); // Selecciona el form correcto
  const btnConfirmar = document.querySelector('.btn-finalizar');

  if (form && btnConfirmar) {
    form.addEventListener('submit', () => {
      btnConfirmar.disabled = true;
      btnConfirmar.textContent = 'Confirmando...';
    });
  }
});
