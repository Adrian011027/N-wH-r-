/* editar.js – Dashboard editar producto con JWT (Diseño Moderno) */
// Variable global para acceso desde otros scripts
window.editForm = null;

document.addEventListener('DOMContentLoaded', () => {
  const form = window.editForm = document.getElementById('editarForm');
  const mensaje = document.getElementById('mensaje');
  const categoriaSelect = document.querySelector('select[name="categoria_id"]');
  const subcategoriasContainer = document.getElementById('subcategorias-container');

  // 📂 Función para cargar subcategorías
  async function cargarSubcategorias(categoriaId) {
    if (!categoriaId) {
      if (subcategoriasContainer) {
        subcategoriasContainer.innerHTML = '<p style="color: #999; font-size: 14px;">Selecciona una categoría primero</p>';
      }
      return;
    }

    try {
      const response = await authFetch(`/api/subcategorias-por-categoria/${categoriaId}/`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      if (subcategoriasContainer) {
        if (data.subcategorias && Array.isArray(data.subcategorias) && data.subcategorias.length > 0) {
          subcategoriasContainer.innerHTML = '';
          data.subcategorias.forEach(sub => {
            const checkboxDiv = document.createElement('label');
            checkboxDiv.className = 'subcategoria-checkbox';
            checkboxDiv.innerHTML = `
              <input type="checkbox" name="subcategorias" value="${sub.id}" />
              <span>${sub.nombre}</span>
            `;
            subcategoriasContainer.appendChild(checkboxDiv);
          });
        } else {
          subcategoriasContainer.innerHTML = '<p style="color: #999; font-size: 14px;">No hay subcategorías disponibles</p>';
        }
      }
    } catch (err) {
      console.error(`Error cargando subcategorías:`, err);
    }
  }

  // Event listener para cambios en categoría
  if (categoriaSelect) {
    categoriaSelect.addEventListener('change', (e) => {
      cargarSubcategorias(e.target.value);
    });

    // Cargar subcategorías al inicio para la categoría seleccionada
    const categoriaId = categoriaSelect.value;
    if (categoriaId) {
      cargarSubcategorias(categoriaId);
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    mensaje.textContent = '';
    mensaje.className = 'form-message';

    const submitBtn = form.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<div class="spinner-small"></div> Guardando...';
    submitBtn.disabled = true;

    const productoId = form.querySelector('input[name="id"]').value;

    try {
      /* 1. PRIMERO: Procesar variantes (crear nuevas, obtener IDs reales) */
      const variantes = form.querySelectorAll('input[name="variante_id"]');
      const varianteIdMap = {}; // Para mapear IDs temporales a reales

      for (let input of variantes) {
        const vId = input.value;
        const stock = form.querySelector(`[name="variante_stock_${vId}"]`)?.value;
        const precio = form.querySelector(`[name="variante_precio_${vId}"]`)?.value;
        const precio_mayorista = form.querySelector(`[name="variante_precio_mayorista_${vId}"]`)?.value;
        const talla = form.querySelector(`[name="variante_talla_${vId}"]`)?.value;
        const color = form.querySelector(`[name="variante_color_${vId}"]`)?.value;

        // Detectar si es una variante nueva (ID comienza con "new-")
        if (vId.startsWith('new-')) {
          // Crear nueva variante
          const newVariantData = new FormData();
          newVariantData.append('producto_id', productoId);
          newVariantData.append('talla', talla || 'UNICA');
          newVariantData.append('color', color || 'N/A');
          newVariantData.append('precio', precio || form.querySelector('[name="precio"]')?.value);
          newVariantData.append('precio_mayorista', precio_mayorista || form.querySelector('[name="precio_mayorista"]')?.value);
          newVariantData.append('stock', stock || 0);

          try {
            const resNewVar = await authFetch('/api/variantes/create/', {
              method: 'POST',
              body: newVariantData
            });
            const dataNewVar = await resNewVar.json();
            if (!resNewVar.ok) throw new Error(dataNewVar.error || 'Error al crear variante');
            
            const actualVId = dataNewVar.id;
            varianteIdMap[vId] = actualVId;
            input.value = actualVId;
          } catch (err) {
            console.error(`Error al crear variante: ${err.message}`);
            toast(`Error al crear variante: ${err.message}`, 'error');
            throw err;
          }
        } else {
          // Actualizar variante existente
          await authFetch(`/api/variantes/update/${vId}/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({ stock, precio, precio_mayorista, talla, color })
          });
        }
      }

      /* 2. SEGUNDO: Construir FormData con IDs reales */
      const formData = new FormData(form);

      // Agregar datos de galería si existen
      if (window.galleryManager) {
        // Agregar nuevas imágenes
        window.galleryManager.newImages.forEach((img, idx) => {
          formData.append(`imagen_galeria_${idx}`, img.file);
        });
        
        // Agregar IDs de imágenes a eliminar
        if (window.galleryManager.imagesToDelete.size > 0) {
          const idsToDelete = Array.from(window.galleryManager.imagesToDelete).join(',');
          formData.append('imagenes_a_eliminar', idsToDelete);
        }
      }

      // Agregar imágenes de variantes con IDs reales
      if (window.variantGalleries) {
        const allIdsToDelete = [];
        
        Object.keys(window.variantGalleries).forEach(vId => {
          const gallery = window.variantGalleries[vId];
          const actualVId = varianteIdMap[vId] || vId; // Usar ID real si fue mapeado
          
          // Nuevas imágenes de la variante
          gallery.newImages.forEach((img, idx) => {
            formData.append(`variante_imagen_${actualVId}_${idx}`, img.file);
          });
          
          // Recopilar IDs a eliminar
          if (gallery.imagesToDelete.size > 0) {
            allIdsToDelete.push(...Array.from(gallery.imagesToDelete));
          }
        });
        
        if (allIdsToDelete.length > 0) {
          formData.append('variante_imagenes_a_eliminar', allIdsToDelete.join(','));
        }
      }

      /* 3. TERCERO: Actualizar el Producto */
      const resProd = await authFetch(`/api/productos/update/${productoId}/`, {
        method: 'POST',
        body: formData
      });

      const dataProd = await resProd.json();
      if (!resProd.ok) throw new Error(dataProd.error || 'Error al actualizar producto');

      /* 4. Mensaje de éxito */
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

// Toast notification - función global
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
