/**
 * crear.js - Lógica para crear productos desde el módulo de inventario
 * Reutiliza el endpoint existente POST /api/productos/crear/
 */

document.addEventListener('DOMContentLoaded', () => {
  // Preview de imágenes
  const fileInput = document.getElementById('var_imagenes');
  const previewGrid = document.getElementById('previewImagenes');

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      previewGrid.innerHTML = '';
      const files = Array.from(fileInput.files).slice(0, 5);
      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const img = document.createElement('img');
          img.src = e.target.result;
          previewGrid.appendChild(img);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  // Submit formulario
  const form = document.getElementById('formCrearProducto');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await crearProducto();
    });
  }
});

function agregarFilaTalla() {
  const container = document.getElementById('tallasStockContainer');
  const row = document.createElement('div');
  row.className = 'talla-row';
  row.innerHTML = `
    <input type="text" name="talla[]" placeholder="Talla (ej: 38, M)" class="input-talla">
    <input type="number" name="stock[]" placeholder="Stock" min="0" value="0" class="input-stock">
    <button type="button" class="btn-icon btn-delete-sm" onclick="this.closest('.talla-row').remove()">✕</button>
  `;
  container.appendChild(row);
  row.querySelector('.input-talla').focus();
}

async function crearProducto() {
  const btn = document.getElementById('btnCrear');
  btn.disabled = true;
  btn.textContent = 'Creando...';

  try {
    // Recolectar tallas y stock
    const tallaInputs = document.querySelectorAll('input[name="talla[]"]');
    const stockInputs = document.querySelectorAll('input[name="stock[]"]');
    const tallasStock = {};
    tallaInputs.forEach((input, i) => {
      const talla = input.value.trim();
      if (talla) {
        tallasStock[talla] = parseInt(stockInputs[i]?.value) || 0;
      }
    });

    // Subcategorías seleccionadas
    const subcategorias = Array.from(
      document.querySelectorAll('input[name="subcategorias"]:checked')
    ).map(cb => parseInt(cb.value));

    // Construir FormData para enviar imágenes
    const formData = new FormData();
    formData.append('nombre', document.getElementById('nombre').value.trim());
    formData.append('descripcion', document.getElementById('descripcion').value.trim());
    formData.append('precio', document.getElementById('precio').value);
    formData.append('precio_mayorista', document.getElementById('precio_mayorista').value || '0');
    formData.append('categoria_id', document.getElementById('categoria').value);
    formData.append('genero', document.getElementById('genero').value);
    formData.append('marca', document.getElementById('marca').value.trim());
    formData.append('color', document.getElementById('var_color').value.trim() || 'N/A');
    formData.append('sku', document.getElementById('var_sku').value.trim());
    formData.append('tallas_stock', JSON.stringify(tallasStock));
    formData.append('subcategorias', JSON.stringify(subcategorias));

    // Imágenes
    const fileInput = document.getElementById('var_imagenes');
    if (fileInput.files.length > 0) {
      Array.from(fileInput.files).slice(0, 5).forEach(file => {
        formData.append('imagenes', file);
      });
    }

    const csrfToken = getCsrf();
    const accessToken = localStorage.getItem('inv_access');

    const res = await fetch('/api/productos/crear/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Authorization': `Bearer ${accessToken}`
      },
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Error al crear producto');
    }

    showToast('Producto creado exitosamente');
    setTimeout(() => {
      window.location.href = '/inventario/';
    }, 1000);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Crear Producto';
  }
}

function showToast(message, type = 'success') {
  const existing = document.querySelector('.inv-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `inv-toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function getCsrf() {
  let v = null;
  if (document.cookie) {
    document.cookie.split(';').forEach(c => {
      c = c.trim();
      if (c.startsWith('csrftoken=')) {
        v = decodeURIComponent(c.substring(10));
      }
    });
  }
  return v || '';
}
