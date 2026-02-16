/* editar.js – Dashboard editar cliente con JWT */
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.cliente-form-card');
  
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<div class="spinner-small"></div> Guardando...';
    submitBtn.disabled = true;

    // Obtener el ID del cliente desde la URL (último segmento)
    const pathParts = window.location.pathname.split('/');
    const clienteId = pathParts[pathParts.length - 2];

    const formData = {
      username: form.querySelector('[name="username"]').value.trim(),
      correo: form.querySelector('[name="correo"]').value.trim(),
      nombre: form.querySelector('[name="nombre"]').value.trim(),
      telefono: form.querySelector('[name="telefono"]').value.trim(),
      direccion: form.querySelector('[name="direccion"]').value.trim()
    };

    try {
      const response = await authFetch(`/clientes/update/${clienteId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al actualizar cliente');
      }

      toast('Cliente actualizado correctamente', 'success');
      
      // Redirigir después de 1 segundo
      setTimeout(() => {
        window.location.href = '/dashboard/clientes/';
      }, 1000);

    } catch (err) {
      toast(err.message, 'error');
      console.error(err);
    } finally {
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
    }
  });
});

// Toast notification
function toast(msg, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  
  requestAnimationFrame(() => t.classList.add('show'));
  
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 400);
  }, 3000);
}
