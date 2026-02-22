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
      
      for (const varianteId in window.variantGalleries) {
        const gallery = window.variantGalleries[varianteId];
        
        // Agregar imágenes nuevas de esta variante
        if (gallery.newImages && gallery.newImages.length > 0) {
          gallery.newImages.forEach((imgData, idx) => {
            const fieldName = `variante_imagen_${varianteId}_${idx}`;
            formData.append(fieldName, imgData.file);
          });
        }
        
        // Agregar IDs de imágenes a eliminar de esta variante
        if (gallery.imagesToDelete && gallery.imagesToDelete.size > 0) {
          const deleteIds = Array.from(gallery.imagesToDelete);
          formData.append(`variante_imagenes_a_eliminar_${varianteId}`, JSON.stringify(deleteIds));
        } else {
        }
      }
    } else {
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

      /* 2. Procesar variantes (crear nuevas o actualizar existentes) */
      const variantes = form.querySelectorAll('input[name="variante_id"]');

      for (let input of variantes) {
        const vId = input.value;
        const tallas_stock_raw = form.querySelector(`[name="variante_tallas_stock_${vId}"]`)?.value;
        const precio = form.querySelector(`[name="variante_precio_${vId}"]`)?.value;
        const precio_mayorista = form.querySelector(`[name="variante_precio_mayorista_${vId}"]`)?.value;
        const color = form.querySelector(`[name="variante_color_${vId}"]`)?.value;

        // Detectar si es variante nueva (ID temporal)
        if (vId.startsWith('new-')) {
          // CREAR NUEVA VARIANTE
          const createFormData = new FormData();
          createFormData.append('producto_id', productoId);
          createFormData.append('color', color || 'N/A');
          createFormData.append('precio', precio || '0');
          createFormData.append('precio_mayorista', precio_mayorista || '0');
          
          if (tallas_stock_raw) {
            createFormData.append('tallas_stock', tallas_stock_raw);
          } else {
            console.error(`[ERROR] Falta tallas_stock para variante nueva ${vId}`);
            continue;
          }

          // Agregar imágenes de la variante nueva
          if (window.variantGalleries && window.variantGalleries[vId]) {
            const gallery = window.variantGalleries[vId];
            if (gallery.newImages && gallery.newImages.length > 0) {
              gallery.newImages.forEach((imgData, idx) => {
                createFormData.append(`imagenes_${idx}`, imgData.file);
              });
            }
          }

          const createRes = await authFetch('/api/variantes/create/', {
            method: 'POST',
            body: createFormData
          });

          if (!createRes.ok) {
            const errorData = await createRes.json();
            console.error(`[ERROR] Error creando variante nueva ${vId}:`, errorData);
            throw new Error(`Error al crear variante: ${errorData.error || 'Error desconocido'}`);
          } else {
            const createData = await createRes.json();
          }

        } else {
          // ACTUALIZAR VARIANTE EXISTENTE
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
            const errorData = await varRes.json();
            console.error(`[ERROR] Error actualizando variante ${vId}:`, errorData);
          } else {
          }
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
