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
    const uploadArea = galleryEl.querySelector('.var-upload-area');
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
        console.log(`[Variante ${varianteId}] Click en área de upload, intentando abrir file input`);
        if (fileInput) {
          fileInput.click();
        } else {
          console.error(`[Variante ${varianteId}] fileInput no encontrado`);
        }
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
    } else {
      console.error(`[Variante ${varianteId}] uploadArea no encontrada`);
    }

    // Event delegado para botones de eliminar
    if (thumbsContainer) {
      thumbsContainer.addEventListener('click', (e) => {
        if (e.target.closest('.btn-delete-var-img')) {
          e.preventDefault();
          e.stopPropagation();
          const btn = e.target.closest('.btn-delete-var-img');
          const imageId = btn.dataset.imageId;
          const thumbItem = btn.closest('.var-thumb-item');

          console.log(`[Variante ${varianteId}] Click en eliminar imagen, ID:`, imageId);

          if (imageId) {
            // Imagen existente - marcar para eliminar
            const imageIdNum = parseInt(imageId);
            console.log(`[Variante ${varianteId}] Marcando imagen ${imageIdNum} para eliminar`);
            window.variantGalleries[varianteId].imagesToDelete.add(imageIdNum);
            console.log(`[Variante ${varianteId}] IDs a eliminar:`, Array.from(window.variantGalleries[varianteId].imagesToDelete));
            
            // Marcar visualmente
            thumbItem.style.opacity = '0.5';
            thumbItem.style.filter = 'grayscale(100%)';
            btn.disabled = true;
            btn.style.cursor = 'not-allowed';
            toast(`Imagen marcada para eliminar`, 'warning');
          } else {
            // Imagen nueva - simplemente quitar del array
            const allNewThumbs = thumbsContainer.querySelectorAll('.var-thumb-item:not([data-image-id])');
            const idx = Array.from(allNewThumbs).indexOf(thumbItem);
            console.log(`[Variante ${varianteId}] Eliminando imagen nueva en índice ${idx}`);
            if (idx >= 0 && idx < window.variantGalleries[varianteId].newImages.length) {
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
    
    // Contar imágenes existentes que NO están marcadas para eliminar
    const existingThumbsAll = galleryEl.querySelectorAll('.var-thumb-item[data-image-id]');
    let existingCount = 0;
    existingThumbsAll.forEach(item => {
      const imgId = parseInt(item.dataset.imageId);
      if (!gallery.imagesToDelete.has(imgId)) {
        existingCount++;
      }
    });
    
    const currentNewCount = gallery.newImages.length;
    const imagesToDeleteCount = gallery.imagesToDelete.size;
    let totalCount = existingCount + currentNewCount;

    console.log(`[Variante ${varianteId}] Procesando ${files.length} archivos.`);
    console.log(`[Variante ${varianteId}] Existentes totales: ${existingThumbsAll.length}, Marcadas para eliminar: ${imagesToDeleteCount}`);
    console.log(`[Variante ${varianteId}] Existentes que quedan: ${existingCount}, Nuevas: ${currentNewCount}`);
    console.log(`[Variante ${varianteId}] Total efectivo: ${totalCount}, Intentando añadir: ${files.length}`);

    Array.from(files).forEach((file, fileIdx) => {
      if (totalCount >= MAX_IMAGES) {
        const espaciosLibres = MAX_IMAGES - totalCount;
        const mensaje = imagesToDeleteCount > 0 
          ? `Máximo ${MAX_IMAGES} imágenes. Tienes ${existingCount} activas + ${currentNewCount} nuevas. ${imagesToDeleteCount} marcadas para eliminar.`
          : `Máximo ${MAX_IMAGES} imágenes permitidas por variante`;
        toast(mensaje, 'error');
        console.warn(`[Variante ${varianteId}] Límite alcanzado. No se puede agregar más imágenes.`);
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
    
    // Contar imágenes existentes que NO están marcadas para eliminar
    const allExisting = galleryEl.querySelectorAll('.var-thumb-item[data-image-id]');
    let existingCount = 0;
    allExisting.forEach(item => {
      const imgId = parseInt(item.dataset.imageId);
      if (!gallery.imagesToDelete.has(imgId)) {
        existingCount++;
      }
    });
    
    const newCount = gallery.newImages.length;
    const totalCount = existingCount + newCount;
    const imagesToDeleteCount = gallery.imagesToDelete.size;
    
    console.log(`[Variante ${varianteId}] Estado de galería:`);
    console.log(`  - Existentes totales: ${allExisting.length}`);
    console.log(`  - Marcadas para eliminar: ${imagesToDeleteCount}`);
    console.log(`  - Existentes que quedan: ${existingCount}`);
    console.log(`  - Nuevas pendientes: ${newCount}`);
    console.log(`  - Total efectivo: ${totalCount}/5`);
    console.log(`  - Espacios disponibles: ${5 - totalCount}`);
    
    if (countSpan) {
      countSpan.textContent = `${totalCount}/5`;
      
      // Añadir indicador visual si hay imágenes marcadas para eliminar
      if (imagesToDeleteCount > 0) {
        countSpan.title = `${totalCount} imágenes activas (${imagesToDeleteCount} marcadas para eliminar)`;
        countSpan.style.color = '#f59e0b'; // Amber para indicar cambios pendientes
      } else {
        countSpan.title = '';
        countSpan.style.color = '';
      }
    }
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

