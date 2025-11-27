// registro.js – Dashboard alta producto con JWT (Diseño Moderno)
document.addEventListener('DOMContentLoaded', () => {
  const form            = document.getElementById('productoForm');
  const mensaje         = document.getElementById('mensaje');
  const tallasContainer = document.getElementById('tallasContainer');
  const addTallaBtn     = document.getElementById('addTalla');
  const categoriaSelect = document.querySelector('select[name="categoria_id"]');
  const imageInput      = document.getElementById('imagen');
  const imagePreview    = document.getElementById('imagePreview');
  const uploadArea      = document.getElementById('imageUploadArea');

  // 🖼️ Preview de imagen
  if (imageInput && imagePreview) {
    imageInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          imagePreview.src = e.target.result;
          imagePreview.style.display = 'block';
          uploadArea.querySelector('.upload-placeholder').style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // 🔁 Función que crea una fila nueva de talla + stock
  function crearFilaTalla() {
    const row = document.createElement('div');
    row.classList.add('talla-row');
    row.innerHTML = `
      <label>
        Talla
        <input type="text" name="tallas" required placeholder="Ej. 39" />
      </label>
      <label>
        Stock
        <input type="number" name="stocks" min="0" required placeholder="10" />
      </label>
      <button type="button" class="removeTalla">✕</button>
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
  (async () => {
    try {
      const urlCategorias = form.dataset.catsUrl;
      const token = localStorage.getItem('access');
      if (!token) throw new Error('No tienes sesión activa');

      const res = await fetch(urlCategorias, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('No se pudo obtener la lista de categorías');
      const cats = await res.json();

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
    const token = localStorage.getItem('access');
    
    if (!token) {
      mensaje.className = 'form-message error';
      mensaje.textContent = '❌ No tienes sesión iniciada.';
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
      return;
    }

    try {
      const resp = await fetch(form.getAttribute('action'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Error desconocido');

      mensaje.className = 'form-message success';
      mensaje.textContent = `✅ Producto #${data.id} creado con éxito`;
      toast('Producto creado correctamente', 'success');

      // Reset del formulario
      form.reset();
      if (imagePreview) {
        imagePreview.style.display = 'none';
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
