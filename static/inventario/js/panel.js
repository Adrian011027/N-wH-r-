/**
 * panel.js - Lógica del panel de inventario
 * Maneja filtros, edición de stock, eliminación de variantes.
 */

let currentEditVarianteId = null;
let currentDeleteVarianteId = null;
let debounceTimer = null;

// ───────────────────────────────────────────────
// Toast notifications
// ───────────────────────────────────────────────
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

// ───────────────────────────────────────────────
// Filtros y búsqueda
// ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => aplicarFiltros(), 400);
    });

    // Enter para filtrar inmediato
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        clearTimeout(debounceTimer);
        aplicarFiltros();
      }
    });
  }
});

async function aplicarFiltros() {
  const search = document.getElementById('searchInput').value.trim();
  const categoria = document.getElementById('filterCategoria').value;
  const stock = document.getElementById('filterStock').value;

  const params = new URLSearchParams();
  if (search) params.set('q', search);
  if (categoria) params.set('categoria', categoria);
  if (stock) params.set('stock', stock);

  try {
    const res = await fetch(`/inventario/api/data/?${params.toString()}`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || 'Error al filtrar');
    renderTabla(json.data);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function limpiarFiltros() {
  document.getElementById('searchInput').value = '';
  document.getElementById('filterCategoria').value = '';
  document.getElementById('filterStock').value = '';
  aplicarFiltros();
}

function renderTabla(data) {
  const tbody = document.getElementById('inventarioBody');
  if (!data.length) {
    tbody.innerHTML = `
      <tr><td colspan="9" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
        </svg>
        <p>No se encontraron resultados</p>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(item => {
    const tallasHTML = Object.entries(item.tallas_stock || {}).map(([t, s]) => {
      const cls = s === 0 ? 'talla-agotada' : s <= 3 ? 'talla-baja' : '';
      return `<div class="talla-item ${cls}"><span class="talla-label">${esc(t)}</span><span class="talla-stock">${s}</span></div>`;
    }).join('') || '<span class="text-muted">Sin tallas</span>';

    const stockCls = item.stock_total === 0 ? 'stock-cero' : item.stock_total <= 5 ? 'stock-bajo' : 'stock-ok';
    const rowCls = item.stock_total === 0 ? 'row-sin-stock' : item.stock_total <= 5 ? 'row-stock-bajo' : '';

    const imgHTML = item.imagen_url
      ? `<img src="${esc(item.imagen_url)}" alt="${esc(item.producto_nombre)}" class="inv-thumb" loading="lazy">`
      : `<div class="inv-thumb-placeholder"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg></div>`;

    return `
    <tr class="inv-row ${rowCls}" data-variante-id="${item.variante_id}" data-producto-id="${item.producto_id}"
        onclick="abrirDetallesProducto(${item.producto_id})" style="cursor: pointer;">
      <td class="col-img">${imgHTML}</td>
      <td class="col-prod">
        <div class="prod-name">${esc(item.producto_nombre)}</div>
        <div class="prod-meta">
          <span class="genero-tag">${esc(item.genero)}</span>
          ${item.es_principal ? '<span class="principal-tag">Principal</span>' : ''}
        </div>
      </td>
      <td class="col-cat">${esc(item.categoria)}</td>
      <td class="col-marca">${esc(item.marca)}</td>
      <td class="col-sku"><code>${esc(item.sku)}</code></td>
      <td class="col-color"><span class="color-chip">${esc(item.color)}</span></td>
      <td class="col-tallas"><div class="tallas-grid">${tallasHTML}</div></td>
      <td class="col-stock"><span class="stock-badge ${stockCls}">${item.stock_total}</span></td>
      <td class="col-actions" onclick="event.stopPropagation()">
        <button class="btn-icon btn-view" title="Ver detalles" onclick="abrirDetallesProducto(${item.producto_id})">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        </button>
      </td>
    </tr>`;
  }).join('');
}

function esc(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

function escJS(str) {
  return (str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// ───────────────────────────────────────────────
// Modal Editar Stock
// ───────────────────────────────────────────────
function abrirModalEditar(varianteId, productoNombre, color, tallasStock) {
  currentEditVarianteId = varianteId;

  document.getElementById('modalProductoNombre').textContent = productoNombre;
  document.getElementById('modalColor').textContent = color;

  const container = document.getElementById('modalTallasContainer');
  container.innerHTML = '';

  Object.entries(tallasStock || {}).forEach(([talla, stock]) => {
    const row = document.createElement('div');
    row.className = 'modal-talla-row';
    row.innerHTML = `
      <span class="talla-name">${esc(talla)}</span>
      <input type="number" min="0" value="${stock}" data-talla="${esc(talla)}">
      <button class="btn-delete-sm" onclick="this.closest('.modal-talla-row').remove()" title="Quitar talla">✕</button>
    `;
    container.appendChild(row);
  });

  document.getElementById('nuevaTalla').value = '';
  document.getElementById('modalEditar').style.display = 'flex';
}

function agregarTallaModal() {
  const input = document.getElementById('nuevaTalla');
  const talla = input.value.trim();
  if (!talla) return;

  // Verificar que no exista
  const container = document.getElementById('modalTallasContainer');
  const existing = container.querySelectorAll('.talla-name');
  for (const el of existing) {
    if (el.textContent.trim().toLowerCase() === talla.toLowerCase()) {
      showToast('Esa talla ya existe', 'error');
      return;
    }
  }

  const row = document.createElement('div');
  row.className = 'modal-talla-row';
  row.innerHTML = `
    <span class="talla-name">${esc(talla)}</span>
    <input type="number" min="0" value="0" data-talla="${esc(talla)}">
    <button class="btn-delete-sm" onclick="this.closest('.modal-talla-row').remove()" title="Quitar talla">✕</button>
  `;
  container.appendChild(row);
  input.value = '';
  input.focus();
}

function cerrarModal() {
  document.getElementById('modalEditar').style.display = 'none';
  currentEditVarianteId = null;
}

async function guardarStock() {
  if (!currentEditVarianteId) return;

  const btn = document.getElementById('btnGuardarStock');
  btn.disabled = true;
  btn.textContent = 'Guardando...';

  const rows = document.querySelectorAll('#modalTallasContainer .modal-talla-row');
  const tallasStock = {};
  rows.forEach(row => {
    const talla = row.querySelector('.talla-name').textContent.trim();
    const stock = parseInt(row.querySelector('input').value) || 0;
    tallasStock[talla] = stock;
  });

  try {
    const res = await fetch(`/inventario/api/stock/${currentEditVarianteId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf()
      },
      body: JSON.stringify({ tallas_stock: tallasStock })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al guardar');

    showToast('Stock actualizado correctamente');
    cerrarModal();

    // Actualizar la fila en la tabla sin recargar
    const row = document.querySelector(`tr[data-variante-id="${currentEditVarianteId}"]`);
    if (row) {
      // Recargar con filtros actuales
      aplicarFiltros();
    } else {
      location.reload();
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Guardar cambios';
  }
}

// ───────────────────────────────────────────────
// Modal Eliminar Variante
// ───────────────────────────────────────────────
function eliminarVariante(varianteId, productoNombre, color) {
  currentDeleteVarianteId = varianteId;
  document.getElementById('deleteProductoNombre').textContent = productoNombre;
  document.getElementById('deleteColor').textContent = color;
  document.getElementById('modalEliminar').style.display = 'flex';
}

function cerrarModalEliminar() {
  document.getElementById('modalEliminar').style.display = 'none';
  currentDeleteVarianteId = null;
}

async function confirmarEliminar() {
  if (!currentDeleteVarianteId) return;

  const btn = document.getElementById('btnConfirmarEliminar');
  btn.disabled = true;
  btn.textContent = 'Eliminando...';

  try {
    const res = await fetch(`/inventario/api/variante/${currentDeleteVarianteId}/`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': getCsrf() }
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al eliminar');

    showToast(data.message || 'Variante eliminada');
    cerrarModalEliminar();

    // Remover fila de la tabla
    const row = document.querySelector(`tr[data-variante-id="${currentDeleteVarianteId}"]`);
    if (row) {
      row.style.transition = 'opacity 0.3s, transform 0.3s';
      row.style.opacity = '0';
      row.style.transform = 'translateX(20px)';
      setTimeout(() => row.remove(), 300);
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Eliminar';
  }
}

// ───────────────────────────────────────────────
// Utils
// ───────────────────────────────────────────────
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

// Cerrar modales con Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    cerrarModal();
    cerrarModalEliminar();
    cerrarDetalles();
  }
});

// Cerrar modales al hacer clic en overlay
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    cerrarModal();
    cerrarModalEliminar();
    cerrarDetalles();
  }
});

