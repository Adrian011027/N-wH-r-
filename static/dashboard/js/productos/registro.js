// registro.js – Dashboard alta producto con JWT (Diseño Moderno)
document.addEventListener('DOMContentLoaded', () => {
  const form            = document.getElementById('productoForm');
  const mensaje         = document.getElementById('mensaje');
  const tallasContainer = document.getElementById('tallasContainer');
  const addTallaBtn     = document.getElementById('addTalla');
  const categoriaSelect = document.querySelector('select[name="categoria_id"]');
  const subcategoriasSelect = document.getElementById('subcategorias');
  const imageInput      = document.getElementById('imagen');
  const imagePreview    = document.getElementById('imagePreview');
  const uploadArea      = document.getElementById('imageUploadArea');

  // 🖼️ Preview de múltiples imágenes
  if (imageInput) {
    imageInput.addEventListener('change', (e) => {
      const files = Array.from(e.target.files).slice(0, 5); // Máximo 5 imágenes
      const previewsContainer = document.getElementById('imagePreviews');
      
      if (files.length > 5) {
        toast('Máximo 5 imágenes permitidas', 'warning');
      }
      
      previewsContainer.innerHTML = '';
      
      files.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (event) => {
          const div = document.createElement('div');
          div.className = 'image-preview-item';
          div.innerHTML = `
            <img src="${event.target.result}" alt="Vista previa ${index + 1}">
            <span class="preview-order">${index + 1}</span>
          `;
          previewsContainer.appendChild(div);
        };
        reader.readAsDataURL(file);
      });
      
      if (files.length > 0) {
        uploadArea.querySelector('.upload-placeholder').style.display = 'none';
      }
    });
  }

  // 📂 Cargar subcategorías cuando cambia la categoría
  if (categoriaSelect && subcategoriasSelect) {
    categoriaSelect.addEventListener('change', async () => {
      const categoriaId = categoriaSelect.value;
      console.log('📂 Categoría seleccionada:', categoriaId);
      subcategoriasSelect.innerHTML = '<option value="" disabled>Cargando...</option>';

      if (!categoriaId) {
        subcategoriasSelect.innerHTML = '<option value="" disabled>Primero selecciona una categoría</option>';
        return;
      }

      try {
        // Usar fetch normal ya que este endpoint no requiere JWT
        const resp = await fetch(`/api/subcategorias/?categoria_id=${categoriaId}`);
        const data = await resp.json();
        console.log('📦 Subcategorías recibidas:', data);

        subcategoriasSelect.innerHTML = '';

        if (!data || data.length === 0) {
          subcategoriasSelect.innerHTML = '<option value="" disabled>No hay subcategorías para esta categoría</option>';
          return;
        }

        data.forEach(sub => {
          const opt = document.createElement('option');
          opt.value = sub.id;
          opt.textContent = sub.nombre;
          subcategoriasSelect.appendChild(opt);
        });
      } catch (err) {
        console.error('Error cargando subcategorías:', err);
        subcategoriasSelect.innerHTML = '<option value="" disabled>Error al cargar subcategorías</option>';
      }
    });
  }

  // 🔁 Función que crea una fila nueva de talla + stock + imágenes
  function crearFilaTalla() {
    const rowCount = tallasContainer.querySelectorAll('.talla-row').length;
    const row = document.createElement('div');
    row.classList.add('talla-row');
    row.dataset.index = rowCount;
    row.innerHTML = `
      <div class="talla-row-main">
        <label>
          Talla
          <input type="text" name="tallas" required placeholder="Ej. 39" />
        </label>
        <label>
          Stock
          <input type="number" name="stocks" min="0" required placeholder="10" />
        </label>
        <button type="button" class="btn-show-images" title="Agregar imágenes a esta talla">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          Imágenes
        </button>
        <button type="button" class="removeTalla">✕</button>
      </div>
      <div class="talla-images-section" style="display: none;">
        <div class="image-upload-area-variant">
          <input type="file" name="variante_imagenes_${rowCount}" class="variant-images" accept="image/*" multiple />
          <div class="upload-placeholder-variant">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>Imágenes de esta talla (máximo 5)</span>
          </div>
          <div class="image-previews-variant"></div>
        </div>
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
    
    // Mostrar/ocultar sección de imágenes
    if (e.target.closest('.btn-show-images')) {
      e.preventDefault();
      const section = e.target.closest('.talla-row').querySelector('.talla-images-section');
      section.style.display = section.style.display === 'none' ? 'block' : 'none';
    }
  });

  // Preview de imágenes en variantes
  tallasContainer.addEventListener('change', e => {
    if (e.target.classList.contains('variant-images')) {
      const files = Array.from(e.target.files).slice(0, 5);
      const previewsContainer = e.target.closest('.image-upload-area-variant').querySelector('.image-previews-variant');
      
      if (files.length > 5) {
        toast('Máximo 5 imágenes por talla', 'warning');
      }
      
      previewsContainer.innerHTML = '';
      
      files.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (event) => {
          const div = document.createElement('div');
          div.className = 'image-preview-item';
          div.innerHTML = `
            <img src="${event.target.result}" alt="Vista previa ${index + 1}">
            <span class="preview-order">${index + 1}</span>
          `;
          previewsContainer.appendChild(div);
        };
        reader.readAsDataURL(file);
      });
      
      if (files.length > 0) {
        e.target.closest('.image-upload-area-variant').querySelector('.upload-placeholder-variant').style.display = 'none';
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

      // Agrega una fila de talla por defecto
      tallasContainer.innerHTML = '';
      tallasContainer.appendChild(crearFilaTalla());
    } catch (err) {
      toast(err.message, 'error');
    }
  })();

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
      const previewsContainer = document.getElementById('imagePreviews');
      if (previewsContainer) {
        previewsContainer.innerHTML = '';
        uploadArea.querySelector('.upload-placeholder').style.display = 'flex';
      }

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
