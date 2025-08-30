/* editar.js – dashboard editar producto con JWT */
document.getElementById('editarForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const form     = e.target;
  const mensaje  = document.getElementById('mensaje');
  mensaje.textContent = '';

  const formData   = new FormData(form);
  const productoId = formData.get('id');

  const token = localStorage.getItem('access'); // 🔑 JWT access token
  if (!token) {
    mensaje.style.color = 'red';
    mensaje.textContent = '❌ No tienes sesión iniciada.';
    return;
  }

  try {
    /* 1. Actualiza el producto principal ----------------------- */
    const resProd = await fetch(`/api/productos/update/${productoId}/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData // mantiene multipart/form-data
    });

    const dataProd = await resProd.json();
    if (!resProd.ok) throw new Error(dataProd.error || 'Error al actualizar producto');

    /* 2. Actualiza cada variante ------------------------------- */
    const variantes = form.querySelectorAll('input[name="variante_id"]');

    for (let input of variantes) {
      const vId    = input.value;
      const stock  = form.querySelector(`[name="variante_stock_${vId}"]`)?.value;
      const precio = form.querySelector(`[name="variante_precio_${vId}"]`)?.value;
      const precio_mayorista = form.querySelector(`[name="variante_precio_mayorista_${vId}"]`)?.value;

      await fetch(`/api/variantes/update/${vId}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({ stock, precio, precio_mayorista })
      });
    }

    /* 3. Mensaje de éxito */
    mensaje.style.color = 'green';
    mensaje.textContent = dataProd.mensaje || 'Actualizado ✔️';

  } catch (err) {
    mensaje.style.color = 'red';
    mensaje.textContent = '❌ ' + err.message;
    console.error(err);
  }
});