// ═══════════════════════════════════════════════════════════════
// MODAL DE DETALLES COMPLETO
// ═══════════════════════════════════════════════════════════════

let productoActual = null;
let imagenesAEliminar = {}; // { varianteId: [imgId1, imgId2...] }
let imagenesNuevas = {}; // { varianteId: [File1, File2...] }

async function abrirDetallesProducto(productoId) {
  try {
    const res = await fetch(`/inventario/api/producto/${productoId}/`);
    const json = await res.json();
    
    if (!res.ok) throw new Error(json.error || 'Error al cargar producto');
    
    productoActual = json.producto;
    imagenesAEliminar = {};
    imagenesNuevas = {};
    
    // Cargar datos del producto
    document.getElementById('detallesProductoTitulo').textContent = productoActual.nombre;
    document.getElementById('detNombre').value = productoActual.nombre;
    document.getElementById('detMarca').value = productoActual.marca;
    document.getElementById('detDescripcion').value = productoActual.descripcion;
    document.getElementById('detCategoria').value = productoActual.categoria_id || '';
    document.getElementById('detGenero').value = productoActual.genero;
    document.getElementById('detPrecio').value = productoActual.precio;
    document.getElementById('detPrecioMayorista').value = productoActual.precio_mayorista;
    
    // Renderizar variantes
    renderVariantes(productoActual.variantes);
    
    // Mostrar modal
    document.getElementById('modalDetalles').style.display = 'flex';
    
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function cerrarDetalles() {
  document.getElementById('modalDetalles').style.display = 'none';
  productoActual = null;
  imagenesAEliminar = {};
  imagenesNuevas = {};
}

function renderVariantes(variantes) {
  const container = document.getElementById('variantesContainer');
  document.getElementById('variantesCount').textContent = variantes.length;
  
  if (!variantes.length) {
    container.innerHTML = '<p class="text-muted" style="padding: 1rem; text-align: center;">No hay variantes</p>';
    return;
  }
  
  container.innerHTML = variantes.map((v, idx) => {
    const esPrincipal = v.es_variante_principal;
    const tallasHTML = Object.entries(v.tallas_stock || {}).map(([t, s]) => `
      <div class="talla-input-row">
        <span class="talla-label-det">${esc(t)}</span>
        <input type="number" min="0" value="${s}" 
               data-variante-id="${v.id}" data-talla="${esc(t)}" 
               class="talla-input-det">
        <button type="button" class="btn-delete-talla-det" 
                onclick="eliminarTallaDetalle(${v.id}, '${escJS(t)}')" title="Eliminar talla">×</button>
      </div>
    `).join('');
    
    const imagenesHTML = v.imagenes.map(img => `
      <div class="var-det-img-item" data-img-id="${img.id}">
        <img src="${esc(img.url)}" alt="Variante ${esc(v.color)}">
        <button type="button" class="btn-delete-img-det" 
                onclick="marcarImagenParaEliminar(${v.id}, ${img.id})" 
                title="Eliminar imagen">×</button>
      </div>
    `).join('');
    
    return `
      <div class="variante-detalle-card" data-variante-id="${v.id}">
        <div class="var-det-header">
          <div class="var-det-title">
            <span class="color-chip">${esc(v.color)}</span>
            ${esPrincipal ? '<span class="badge badge-blue">Principal</span>' : ''}
            <code class="sku-code">${esc(v.sku)}</code>
          </div>
          ${!esPrincipal ? `
            <button type="button" class="btn-danger-sm" 
                    onclick="eliminarVarianteDetalle(${v.id}, '${escJS(v.color)}')" 
                    title="Eliminar variante">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              Eliminar
            </button>
          ` : '<span class="text-muted-sm">No se puede eliminar la variante principal</span>'}
        </div>
        
        <div class="var-det-body">
          <div class="var-det-form">
            <div class="form-group-det-small">
              <label>Color</label>
              <input type="text" class="form-input-sm" value="${esc(v.color)}" 
                     data-variante-id="${v.id}" data-field="color">
            </div>
            <div class="form-group-det-small">
              <label>SKU</label>
              <input type="text" class="form-input-sm" value="${esc(v.sku)}" 
                     data-variante-id="${v.id}" data-field="sku">
            </div>
          </div>
          
          <div class="tallas-det-section">
            <label class="label-det-strong">Tallas y Stock</label>
            <div class="tallas-det-grid">
              ${tallasHTML}
            </div>
            <div class="agregar-talla-det">
              <input type="text" class="input-nueva-talla-det" 
                     placeholder="Nueva talla (ej: 42)" 
                     id="nuevaTalla_${v.id}">
              <button type="button" class="btn btn-outline btn-sm" 
                      onclick="agregarTallaDetalle(${v.id})">+ Talla</button>
            </div>
          </div>
          
          <div class="imagenes-det-section">
            <label class="label-det-strong">Imágenes <span class="text-muted-sm">(${v.imagenes.length}/5)</span></label>
            <div class="var-det-imgs-grid" id="varImgs_${v.id}">
              ${imagenesHTML}
              <div class="var-det-upload-box">
                <input type="file" class="input-file-hidden" id="fileInput_${v.id}" 
                       accept="image/*" multiple onchange="handleNuevasImagenes(${v.id}, this)">
                <label for="fileInput_${v.id}" class="upload-label-det">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                  </svg>
                  <span>Subir</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function agregarTallaDetalle(varianteId) {
  const input = document.getElementById(`nuevaTalla_${varianteId}`);
  const talla = input.value.trim();
  if (!talla) return;
  
  // Verificar si ya existe
  const card = document.querySelector(`.variante-detalle-card[data-variante-id="${varianteId}"]`);
  const existing = card.querySelectorAll('.talla-label-det');
  for (const el of existing) {
    if (el.textContent.trim().toLowerCase() === talla.toLowerCase()) {
      showToast('Esa talla ya existe en esta variante', 'error');
      return;
    }
  }
  
  // Agregar nueva fila
  const grid = card.querySelector('.tallas-det-grid');
  const newRow = document.createElement('div');
  newRow.className = 'talla-input-row';
  newRow.innerHTML = `
    <span class="talla-label-det">${esc(talla)}</span>
    <input type="number" min="0" value="0" 
           data-variante-id="${varianteId}" data-talla="${esc(talla)}" 
           class="talla-input-det">
    <button type="button" class="btn-delete-talla-det" 
            onclick="eliminarTallaDetalle(${varianteId}, '${escJS(talla)}')" title="Eliminar talla">×</button>
  `;
  grid.appendChild(newRow);
  input.value = '';
}

function eliminarTallaDetalle(varianteId, talla) {
  const card = document.querySelector(`.variante-detalle-card[data-variante-id="${varianteId}"]`);
  const rows = card.querySelectorAll('.talla-input-row');
  
  rows.forEach(row => {
    const label = row.querySelector('.talla-label-det');
    if (label && label.textContent.trim() === talla) {
      row.remove();
    }
  });
}

function marcarImagenParaEliminar(varianteId, imgId) {
  if (!imagenesAEliminar[varianteId]) {
    imagenesAEliminar[varianteId] = [];
  }
  imagenesAEliminar[varianteId].push(imgId);
  
  // Ocultar visualmente
  const imgItem = document.querySelector(`.var-det-img-item[data-img-id="${imgId}"]`);
  if (imgItem) {
    imgItem.style.opacity = '0.3';
    imgItem.style.pointerEvents = 'none';
    const btn = imgItem.querySelector('.btn-delete-img-det');
    if (btn) btn.textContent = '✓';
  }
}

function handleNuevasImagenes(varianteId, input) {
  const files = Array.from(input.files);
  if (!files.length) return;
  
  if (!imagenesNuevas[varianteId]) {
    imagenesNuevas[varianteId] = [];
  }
  
  // Validar límite de 5 imágenes
  const variante = productoActual.variantes.find(v => v.id === varianteId);
  const totalActual = variante.imagenes.length - (imagenesAEliminar[varianteId]?.length || 0);
  const totalNuevas = imagenesNuevas[varianteId].length + files.length;
  
  if (totalActual + totalNuevas > 5) {
    showToast('Máximo 5 imágenes por variante', 'error');
    input.value = '';
    return;
  }
  
  imagenesNuevas[varianteId].push(...files);
  
  // Mostrar preview
  const grid = document.getElementById(`varImgs_${varianteId}`);
  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.createElement('div');
      preview.className = 'var-det-img-item preview-img';
      preview.innerHTML = `
        <img src="${e.target.result}" alt="Preview">
        <span class="badge-new">Nueva</span>
      `;
      // Insertar antes del upload box
      const uploadBox = grid.querySelector('.var-det-upload-box');
      grid.insertBefore(preview, uploadBox);
    };
    reader.readAsDataURL(file);
  });
  
  input.value = '';
}

async function eliminarVarianteDetalle(varianteId, color) {
  if (!confirm(`¿Eliminar la variante de color ${color}? Esta acción no se puede deshacer.`)) {
    return;
  }
  
  try {
    const res = await fetch(`/inventario/api/variante/${varianteId}/`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': getCsrf() }
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al eliminar');
    
    showToast(data.message || 'Variante eliminada');
    
    // Actualizar productoActual
    productoActual.variantes = productoActual.variantes.filter(v => v.id !== varianteId);
    renderVariantes(productoActual.variantes);
    
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function guardarCambiosProducto() {
  if (!productoActual) return;
  
  const btn = document.getElementById('btnGuardarDetalles');
  btn.disabled = true;
  btn.innerHTML = '<svg width="16" height="16" class="spinner">...</svg> Guardando...';
  
  try {
    // 1. Actualizar producto principal
    const formData = new FormData();
    formData.append('nombre', document.getElementById('detNombre').value.trim());
    formData.append('marca', document.getElementById('detMarca').value.trim());
    formData.append('descripcion', document.getElementById('detDescripcion').value.trim());
    formData.append('categoria_id', document.getElementById('detCategoria').value);
    formData.append('genero', document.getElementById('detGenero').value);
    formData.append('precio', document.getElementById('detPrecio').value);
    formData.append('precio_mayorista', document.getElementById('detPrecioMayorista').value);
    
    const resProducto = await fetch(`/api/productos/update/${productoActual.id}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      },
      body: formData
    });
    
    if (!resProducto.ok) {
      const err = await resProducto.json();
      throw new Error(err.error || 'Error al actualizar producto');
    }
    
    // 2. Actualizar cada variante
    for (const varianteOriginal of productoActual.variantes) {
      const card = document.querySelector(`.variante-detalle-card[data-variante-id="${varianteOriginal.id}"]`);
      if (!card) continue;
      
      // Recopilar tallas_stock
      const tallasInputs = card.querySelectorAll('.talla-input-det');
      const tallas_stock = {};
      tallasInputs.forEach(input => {
        const talla = input.dataset.talla;
        const stock = parseInt(input.value) || 0;
        tallas_stock[talla] = stock;
      });
      
      // Recopilar color y sku
      const colorInput = card.querySelector('input[data-field="color"]');
      const skuInput = card.querySelector('input[data-field="sku"]');
      
      const varFormData = new FormData();
      varFormData.append('tallas_stock', JSON.stringify(tallas_stock));
      varFormData.append('color', colorInput.value.trim());
      varFormData.append('sku', skuInput.value.trim());
      
      const resVar = await fetch(`/api/variantes/update/${varianteOriginal.id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrf(),
          'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
        },
        body: varFormData
      });
      
      if (!resVar.ok) {
        const errVar = await resVar.json();
        throw new Error(`Variante ${varianteOriginal.id}: ${errVar.error || 'Error'}`);
      }
    }
    
    showToast('Producto actualizado correctamente');
    cerrarDetalles();
    aplicarFiltros(); // Refrescar tabla
    
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
      </svg>
      Guardar Cambios
    `;
  }
}

async function eliminarProductoCompleto() {
  if (!productoActual) return;
  
  const confirmacion = confirm(`¿ELIMINAR TODO EL PRODUCTO "${productoActual.nombre}"?\n\nEsto eliminará:\n• El producto completo\n• Todas sus variantes (${productoActual.variantes.length})\n• Todas las imágenes\n\nEsta acción NO se puede deshacer.`);
  
  if (!confirmacion) return;
  
  const btn = document.getElementById('btnEliminarProducto');
  btn.disabled = true;
  btn.textContent = 'Eliminando...';
  
  try {
    const res = await fetch(`/api/productos/delete/${productoActual.id}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      }
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al eliminar');
    
    showToast(data.mensaje || 'Producto eliminado completamente');
    cerrarDetalles();
    aplicarFiltros();
    
  } catch (err) {
    showToast(err.message, 'error');
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="3 6 5 6 21 6"></polyline>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
      </svg>
      Eliminar Producto
    `;
  }
}
