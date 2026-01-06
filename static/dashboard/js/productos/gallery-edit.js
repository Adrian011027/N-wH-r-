/* gallery-edit.js - Manejo de galería en página de edición */

// Variables globales para la galería
window.galleryManager = {
  newImages: [],
  imagesToDelete: new Set(),
  
  updateGlobalState() {
    window.galleryDataToSubmit = {
      newImages: this.newImages,
      imagesToDelete: Array.from(this.imagesToDelete)
    };
    console.log('Gallery state updated:', window.galleryDataToSubmit);
  },
  
  addImage(file) {
    // Contar imágenes existentes + nuevas
    const existingCount = document.querySelectorAll('.thumbnail-item-edit[data-image-id]:not([style*="opacity"])').length;
    const totalImages = existingCount + this.newImages.length;
    
    if (totalImages >= 5) {
      toast('⚠️ Ya tienes 5 imágenes. Elimina al menos una para agregar más.', 'warning');
      return;
    }

    if (!file.type.startsWith('image/')) {
      toast('Por favor selecciona un archivo de imagen válido', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const imageData = {
        src: e.target.result,
        file: file,
        isNew: true,
        id: `new_${Date.now()}_${Math.random()}`
      };
      this.newImages.push(imageData);
      this.updateGlobalState();
      this.renderThumbnails();
      this.updateCount();
    };
    reader.readAsDataURL(file);
  },
  
  deleteImage(imageId) {
    if (imageId.startsWith('new_')) {
      this.newImages = this.newImages.filter(img => img.id !== imageId);
    } else {
      this.imagesToDelete.add(parseInt(imageId));
    }

    const thumbnail = document.querySelector(`[data-image-id="${imageId}"]`);
    if (thumbnail) {
      thumbnail.style.opacity = '0';
      setTimeout(() => thumbnail.remove(), 200);
    }

    this.updateGlobalState();
    this.updateCount();
  },
  
  renderThumbnails() {
    const grid = document.querySelector('.thumbnails-grid-edit');
    if (!grid) return;

    // Agregar solo las nuevas imágenes al DOM
    this.newImages.forEach((img) => {
      const exists = document.querySelector(`[data-image-id="${img.id}"]`);
      if (!exists) {
        const div = document.createElement('div');
        div.className = 'thumbnail-item-edit';
        div.setAttribute('data-image-id', img.id);
        div.innerHTML = `
          <img src="${img.src}" alt="Nueva imagen" />
          <div class="thumbnail-overlay">
            <button type="button" class="btn-delete-existing" data-image-id="${img.id}" title="Eliminar imagen">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        `;
        grid.appendChild(div);
      }
    });

    // Asignar event listeners a TODOS los botones de eliminar (existentes y nuevos)
    this.attachDeleteListeners();
  },
  
  attachDeleteListeners() {
    document.querySelectorAll('.btn-delete-existing').forEach(btn => {
      // Remover listener anterior si existe para evitar duplicados
      btn.replaceWith(btn.cloneNode(true));
    });
    
    // Agregar listeners nuevos
    document.querySelectorAll('.btn-delete-existing').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        window.galleryManager.deleteImage(btn.dataset.imageId);
      });
    });
  },
  
  updateCount() {
    const countEl = document.getElementById('imageCount');
    if (countEl) {
      const existingCount = document.querySelectorAll('.thumbnail-item-edit[data-image-id]:not([style*="display: none"])').length;
      const deleted = Array.from(this.imagesToDelete).length;
      const total = (existingCount - deleted) + this.newImages.length;
      countEl.textContent = `${total}/5`;
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const galeriaInput = document.getElementById('galeriaInput');
  const uploadAreaEdit = document.querySelector('.upload-area-edit');
  
  if (!galeriaInput || !uploadAreaEdit) return;

  // Evento change del input de archivo
  galeriaInput.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      for (let file of files) {
        window.galleryManager.addImage(file);
      }
      galeriaInput.value = '';
    }
  });

  // Drag and drop
  uploadAreaEdit.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadAreaEdit.classList.add('dragover');
  });

  uploadAreaEdit.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadAreaEdit.classList.remove('dragover');
  });

  uploadAreaEdit.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadAreaEdit.classList.remove('dragover');
    const files = e.dataTransfer.files;
    for (let file of files) {
      if (file.type.startsWith('image/')) {
        window.galleryManager.addImage(file);
      }
    }
  });

  // Click en el área para abrir explorador
  uploadAreaEdit.addEventListener('click', (e) => {
    // Validar ANTES de abrir el explorador
    const existingCount = document.querySelectorAll('.thumbnail-item-edit[data-image-id]:not([style*="opacity"])').length;
    const totalImages = existingCount + window.galleryManager.newImages.length;
    
    if (totalImages >= 5) {
      toast('⚠️ Ya tienes 5 imágenes. Elimina al menos una para agregar más.', 'warning');
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
    
    galeriaInput.click();
  });

  // Inicializar galleryDataToSubmit y asignar listeners a imágenes existentes
  window.galleryManager.updateGlobalState();
  window.galleryManager.attachDeleteListeners();
});
