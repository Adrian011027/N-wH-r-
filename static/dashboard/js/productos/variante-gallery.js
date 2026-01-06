/* variante-gallery.js – Gestión de galerías para variantes */

document.addEventListener('DOMContentLoaded', () => {
  // Objeto global para almacenar datos de variantes
  if (!window.variantGalleries) {
    window.variantGalleries = {};
  }

  // Exponer la función de setup globalmente para que variantes-edit.js pueda usarla
  window.setupVariantGallery = setupVariantGallery;

  // Inicializar cada galería de variante existente
  document.querySelectorAll('.variante-gallery').forEach(galleryEl => {
    const varianteId = galleryEl.dataset.varianteId;
    
    // Inicializar objeto para esta variante si no existe
    if (!window.variantGalleries[varianteId]) {
      window.variantGalleries[varianteId] = {
        newImages: [],
        imagesToDelete: new Set()
      };
    }

    setupVariantGallery(galleryEl, varianteId);
  });

  function setupVariantGallery(galleryEl, varianteId) {
    const fileInput = galleryEl.querySelector('.var-image-input');
    const uploadArea = galleryEl.querySelector('.var-upload-placeholder');
    const thumbsContainer = galleryEl.querySelector('.var-thumbnails');
    const countSpan = galleryEl.querySelector('.var-img-count');
    const MAX_IMAGES = 5;

    console.log(`[Variante ${varianteId}] Inicializando galería`, { fileInput, uploadArea, thumbsContainer });

    // Event listener para el input de archivo
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        console.log(`[Variante ${varianteId}] Archivos seleccionados:`, e.target.files.length);
        handleFileSelection(e.target.files, varianteId, galleryEl);
        // Reset el input después de procesar
        setTimeout(() => {
          fileInput.value = '';
        }, 100);
      });
    }

    // Drag and drop
    if (uploadArea) {
      uploadArea.addEventListener('click', () => {
        if (fileInput) fileInput.click();
      });
      
      uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = '#f0f4ff';
      });

      uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#d1d5db';
        uploadArea.style.background = '#f9fafb';
      });

      uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#d1d5db';
        uploadArea.style.background = '#f9fafb';
        console.log(`[Variante ${varianteId}] Archivos por drag-drop:`, e.dataTransfer.files.length);
        handleFileSelection(e.dataTransfer.files, varianteId, galleryEl);
      });
    }

    // Event delegado para botones de eliminar
    if (thumbsContainer) {
      thumbsContainer.addEventListener('click', (e) => {
        if (e.target.closest('.btn-delete-var-img')) {
          e.preventDefault();
          const btn = e.target.closest('.btn-delete-var-img');
          const imageId = btn.dataset.imageId;
          const thumbItem = btn.closest('.var-thumb-item');

          if (imageId) {
            // Imagen existente - marcar para eliminar
            window.variantGalleries[varianteId].imagesToDelete.add(imageId);
            thumbItem.style.opacity = '0.5';
            btn.disabled = true;
            toast(`Imagen marcada para eliminar`, 'warning');
          } else {
            // Imagen nueva - simplemente quitar del array
            const idx = Array.from(thumbsContainer.querySelectorAll('.var-thumb-item')).indexOf(thumbItem);
            if (idx >= 0) {
              window.variantGalleries[varianteId].newImages.splice(idx, 1);
              updateVariantGalleryUI(galleryEl, varianteId);
            }
          }
          updateImageCount(galleryEl, varianteId);
        }
      });
    }

    // Actualizar UI inicial
    updateVariantGalleryUI(galleryEl, varianteId);
  }

  function handleFileSelection(files, varianteId, galleryEl) {
    const gallery = window.variantGalleries[varianteId];
    const thumbsContainer = galleryEl.querySelector('.var-thumbnails');
    const MAX_IMAGES = 5;
    
    // Contar imágenes existentes
    const existingCount = galleryEl.querySelectorAll('.var-thumb-item[data-image-id]').length;
    const currentNewCount = gallery.newImages.length;
    let totalCount = existingCount + currentNewCount;

    console.log(`[Variante ${varianteId}] Procesando ${files.length} archivos. Existentes: ${existingCount}, Nuevas: ${currentNewCount}, Total: ${totalCount}`);

    Array.from(files).forEach((file, fileIdx) => {
      if (totalCount >= MAX_IMAGES) {
        toast(`Máximo ${MAX_IMAGES} imágenes permitidas por variante`, 'error');
        return;
      }

      if (!file.type.startsWith('image/')) {
        toast('Solo se permiten archivos de imagen', 'error');
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        toast('La imagen no puede exceder 5MB', 'error');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        console.log(`[Variante ${varianteId}] Imagen ${fileIdx + 1} cargada`);
        gallery.newImages.push({
          file: file,
          src: e.target.result
        });
        totalCount++;
        updateVariantGalleryUI(galleryEl, varianteId);
      };
      reader.onerror = () => {
        console.error(`[Variante ${varianteId}] Error al leer archivo ${fileIdx + 1}`);
        toast('Error al leer la imagen', 'error');
      };
      reader.readAsDataURL(file);
    });
  }

  function updateVariantGalleryUI(galleryEl, varianteId) {
    const gallery = window.variantGalleries[varianteId];
    const thumbsContainer = galleryEl.querySelector('.var-thumbnails');
    const countSpan = galleryEl.querySelector('.var-img-count');
    const uploadArea = galleryEl.querySelector('.var-upload-placeholder');

    // Renderizar nuevas imágenes con previsualización
    const newImgElements = thumbsContainer.querySelectorAll('[data-new-image]');
    newImgElements.forEach(el => el.remove());

    gallery.newImages.forEach((imgData, idx) => {
      const div = document.createElement('div');
      div.className = 'var-thumb-item';
      div.setAttribute('data-new-image', 'true');
      div.innerHTML = `
        <img src="${imgData.src}" alt="Nueva imagen ${idx + 1}">
        <button type="button" class="btn-delete-var-img" title="Eliminar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      `;
      thumbsContainer.appendChild(div);
    });

    updateImageCount(galleryEl, varianteId);
  }

  function updateImageCount(galleryEl, varianteId) {
    const gallery = window.variantGalleries[varianteId];
    const countSpan = galleryEl.querySelector('.var-img-count');
    const existingCount = galleryEl.querySelectorAll('.var-thumb-item[data-image-id]').length;
    const newCount = gallery.newImages.length;
    const totalCount = existingCount + newCount;
    
    countSpan.textContent = `${totalCount}/5`;
  }

  // Interceptar el submit del formulario para incluir datos de variantes
  const editForm = document.getElementById('editarForm');
  if (editForm) {
    editForm.addEventListener('submit', (e) => {
      // El código de editar.js ya maneja esto, pero podemos agregar lógica aquí si es necesario
      console.log('Galería de variantes:', window.variantGalleries);
    });
  }
});

