/* variantes-edit.js – Gestión de variantes en editar producto */

document.addEventListener('DOMContentLoaded', () => {
  const addVarianteBtn = document.getElementById('addVariante');
  const variantesContainer = document.querySelector('.variantes-edit-container');

  if (addVarianteBtn && variantesContainer) {
    addVarianteBtn.addEventListener('click', (e) => {
      e.preventDefault();
      agregarVariante();
    });
  }

  function agregarVariante() {
    // Crear ID temporal basado en timestamp
    const tempId = `new-${Date.now()}`;
    
    const newVarianteCard = document.createElement('div');
    newVarianteCard.className = 'variante-edit-card';
    newVarianteCard.dataset.newVariante = 'true';
    newVarianteCard.dataset.tempId = tempId;
    newVarianteCard.innerHTML = `
      <input type="hidden" name="variante_id" value="${tempId}">
      
      <div class="variante-fields-full">
        <div class="variante-field">
          <label>Color</label>
          <input type="text" name="variante_color_${tempId}" 
                 placeholder="Ej: Negro, Rojo">
        </div>
        
        <div class="variante-field">
          <label>Precio</label>
          <div class="input-with-icon small">
            <span class="input-icon">$</span>
            <input type="number" name="variante_precio_${tempId}" step="0.01" min="0">
          </div>
        </div>
        
        <div class="variante-field">
          <label>Mayorista</label>
          <div class="input-with-icon small">
            <span class="input-icon">$</span>
            <input type="number" name="variante_precio_mayorista_${tempId}" step="0.01" min="0">
          </div>
        </div>
        
        <div class="variante-field" style="grid-column: 1 / -1;">
          <label>Tallas y Stock <small style="font-weight:normal;color:#6b7280;">(formato: {"talla": stock})</small></label>
          <textarea name="variante_tallas_stock_${tempId}" 
                    rows="2" style="font-family: monospace; font-size: 13px; width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px;"
                    placeholder='{"38": 5, "39": 10}' required></textarea>
        </div>
      </div>

      <!-- Galería de imágenes de la variante -->
      <div class="variante-gallery" data-variante-id="${tempId}">
        <div class="gallery-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          Galería de la variante (<span class="var-img-count">0/5</span>)
        </div>

        <div class="variante-gallery-grid">
          <!-- Imágenes existentes (ninguna para nuevas variantes) -->
          <div class="var-thumbnails"></div>

          <!-- Área de carga -->
          <div class="var-upload-area">
            <input type="file" class="var-image-input" data-variante-id="${tempId}" accept="image/*" multiple />
            <div class="var-upload-placeholder">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              <small>Agregar imágenes</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Botón para eliminar variante (solo nuevas) -->
      <button type="button" class="btn-remove-variante" style="margin-top: 12px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
        Eliminar variante
      </button>
    `;

    // Insertar antes del botón de agregar
    variantesContainer.insertBefore(newVarianteCard, addVarianteBtn);

    // Inicializar objeto de galería PRIMERO (antes de setupVariantGallery)
    if (!window.variantGalleries) {
      window.variantGalleries = {};
    }
    window.variantGalleries[tempId] = {
      newImages: [],
      imagesToDelete: new Set()
    };

    // Inicializar galería para esta nueva variante
    if (window.setupVariantGallery) {
      const galleryEl = newVarianteCard.querySelector('.variante-gallery');
      window.setupVariantGallery(galleryEl, tempId);
    }

    // Event listener para eliminar variante
    const removeBtn = newVarianteCard.querySelector('.btn-remove-variante');
    removeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      newVarianteCard.remove();
      // Limpiar datos de galería
      delete window.variantGalleries[tempId];
      toast('Variante eliminada', 'warning');
    });

    toast('Nueva variante agregada', 'success');
  }
});
