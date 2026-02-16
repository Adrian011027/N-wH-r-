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

    // AGREGAR IMÁGENES DE VARIANTES AL FORMDATA
    if (window.variantGalleries) {
      console.log('[FORM] Procesando imágenes de variantes...');
      console.log('[FORM] window.variantGalleries:', window.variantGalleries);
      
      for (const varianteId in window.variantGalleries) {
        const gallery = window.variantGalleries[varianteId];
        console.log(`[FORM] Variante ${varianteId}:`, gallery);
        
        // Agregar imágenes nuevas de esta variante
        if (gallery.newImages && gallery.newImages.length > 0) {
          console.log(`[FORM] Variante ${varianteId}: agregando ${gallery.newImages.length} imagen(es)`);
          gallery.newImages.forEach((imgData, idx) => {
            const fieldName = `variante_imagen_${varianteId}_${idx}`;
            formData.append(fieldName, imgData.file);
            console.log(`[FORM] Campo agregado: ${fieldName}`);
          });
        }
        
        // Agregar IDs de imágenes a eliminar de esta variante
        if (gallery.imagesToDelete && gallery.imagesToDelete.size > 0) {
          const deleteIds = Array.from(gallery.imagesToDelete);
          console.log(`[FORM] Variante ${varianteId}: marcando ${deleteIds.length} imagen(es) para eliminar`);
          console.log(`[FORM] IDs a eliminar:`, deleteIds);
          formData.append(`variante_imagenes_a_eliminar_${varianteId}`, JSON.stringify(deleteIds));
        } else {
          console.log(`[FORM] Variante ${varianteId}: sin imágenes para eliminar`);
        }
      }
    } else {
      console.log('[FORM] window.variantGalleries no existe');
    }

    try {
      /* 1. Actualiza el producto principal ----------------------- */
      const resProd = await authFetch(`/api/productos/update/${productoId}/`, {
        method: 'POST',
        body: formData
      });

      const dataProd = await resProd.json();
      if (!resProd.ok) {
        console.error('[ERROR] Respuesta del servidor:', dataProd);
        throw new Error(dataProd.error || 'Error al actualizar producto');
      }

      /* 2. Actualiza cada variante ------------------------------- */
      const variantes = form.querySelectorAll('input[name="variante_id"]');

      for (let input of variantes) {
        const vId = input.value;
        const tallas_stock_raw = form.querySelector(`[name="variante_tallas_stock_${vId}"]`)?.value;
        const precio = form.querySelector(`[name="variante_precio_${vId}"]`)?.value;
        const precio_mayorista = form.querySelector(`[name="variante_precio_mayorista_${vId}"]`)?.value;
        const color = form.querySelector(`[name="variante_color_${vId}"]`)?.value;

        const params = new URLSearchParams({ precio, precio_mayorista, color });
        if (tallas_stock_raw) {
          params.set('tallas_stock', tallas_stock_raw);
        }

        const varRes = await authFetch(`/api/variantes/update/${vId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: params
        });
        
        if (!varRes.ok) {
          console.error(`[ERROR] Error actualizando variante ${vId}:`, await varRes.json());
        }
      }

      /* 3. Mensaje de éxito */
      mensaje.className = 'form-message success';
      mensaje.textContent = dataProd.mensaje || '✅ Producto actualizado correctamente';
      toast('Producto actualizado correctamente', 'success');

    } catch (err) {
      console.error('[ERROR COMPLETO]', err);
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
