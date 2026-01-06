// registro.js – Dashboard alta producto con JWT (Diseño Moderno)
document.addEventListener('DOMContentLoaded', () => {
  const form              = document.getElementById('productoForm');
  const mensaje           = document.getElementById('mensaje');
  const tallasContainer   = document.getElementById('tallasContainer');
  const addTallaBtn       = document.getElementById('addTalla');
  const categoriaSelect   = document.querySelector('select[name="categoria_id"]');
  const subcategoriasContainer = document.getElementById('subcategorias-container');
  const imageInput        = document.getElementById('imagen');
  const imagePreview      = document.getElementById('imagePreview');
  const uploadArea        = document.getElementById('imageUploadArea');
  const thumbnailsGrid    = document.getElementById('thumbnailsGrid');
  const imageCount        = document.getElementById('imageCount');

  // 🖼️ Almacenamiento de imágenes como DataURLs
  const galleryImages = [];
  const MAX_IMAGES = 5;

  // Función para actualizar contador
  function updateImageCount() {
    imageCount.textContent = `(${galleryImages.length}/${MAX_IMAGES})`;
  }

  // Función para renderizar miniaturas
  function renderThumbnails() {
    if (galleryImages.length === 0) {
      thumbnailsGrid.innerHTML = `
        <div class="empty-gallery">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <p>Sin imágenes</p>
        </div>
      `;
      return;
    }

    thumbnailsGrid.innerHTML = '';
    galleryImages.forEach((imgData, idx) => {
      const thumbnailDiv = document.createElement('div');
      thumbnailDiv.className = 'thumbnail-item';
      thumbnailDiv.innerHTML = `
        <img src="${imgData.src}" alt="Miniatura ${idx + 1}">
        <button type="button" class="thumbnail-remove" data-idx="${idx}" title="Eliminar">
          ✕
        </button>
      `;
      thumbnailsGrid.appendChild(thumbnailDiv);
    });

    // Event listeners para eliminar
    thumbnailsGrid.querySelectorAll('.thumbnail-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const idx = parseInt(btn.dataset.idx);
        galleryImages.splice(idx, 1);
        renderThumbnails();
        updateImageCount();
        resetUploadArea();
      });
    });
  }

  // Función para resetear el área de upload
  function resetUploadArea() {
    imageInput.value = '';
    imagePreview.style.display = 'none';
    uploadArea.querySelector('.upload-placeholder').style.display = 'flex';
  }

  // Función para agregar una imagen a la galería
  function addImageToGallery(file) {
    if (galleryImages.length >= MAX_IMAGES) {
      alert(`Ya has agregado el máximo de ${MAX_IMAGES} imágenes`);
      return false;
    }

    if (!file.type.startsWith('image/')) {
      alert('Por favor selecciona un archivo de imagen válido');
      return false;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      galleryImages.push({
        src: e.target.result,
        file: file,
        name: file.name
      });
      renderThumbnails();
      updateImageCount();
      resetUploadArea();
    };
    reader.readAsDataURL(file);
    return true;
  }

  // 🖼️ Manejo de input de imagen
  if (imageInput) {
    imageInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        addImageToGallery(file);
      }
    });

    // 🎯 Drag and drop support
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        const file = files[0];
        addImageToGallery(file);
      }
    });
  }

  // Inicializar contador
  updateImageCount();

  // 🔁 Función que crea una fila nueva con 5 campos de variante
  function crearFilaTalla() {
    const idx = Date.now(); // Usar timestamp como ID único temporal
    const row = document.createElement('div');
    row.classList.add('talla-row');
    row.innerHTML = `
      <div class="variante-fields-full">
        <div class="variante-field">
          <label>Talla</label>
          <input type="text" name="tallas" required placeholder="Ej. 39, M, L, XL" />
        </div>
        <div class="variante-field">
          <label>Color</label>
          <input type="text" name="colores" placeholder="Ej. Negro, Rojo" />
        </div>
        <div class="variante-field">
          <label>Precio</label>
          <div class="input-with-icon small">
            <span class="input-icon">$</span>
            <input type="number" name="precios" step="0.01" min="0" placeholder="0.00" />
          </div>
        </div>
        <div class="variante-field">
          <label>Mayorista</label>
          <div class="input-with-icon small">
            <span class="input-icon">$</span>
            <input type="number" name="precios_mayorista" step="0.01" min="0" placeholder="0.00" />
          </div>
        </div>
        <div class="variante-field">
          <label>Stock</label>
          <input type="number" name="stocks" min="0" required placeholder="10" />
        </div>
        <button type="button" class="removeTalla">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>
        </button>
      </div>
    `;
    return row;
  }

  // ➕ Añadir fila de talla
  addTallaBtn.addEventListener('click', () => {
    tallasContainer.appendChild(crearFilaTalla());
  });

  // ❌ Eliminar fila
  tallasContainer.addEventListener('click', e => {
    if (e.target.classList.contains('removeTalla')) {
      const rows = tallasContainer.querySelectorAll('.talla-row');
      if (rows.length > 1) {
        e.target.closest('.talla-row').remove();
      } else {
        toast('Debe haber al menos una variante', 'error');
      }
    }
  });

  // 🔃 Cargar categorías desde API con JWT
  async function cargarCategorias() {
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

      // Agrega una fila de talla por defecto
      tallasContainer.innerHTML = '';
      tallasContainer.appendChild(crearFilaTalla());
    } catch (err) {
      console.error('Error cargando categorías:', err);
      toast(err.message, 'error');
    }
  }

  // 📂 Función para cargar subcategorías
  async function cargarSubcategorias(categoriaId) {
    if (!categoriaId) {
      subcategoriasContainer.innerHTML = '<p style="color: #999; font-size: 14px;">Selecciona una categoría primero</p>';
      return;
    }

    try {
      const response = await authFetch(`/api/subcategorias-por-categoria/${categoriaId}/`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

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
    } catch (err) {
      console.error(`Error cargando subcategorías:`, err);
      toast(`Error cargando subcategorías: ${err.message}`, 'error');
      subcategoriasContainer.innerHTML = '<p style="color: #e74c3c; font-size: 14px;">Error cargando subcategorías</p>';
    }
  }

  // Event listener para cambios en categoría
  categoriaSelect.addEventListener('change', (e) => {
    cargarSubcategorias(e.target.value);
  });

  // Inicializar categorías
  cargarCategorias();

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

    // ➕ Agregar imágenes adicionales de la galería
    galleryImages.forEach((imgData, idx) => {
      formData.append(`imagen_galeria_${idx}`, imgData.file);
    });

    try {
      const resp = await authFetch(form.getAttribute('action'), {
        method: 'POST',
        body: formData
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Error desconocido');

      mensaje.className = 'form-message success';
      mensaje.textContent = `✅ Producto #${data.id} creado con éxito (${galleryImages.length} imágenes adicionales)`;
      toast('Producto creado correctamente', 'success');

      // Reset del formulario
      form.reset();
      galleryImages.length = 0;
      resetUploadArea();
      renderThumbnails();
      updateImageCount();

      // Dejar una fila vacía
      tallasContainer.innerHTML = '';
      tallasContainer.appendChild(crearFilaTalla());

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
