// ═══════════════════════════════════════════════════════════════
// Funcionalidad para AÑADIR NUEVA VARIANTE desde el modal de edición
// ═══════════════════════════════════════════════════════════════

function mostrarFormularioNuevaVariante() {
  if (!productoActual) {
    showToast('No hay producto cargado', 'error');
    return;
  }

  const container = document.getElementById('variantesContainer');
  
  // Verificar si ya hay un formulario abierto
  if (document.getElementById('formNuevaVariante')) {
    showToast('Ya hay un formulario de variante abierto', 'warning');
    return;
  }

  // HTML del formulario para nueva variante
  const formHTML = `
    <div class="variante-detalle-card nueva-variante-form" id="formNuevaVariante" style="border: 2px solid #3b82f6; background: #eff6ff;">
      <div class="var-det-header" style="background: #dbeafe;">
        <div class="var-det-title">
          <span style="font-weight: 600; color: #1e40af;">➕ Nueva Variante</span>
        </div>
        <button type="button" class="btn-danger-sm" onclick="cancelarNuevaVariante()" title="Cancelar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
          Cancelar
        </button>
      </div>
      
      <div class="var-det-body">
        <div class="var-det-form">
          <div class="form-group-det-small">
            <label>Color <span style="color: red;">*</span></label>
            <input type="text" class="form-input-sm" id="nuevaVarColor" placeholder="Negro, Blanco, Rojo..." required>
          </div>
          <div class="form-group-det-small">
            <label>SKU (opcional)</label>
            <input type="text" class="form-input-sm" id="nuevaVarSKU" placeholder="SKU-001">
          </div>
        </div>
        
        <div class="tallas-det-section">
          <label class="label-det-strong">Tallas y Stock</label>
          <div class="tallas-det-grid" id="nuevaVarTallasGrid">
            <div class="talla-input-row">
              <input type="text" placeholder="Talla" class="talla-label-det" style="width: 80px;" id="nuevaVarTallaInput">
              <input type="number" min="0" placeholder="Stock" class="talla-input-det" id="nuevaVarStockInput">
              <button type="button" class="btn btn-outline btn-sm" onclick="agregarTallaNuevaVariante()">
                + Añadir
              </button>
            </div>
          </div>
          <div id="nuevaVarTallasLista" style="margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem;">
            <!-- Aquí se mostrarán las tallas añadidas -->
          </div>
        </div>
        
        <div class="imagenes-det-section">
          <label class="label-det-strong">Imágenes (opcional, hasta 5)</label>
          <div class="var-det-imgs-grid" id="nuevaVarImagenesPreview">
            <div class="var-det-upload-box">
              <input type="file" class="input-file-hidden" id="nuevaVarImagenesInput" 
                     accept="image/*" multiple onchange="previsualizarImagenesNuevaVariante(this)">
              <label for="nuevaVarImagenesInput" class="upload-label-det">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <span>Seleccionar</span>
              </label>
            </div>
          </div>
        </div>
        
        <button type="button" class="btn btn-primary" style="width: 100%; margin-top: 1rem;" 
                onclick="guardarNuevaVariante()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
            <polyline points="17 21 17 13 7 13 7 21"></polyline>
            <polyline points="7 3 7 8 15 8"></polyline>
          </svg>
          Crear Variante
        </button>
      </div>
    </div>
  `;
  
  // Insertar el formulario al inicio del container
  container.insertAdjacentHTML('afterbegin', formHTML);
  
  // Focus en el campo de color
  document.getElementById('nuevaVarColor').focus();
  
  // Scroll al formulario
  document.getElementById('formNuevaVariante').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Variable global para almacenar las tallas temporales
let tallasNuevaVariante = {};

function agregarTallaNuevaVariante() {
  const tallaInput = document.getElementById('nuevaVarTallaInput');
  const stockInput = document.getElementById('nuevaVarStockInput');
  
  const talla = tallaInput.value.trim();
  const stock = parseInt(stockInput.value) || 0;
  
  if (!talla) {
    showToast('Ingresa una talla', 'warning');
    return;
  }
  
  if (stock < 0) {
    showToast('El stock no puede ser negativo', 'error');
    return;
  }
  
  // Agregar a la lista temporal
  tallasNuevaVariante[talla] = stock;
  
  // Limpiar inputs
  tallaInput.value = '';
  stockInput.value = '';
  tallaInput.focus();
  
  // Actualizar la vista
  actualizarVistaTallasNuevaVariante();
}

function actualizarVistaTallasNuevaVariante() {
  const lista = document.getElementById('nuevaVarTallasLista');
  
  if (Object.keys(tallasNuevaVariante).length === 0) {
    lista.innerHTML = '<span class="text-muted-sm">No hay tallas añadidas</span>';
    return;
  }
  
  lista.innerHTML = Object.entries(tallasNuevaVariante).map(([talla, stock]) => `
    <span class="badge" style="background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; display: flex; align-items: center; gap: 0.25rem;">
      ${esc(talla)}: ${stock}
      <button onclick="eliminarTallaNuevaVariante('${escJS(talla)}')" style="background: none; border: none; color: white; cursor: pointer; padding: 0; margin-left: 0.25rem;">×</button>
    </span>
  `).join('');
}

function eliminarTallaNuevaVariante(talla) {
  delete tallasNuevaVariante[talla];
  actualizarVistaTallasNuevaVariante();
}

function previsualizarImagenesNuevaVariante(input) {
  const preview = document.getElementById('nuevaVarImagenesPreview');
  const files = Array.from(input.files);
  
  if (files.length > 5) {
    showToast('Máximo 5 imágenes permitidas', 'warning');
    input.value = '';
    return;
  }
  
  // Limpiar preview anterior (mantener el botón de upload)
  const uploadBox = preview.querySelector('.var-det-upload-box');
  preview.innerHTML = '';
  
  // Agregar previews
  files.forEach((file, idx) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const div = document.createElement('div');
      div.className = 'var-det-img-item';
      div.innerHTML = `<img src="${e.target.result}" alt="Preview ${idx + 1}">`;
      preview.appendChild(div);
    };
    reader.readAsDataURL(file);
  });
  
  // Re-agregar el botón de upload
  preview.appendChild(uploadBox);
}

