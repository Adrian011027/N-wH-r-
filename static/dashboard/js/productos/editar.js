/* editar.js – Dashboard editar producto con JWT (Diseño Moderno) */
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('editarForm');
  const mensaje = document.getElementById('mensaje');
  const imageInput = document.getElementById('imagen');
  const imagePreview = document.getElementById('imagePreview');
  const uploadArea = document.getElementById('imageUploadArea');

  // 🖼️ Preview de nueva imagen
  if (imageInput && imagePreview) {
    imageInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          imagePreview.src = e.target.result;
          imagePreview.style.display = 'block';
          if (uploadArea) {
            const placeholder = uploadArea.querySelector('.upload-placeholder');
            if (placeholder) placeholder.style.display = 'none';
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    mensaje.textContent = '';
    mensaje.className = 'form-message';

    const submitBtn = form.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<div class="spinner-small"></div> Guardando...';
    submitBtn.disabled = true;

    const formData = new FormData(form);
    const productoId = formData.get('id');

    // AGREGAR IMÁGENES NUEVAS AL FORMDATA
    // Las imágenes nuevas están en window.galleryManager.newImages
    if (window.galleryManager && window.galleryManager.newImages && window.galleryManager.newImages.length > 0) {
      console.log('[FORM] Agregando ' + window.galleryManager.newImages.length + ' imágenes nuevas al FormData');
      // Agregar cada imagen como un archivo separado al FormData
      // Usando el nombre 'imagen_galeria_upload' para ser compatible con el backend
      window.galleryManager.newImages.forEach((imgData, index) => {
        formData.append('imagen_galeria_upload', imgData.file);
        console.log('[FORM] Imagen ' + (index + 1) + ' agregada: ' + imgData.file.name);
      });
    }

    // AGREGAR IMÁGENES A ELIMINAR AL FORMDATA JSON
    if (window.galleryManager && window.galleryManager.imagesToDelete && window.galleryManager.imagesToDelete.size > 0) {
      console.log('[FORM] Imágenes a eliminar: ' + Array.from(window.galleryManager.imagesToDelete).join(','));
      formData.append('imagenes_a_eliminar', JSON.stringify(Array.from(window.galleryManager.imagesToDelete)));
    }

    try {
      /* 1. Actualiza el producto principal ----------------------- */
      const resProd = await authFetch(`/api/productos/update/${productoId}/`, {
        method: 'POST',
        body: formData
      });

      const dataProd = await resProd.json();
      if (!resProd.ok) throw new Error(dataProd.error || 'Error al actualizar producto');

      /* 2. Actualiza cada variante ------------------------------- */
      const variantes = form.querySelectorAll('input[name="variante_id"]');

      for (let input of variantes) {
        const vId = input.value;
        const stock = form.querySelector(`[name="variante_stock_${vId}"]`)?.value;
        const precio = form.querySelector(`[name="variante_precio_${vId}"]`)?.value;
        const precio_mayorista = form.querySelector(`[name="variante_precio_mayorista_${vId}"]`)?.value;
        const talla = form.querySelector(`[name="variante_talla_${vId}"]`)?.value;
        const color = form.querySelector(`[name="variante_color_${vId}"]`)?.value;

        await authFetch(`/api/variantes/update/${vId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({ stock, precio, precio_mayorista, talla, color })
        });
      }

      /* 3. Mensaje de éxito */
      mensaje.className = 'form-message success';
      mensaje.textContent = dataProd.mensaje || '✅ Producto actualizado correctamente';
      toast('Producto actualizado correctamente', 'success');

    } catch (err) {
      mensaje.className = 'form-message error';
      mensaje.textContent = '❌ ' + err.message;
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
