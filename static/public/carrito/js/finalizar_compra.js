document.addEventListener('DOMContentLoaded', () => {
  const contenedor = document.getElementById('carrito-container');
  if (contenedor) {
    contenedor.offsetWidth;
    contenedor.classList.add('fade-in-carrito');
  }

  const form = document.querySelector('form[action*="enviar"]');
  const btnConfirmar = document.querySelector('.btn-finalizar');

  if (form && btnConfirmar) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault(); // Prevenir submit tradicional
      
      btnConfirmar.disabled = true;
      btnConfirmar.textContent = 'Confirmando...';

      try {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // 🔐 JWT: Usar fetchPost que agrega automáticamente el token
        const response = await fetchPost(form.action, data);
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Error al finalizar compra');
        }

        const result = await response.json();
        
        // Redirigir a la página de éxito
        if (result.redirect) {
          window.location.href = result.redirect;
        } else {
          // Si no hay redirect en la respuesta, construirlo manualmente
          const carritoId = form.action.match(/ordenar\/(\d+)\//)[1];
          window.location.href = `/ordenar/${carritoId}/exito/`;
        }
        
      } catch (error) {
        console.error('Error al finalizar compra:', error);
        alert('Error al finalizar la compra: ' + error.message);
        btnConfirmar.disabled = false;
        btnConfirmar.textContent = 'Confirmar compra';
      }
    });
  }

  // ════════════════════════════════════════════════════════════
  // Botones de envío de ticket (WhatsApp y Email)
  // ════════════════════════════════════════════════════════════
  const btnWhatsApp = document.getElementById('btn-ticket-whatsapp');
  const btnEmail = document.getElementById('btn-ticket-email');
  const mensajeEnvio = document.getElementById('mensaje-envio');

  if (btnWhatsApp) {
    btnWhatsApp.addEventListener('click', async () => {
      const carritoId = window.location.pathname.match(/ordenar\/(\d+)/)?.[1];
      if (!carritoId) {
        alert('Error: No se pudo obtener el ID del carrito');
        return;
      }

      btnWhatsApp.disabled = true;
      btnWhatsApp.textContent = 'Enviando...';
      mensajeEnvio.textContent = '';
      mensajeEnvio.style.color = 'blue';

      try {
        const response = await fetchPost(`/api/orden/${carritoId}/ticket/whatsapp/`, {});
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Error al enviar WhatsApp');
        }

        const result = await response.json();
        mensajeEnvio.style.color = 'green';
        mensajeEnvio.innerHTML = '✅ ' + result.message;
        
        // Deshabilitar ambos botones después de enviar
        btnWhatsApp.style.opacity = '0.5';
        btnEmail.style.opacity = '0.5';
        btnEmail.disabled = true;

      } catch (error) {
        console.error('Error al enviar ticket por WhatsApp:', error);
        mensajeEnvio.style.color = 'red';
        mensajeEnvio.innerHTML = '❌ ' + error.message;
        btnWhatsApp.disabled = false;
        btnWhatsApp.textContent = 'WhatsApp';
      }
    });
  }

  if (btnEmail) {
    btnEmail.addEventListener('click', async () => {
      const carritoId = window.location.pathname.match(/ordenar\/(\d+)/)?.[1];
      if (!carritoId) {
        alert('Error: No se pudo obtener el ID del carrito');
        return;
      }

      btnEmail.disabled = true;
      btnEmail.textContent = 'Enviando...';
      mensajeEnvio.textContent = '';
      mensajeEnvio.style.color = 'blue';

      try {
        const response = await fetchPost(`/api/orden/${carritoId}/ticket/email/`, {});
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Error al enviar email');
        }

        const result = await response.json();
        mensajeEnvio.style.color = 'green';
        mensajeEnvio.innerHTML = '✅ ' + result.message;
        
        // Deshabilitar ambos botones después de enviar
        btnEmail.style.opacity = '0.5';
        btnWhatsApp.style.opacity = '0.5';
        btnWhatsApp.disabled = true;

      } catch (error) {
        console.error('Error al enviar ticket por Email:', error);
        mensajeEnvio.style.color = 'red';
        mensajeEnvio.innerHTML = '❌ ' + error.message;
        btnEmail.disabled = false;
        btnEmail.textContent = 'Email';
      }
    });
  }
});
