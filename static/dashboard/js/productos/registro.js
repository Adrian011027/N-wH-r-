// registro.js – Dashboard alta producto con JWT (Diseño Moderno)
document.addEventListener('DOMContentLoaded', () => {
  const form            = document.getElementById('productoForm');
  const mensaje         = document.getElementById('mensaje');
  const tallasContainer = document.getElementById('tallasContainer');
  const addTallaBtn     = document.getElementById('addTalla');
  const categoriaSelect = document.querySelector('select[name="categoria_id"]');
  
  // 🔁 Contador global para IDs de variantes temporales
  let varianteCount = 0;

  // 🔁 Función que crea una fila nueva de talla + stock + imágenes
  function crearFilaTalla() {
    const varianteId = varianteCount++;
    const row = document.createElement('div');
    row.classList.add('talla-row');
    row.id = `variante-row-${varianteId}`;
    row.style.borderBottom = '1px solid #e5e7eb';
    row.style.paddingBottom = '16px';
    row.style.marginBottom = '16px';
    
    row.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr 100px; gap: 12px; align-items: end; margin-bottom: 12px;">
        <label>
          Talla
          <input type="text" name="tallas" required placeholder="Ej. 39" />
        </label>
        <label>
          Stock
          <input type="number" name="stocks" min="0" required placeholder="10" />
        </label>
        <button type="button" class="removeTalla" style="padding: 8px 12px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer;">✕</button>
      </div>
      
      <!-- Imágenes de esta variante -->
      <div style="background: #f9fafb; padding: 12px; border-radius: 8px;">
        <small style="color: #6b7280; font-weight: 500;">Imágenes de esta variante (máx. 5)</small>
        
        <div class="variante-image-upload-area" data-variante-id="${varianteId}" style="
          border: 2px dashed #d1d5db;
          border-radius: 8px;
          padding: 20px;
          text-align: center;
          background: #fafafa;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-top: 8px;
        ">
          <input type="file" 
                 class="variante-image-input"
                 data-variante-id="${varianteId}"
                 name="variante_imagen_${varianteId}" 
                 accept="image/*" 
                 multiple 
                 style="display: none;" />
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="display: block; margin: 0 auto 8px;">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <span style="font-size: 13px; color: #6b7280;">Arrastra imágenes o haz clic</span>
        </div>
        
        <!-- Miniaturas de imágenes de la variante -->
        <div class="variante-thumbnails-grid" data-variante-id="${varianteId}" style="
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
          gap: 8px;
          margin-top: 8px;
        ">
          <!-- Las miniaturas se generarán con JavaScript -->
        </div>
        <small class="variante-image-count" data-variante-id="${varianteId}" style="color: #9ca3af; display: block; margin-top: 6px;">(0/5)</small>
      </div>
    `;
    return row;
  }

  // ➕ Añadir fila de talla
  addTallaBtn.addEventListener('click', () => {
    const newRow = crearFilaTalla();
    tallasContainer.appendChild(newRow);
    
    // 🖼️ Configurar manejadores de imágenes para la nueva variante
    const varianteId = newRow.id.replace('variante-row-', '');
    configurarImagenesVariante(varianteId);
  });

  // 🖼️ Almacenar imágenes de variantes por ID
  const varianteImagesMap = new Map(); // { varianteId: [files] }
  
  // Función para configurar imágenes de una variante
  function configurarImagenesVariante(varianteId) {
    // Inicializar array si no existe
    if (!varianteImagesMap.has(varianteId)) {
      varianteImagesMap.set(varianteId, []);
    }
    
    const fileInput = document.querySelector(`.variante-image-input[data-variante-id="${varianteId}"]`);
    const uploadArea = document.querySelector(`.variante-image-upload-area[data-variante-id="${varianteId}"]`);
    const thumbnailsGrid = document.querySelector(`.variante-thumbnails-grid[data-variante-id="${varianteId}"]`);
    
    if (!fileInput || !uploadArea) return;
    
    // ─────── MANEJO DE MÚLTIPLES IMÁGENES ─────
    
    function actualizarMiniaturasDEVariante() {
      const images = varianteImagesMap.get(varianteId) || [];
      thumbnailsGrid.innerHTML = '';
      
      images.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const div = document.createElement('div');
          div.className = 'thumbnail-item';
          div.style.position = 'relative';
          div.style.borderRadius = '6px';
          div.style.overflow = 'hidden';
          div.style.backgroundColor = '#e0e0e0';
          div.style.aspectRatio = '1';
          
          const img = document.createElement('img');
          img.src = e.target.result;
          img.style.width = '100%';
          img.style.height = '100%';
          img.style.objectFit = 'cover';
          
          const removeBtn = document.createElement('button');
          removeBtn.type = 'button';
          removeBtn.className = 'thumbnail-remove';
          removeBtn.innerHTML = '×';
          removeBtn.style.position = 'absolute';
          removeBtn.style.top = '2px';
          removeBtn.style.right = '2px';
          removeBtn.style.width = '24px';
          removeBtn.style.height = '24px';
          removeBtn.style.borderRadius = '50%';
          removeBtn.style.backgroundColor = 'rgba(0,0,0,0.6)';
          removeBtn.style.color = 'white';
          removeBtn.style.border = 'none';
          removeBtn.style.cursor = 'pointer';
          removeBtn.style.fontSize = '16px';
          removeBtn.style.padding = '0';
          removeBtn.style.display = 'flex';
          removeBtn.style.alignItems = 'center';
          removeBtn.style.justifyContent = 'center';
          removeBtn.style.fontWeight = 'bold';
          
          removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const currentImages = varianteImagesMap.get(varianteId) || [];
            currentImages.splice(index, 1);
            varianteImagesMap.set(varianteId, currentImages);
            actualizarMiniaturasDEVariante();
          });
          
          removeBtn.addEventListener('mouseover', () => {
            removeBtn.style.backgroundColor = 'rgba(0,0,0,0.8)';
          });
          removeBtn.addEventListener('mouseout', () => {
            removeBtn.style.backgroundColor = 'rgba(0,0,0,0.6)';
          });
          
          div.appendChild(img);
          div.appendChild(removeBtn);
          thumbnailsGrid.appendChild(div);
        };
        reader.readAsDataURL(file);
      });
      
      // Actualizar contador
      const countSpan = document.querySelector(`.variante-image-count[data-variante-id="${varianteId}"]`);
      if (countSpan) {
        countSpan.textContent = `(${images.length}/5)`;
      }
    }
    
    function agregarImagenesVariante(files) {
      const currentImages = varianteImagesMap.get(varianteId) || [];
      files.forEach(file => {
        if (currentImages.length < 5 && file.type.startsWith('image/')) {
          currentImages.push(file);
        }
      });
      varianteImagesMap.set(varianteId, currentImages);
      actualizarMiniaturasDEVariante();
      fileInput.value = '';
    }
    
    // Manejador de cambio de input
    fileInput.addEventListener('change', (e) => {
      const files = Array.from(e.target.files);
      agregarImagenesVariante(files);
    });
    
    // ───── DRAG AND DROP ─────
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadArea.classList.remove('drag-over');
      const files = Array.from(e.dataTransfer.files);
      agregarImagenesVariante(files);
    });
    
    // Click en el área para abrir selector
    uploadArea.addEventListener('click', () => {
      const currentImages = varianteImagesMap.get(varianteId) || [];
      if (currentImages.length < 5) {
        fileInput.click();
      }
    });
  }

  // ❌ Eliminar fila
  tallasContainer.addEventListener('click', e => {
    if (e.target.classList.contains('removeTalla')) {
      const rows = tallasContainer.querySelectorAll('.talla-row');
      if (rows.length > 1) {
        const row = e.target.closest('.talla-row');
        const varianteId = row.id.replace('variante-row-', '');
        // Limpiar imágenes de esta variante
        varianteImagesMap.delete(varianteId);
        row.remove();
      } else {
        toast('Debe haber al menos una variante', 'error');
      }
    }
  });

  // 🔃 Cargar categorías desde API con JWT
  (async () => {
    try {
      const urlCategorias = form.dataset.catsUrl;
      const cats = await authFetchJSON(urlCategorias);

      categoriaSelect.innerHTML = '<option value="">Seleccionar...</option>';
      cats.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.nombre;
        categoriaSelect.appendChild(opt);
      });

      // Agrega una fila de talla por defecto y configura sus imágenes
      tallasContainer.innerHTML = '';
      const firstRow = crearFilaTalla();
      tallasContainer.appendChild(firstRow);
      
      // Configurar imágenes para la primera variante (ID 0)
      configurarImagenesVariante(0);
    } catch (err) {
      toast(err.message, 'error');
    }
  })();

  // 🏷️ Cargar subcategorías cuando seleccionas categoría
  categoriaSelect.addEventListener('change', async (e) => {
    const categoriaId = e.target.value;
    const subcatContainer = document.getElementById('subcategorias-container');
    
    if (!categoriaId) {
      subcatContainer.innerHTML = '<p style="color: #999; font-size: 14px;">Selecciona una categoría primero</p>';
      return;
    }

    try {
      subcatContainer.innerHTML = '<p style="color: #999; font-size: 14px;">Cargando subcategorías...</p>';
      
      const response = await authFetchJSON(`/api/subcategorias-por-categoria/${categoriaId}/`);
      const subcats = response.subcategorias || [];
      
      if (!subcats || subcats.length === 0) {
        subcatContainer.innerHTML = '<p style="color: #999; font-size: 14px;">No hay subcategorías para esta categoría</p>';
        return;
      }

      subcatContainer.innerHTML = '';
      subcats.forEach(subcat => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        label.innerHTML = `
          <input type="checkbox" name="subcategorias" value="${subcat.id}" />
          <span class="checkmark"></span>
          <span class="label-text">${subcat.nombre}</span>
        `;
        subcatContainer.appendChild(label);
      });
    } catch (err) {
      console.error('Error cargando subcategorías:', err);
      subcatContainer.innerHTML = '<p style="color: #d32f2f; font-size: 14px;">Error cargando subcategorías</p>';
      toast('Error al cargar subcategorías: ' + err.message, 'error');
    }
  });

  // 🚀 Enviar formulario con JWT
  form.addEventListener('submit', async e => {
    e.preventDefault();
    mensaje.textContent = '';
    mensaje.className = 'form-message';

    const submitBtn = form.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<div class="spinner-small"></div> Guardando...';
    submitBtn.disabled = true;

    const formData = new FormData(form);
    
    // 🖼️ Agregar todas las imágenes de VARIANTES
    varianteImagesMap.forEach((files, varianteId) => {
      files.forEach((file) => {
        formData.append(`variante_imagen_temp_${varianteId}`, file);
      });
    });

    try {
      const resp = await authFetch(form.getAttribute('action'), {
        method: 'POST',
        body: formData
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Error desconocido');

      mensaje.className = 'form-message success';
      mensaje.textContent = `✅ Producto #${data.id} creado con éxito`;
      toast('Producto creado correctamente', 'success');

      // Reset del formulario
      form.reset();
      varianteImagesMap.clear();
      varianteCount = 0;

      // Dejar una fila vacía de tallas
      tallasContainer.innerHTML = '';
      const firstRow = crearFilaTalla();
      tallasContainer.appendChild(firstRow);
      configurarImagenesVariante(0);

    } catch (err) {
      mensaje.className = 'form-message error';
      mensaje.textContent = `❌ ${err.message}`;
      toast(err.message, 'error');
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