async function guardarNuevaVariante() {
  if (!productoActual) {
    showToast('No hay producto seleccionado', 'error');
    return;
  }
  
  const color = document.getElementById('nuevaVarColor').value.trim();
  const sku = document.getElementById('nuevaVarSKU').value.trim();
  const imagenesInput = document.getElementById('nuevaVarImagenesInput');
  
  // Validaciones
  if (!color) {
    showToast('El color es obligatorio', 'error');
    document.getElementById('nuevaVarColor').focus();
    return;
  }
  
  if (Object.keys(tallasNuevaVariante).length === 0) {
    showToast('Añade al menos una talla con stock', 'error');
    return;
  }
  
  // Preparar FormData
  const formData = new FormData();
  formData.append('producto_id', productoActual.id);
  formData.append('color', color);
  if (sku) formData.append('sku', sku);
  formData.append('tallas_stock', JSON.stringify(tallasNuevaVariante));
  
  // Agregar imágenes si hay
  if (imagenesInput.files.length > 0) {
    Array.from(imagenesInput.files).forEach((file, idx) => {
      formData.append(`imagenes_${idx}`, file);
    });
  }
  
  // Enviar petición
  try {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Creando...';
    
    const res = await fetch('/api/variantes/create/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      },
      body: formData
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error || 'Error al crear variante');
    }
    
    showToast(`Variante "${color}" creada exitosamente`, 'success');
    
    // Cancelar formulario
    cancelarNuevaVariante();
    
    // Recargar los datos del producto
    await cargarDetallesProducto(productoActual.id);
    
  } catch (err) {
    showToast(err.message, 'error');
    const btn = document.querySelector('#formNuevaVariante button[onclick="guardarNuevaVariante()"]');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
          <polyline points="17 21 17 13 7 13 7 21"></polyline>
          <polyline points="7 3 7 8 15 8"></polyline>
        </svg>
        Crear Variante
      `;
    }
  }
}

function cancelarNuevaVariante() {
  const form = document.getElementById('formNuevaVariante');
  if (form) {
    form.remove();
  }
  // Limpiar variables temporales
  tallasNuevaVariante = {};
}
