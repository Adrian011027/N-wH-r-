/**
 * DASHBOARD - Gestión de Órdenes
 * JavaScript para cargar, filtrar y gestionar órdenes
 */

let ordenesData = [];
let debounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  cargarOrdenes();
});

// Debounce para el filtro de cliente
function debounceCargar() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(cargarOrdenes, 400);
}

async function cargarOrdenes() {
  mostrarEstado('loading');
  
  try {
    // Construir query params
    const params = new URLSearchParams();
    
    const status = document.getElementById('filtro-status').value;
    const cliente = document.getElementById('filtro-cliente').value;
    const desde = document.getElementById('filtro-desde').value;
    const hasta = document.getElementById('filtro-hasta').value;
    
    if (status) params.append('status', status);
    if (cliente) params.append('cliente', cliente);
    if (desde) params.append('desde', desde);
    if (hasta) params.append('hasta', hasta);
    
    const url = `/api/admin/ordenes/${params.toString() ? '?' + params.toString() : ''}`;
    
    const response = await authFetch(url);
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Error al cargar órdenes');
    }
    
    ordenesData = data.ordenes;
    
    // Actualizar estadísticas
    actualizarStats(data.stats);
    
    if (data.ordenes.length === 0) {
      mostrarEstado('empty');
      return;
    }
    
    renderOrdenes(data.ordenes);
    mostrarEstado('table');
    
  } catch (error) {
    console.error('Error:', error);
    document.getElementById('error-message').textContent = error.message;
    mostrarEstado('error');
  }
}

function mostrarEstado(estado) {
  document.getElementById('loading-state').style.display = 'none';
  document.getElementById('error-state').style.display = 'none';
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('ordenes-container').style.display = 'none';
  
  switch (estado) {
    case 'loading':
      document.getElementById('loading-state').style.display = 'block';
      break;
    case 'error':
      document.getElementById('error-state').style.display = 'block';
      break;
    case 'empty':
      document.getElementById('empty-state').style.display = 'block';
      break;
    case 'table':
      document.getElementById('ordenes-container').style.display = 'block';
      break;
  }
}

function actualizarStats(stats) {
  document.getElementById('stat-total').textContent = stats.total || 0;
  document.getElementById('stat-pendientes').textContent = stats.pendientes || 0;
  document.getElementById('stat-procesando').textContent = stats.procesando || 0;
  document.getElementById('stat-enviados').textContent = stats.enviados || 0;
  document.getElementById('stat-entregados').textContent = stats.entregados || 0;
}

function renderOrdenes(ordenes) {
  const tbody = document.getElementById('ordenes-tbody');
  tbody.innerHTML = '';
  
  ordenes.forEach(orden => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>#${orden.id}</strong></td>
      <td>
        <div class="cliente-info">
          <span class="cliente-nombre">${orden.cliente.nombre}</span>
          <span class="cliente-email">${orden.cliente.correo || orden.cliente.username}</span>
        </div>
      </td>
      <td>
        <div class="productos-preview">
          ${renderProductosPreview(orden.items)}
          <span class="productos-count">${orden.total_items} artículo${orden.total_items > 1 ? 's' : ''}</span>
        </div>
      </td>
      <td class="orden-total">$${orden.total_amount.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
      <td>
        <span class="estado-badge ${normalizeStatus(orden.status)}">${getStatusText(orden.status)}</span>
      </td>
      <td class="orden-fecha">${orden.created_at}</td>
      <td>
        <div class="acciones-cell">
          <button class="btn-accion" onclick="verDetalle(${orden.id})">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" 
                 stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            Ver
          </button>
          <div class="estado-dropdown">
            <button class="estado-dropdown-btn" onclick="toggleDropdown(${orden.id})">
              Cambiar
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" 
                   stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M6 9l6 6 6-6"/>
              </svg>
            </button>
            <div id="dropdown-${orden.id}" class="estado-dropdown-menu">
              <div class="estado-option ${orden.status === 'pendiente' ? 'active' : ''}" 
                   onclick="cambiarEstado(${orden.id}, 'pendiente')">
                🟡 Pendiente
              </div>
              <div class="estado-option ${normalizeStatus(orden.status) === 'procesando' ? 'active' : ''}" 
                   onclick="cambiarEstado(${orden.id}, 'procesando')">
                🔵 Procesando
              </div>
              <div class="estado-option ${orden.status === 'enviado' ? 'active' : ''}" 
                   onclick="cambiarEstado(${orden.id}, 'enviado')">
                🟣 Enviado
              </div>
              <div class="estado-option ${orden.status === 'entregado' ? 'active' : ''}" 
                   onclick="cambiarEstado(${orden.id}, 'entregado')">
                🟢 Entregado
              </div>
              <div class="estado-option ${orden.status === 'cancelado' ? 'active' : ''}" 
                   onclick="cambiarEstado(${orden.id}, 'cancelado')">
                🔴 Cancelado
              </div>
            </div>
          </div>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderProductosPreview(items) {
  const maxShow = 3;
  let html = '';
  
  items.slice(0, maxShow).forEach(item => {
    if (item.producto_imagen) {
      html += `<div class="producto-mini"><img src="${item.producto_imagen}" alt=""></div>`;
    } else {
      html += `<div class="producto-mini" style="display:flex;align-items:center;justify-content:center;color:#ccc;">
        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
        </svg>
      </div>`;
    }
  });
  
  return html;
}

function normalizeStatus(status) {
  if (status === 'proces') return 'procesando';
  return status.toLowerCase();
}

function getStatusText(status) {
  const map = {
    'pendiente': 'Pendiente',
    'pendiente_pago': 'Pago Pendiente',
    'pagado': 'Pagado',
    'procesando': 'Procesando',
    'proces': 'Procesando',
    'enviado': 'Enviado',
    'entregado': 'Entregado',
    'cancelado': 'Cancelado',
    'rechazado': 'Rechazado',
    'reembolsado': 'Reembolsado',
    'expirado': 'Expirado',
    'revision': 'En Revisión',
    'revisión': 'En Revisión'
  };
  return map[status.toLowerCase()] || status;
}

// Dropdown de estado
function toggleDropdown(ordenId) {
  // Cerrar todos los demás
  document.querySelectorAll('.estado-dropdown-menu').forEach(menu => {
    if (menu.id !== `dropdown-${ordenId}`) {
      menu.classList.remove('open');
    }
  });
  
  const menu = document.getElementById(`dropdown-${ordenId}`);
  menu.classList.toggle('open');
}

// Cerrar dropdowns al hacer clic fuera
document.addEventListener('click', (e) => {
  if (!e.target.closest('.estado-dropdown')) {
    document.querySelectorAll('.estado-dropdown-menu').forEach(menu => {
      menu.classList.remove('open');
    });
  }
});

// Cambiar estado
async function cambiarEstado(ordenId, nuevoEstado) {
  try {
    const response = await authFetch(`/api/admin/ordenes/${ordenId}/estado/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nuevoEstado })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Error al cambiar estado');
    }
    
    // Cerrar dropdown
    document.querySelectorAll('.estado-dropdown-menu').forEach(menu => {
      menu.classList.remove('open');
    });
    
    // Mostrar toast
    showToast(`✅ Orden #${ordenId} actualizada a "${getStatusText(nuevoEstado)}"`, 'success');
    
    // Recargar
    cargarOrdenes();
    
  } catch (error) {
    console.error('Error:', error);
    showToast(`❌ ${error.message}`, 'error');
  }
}

// Ver detalle
function verDetalle(ordenId) {
  const orden = ordenesData.find(o => o.id === ordenId);
  if (!orden) return;
  
  document.getElementById('modal-orden-id').textContent = `#${orden.id}`;
  
  const modalBody = document.getElementById('modal-body');
  modalBody.innerHTML = `
    <!-- Info general -->
    <div class="modal-section">
      <h3>Información del Pedido</h3>
      <div class="info-grid">
        <div class="info-item">
          <label>Fecha</label>
          <span>${orden.created_at}</span>
        </div>
        <div class="info-item">
          <label>Método de Pago</label>
          <span>${formatPaymentMethod(orden.payment_method)}</span>
        </div>
        <div class="info-item">
          <label>Estado</label>
          <span class="estado-badge ${normalizeStatus(orden.status)}">${getStatusText(orden.status)}</span>
        </div>
        <div class="info-item">
          <label>Total Artículos</label>
          <span>${orden.total_items}</span>
        </div>
      </div>
    </div>
    
    <!-- Cliente -->
    <div class="modal-section">
      <h3>Cliente</h3>
      <div class="info-grid">
        <div class="info-item">
          <label>Nombre</label>
          <span>${orden.cliente.nombre}</span>
        </div>
        <div class="info-item">
          <label>Usuario</label>
          <span>@${orden.cliente.username}</span>
        </div>
        <div class="info-item">
          <label>Email</label>
          <span>${orden.cliente.correo || 'No proporcionado'}</span>
        </div>
        <div class="info-item">
          <label>Teléfono</label>
          <span>${orden.cliente.telefono || 'No proporcionado'}</span>
        </div>
      </div>
      ${orden.cliente.direccion ? `
        <div class="info-item" style="margin-top: 12px;">
          <label>Dirección de envío</label>
          <span>${orden.cliente.direccion}</span>
        </div>
      ` : ''}
    </div>
    
    <!-- Productos -->
    <div class="modal-section">
      <h3>Productos</h3>
      <div class="modal-productos">
        ${orden.items.map(item => `
          <div class="modal-producto">
            <div class="modal-producto-img">
              ${item.producto_imagen 
                ? `<img src="${item.producto_imagen}" alt="${item.producto_nombre}">`
                : `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" 
                       stroke="#ccc" stroke-width="1.5" viewBox="0 0 24 24" style="margin:18px auto;display:block;">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                  </svg>`
              }
            </div>
            <div class="modal-producto-info">
              <h4 class="modal-producto-nombre">${item.producto_nombre}</h4>
              <p class="modal-producto-attrs">
                ${[item.talla ? `Talla: ${item.talla}` : '', item.color && item.color !== 'N/A' ? `Color: ${item.color}` : ''].filter(Boolean).join(' · ') || 'Sin variantes'}
              </p>
              <div class="modal-producto-precio">
                <span class="qty">${item.cantidad} × $${item.precio_unitario.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                <span class="subtotal">$${item.subtotal.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
      
      <div class="modal-total">
        <span class="label">Total del Pedido</span>
        <span class="amount">$${orden.total_amount.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
      </div>
    </div>
    
    <!-- Cambiar estado -->
    <div class="modal-section">
      <h3>Cambiar Estado</h3>
      <div class="cambiar-estado-section">
        <button class="btn-estado pendiente ${normalizeStatus(orden.status) === 'pendiente' ? 'active' : ''}" 
                onclick="cambiarEstadoModal(${orden.id}, 'pendiente')">
          🟡 Pendiente
        </button>
        <button class="btn-estado procesando ${normalizeStatus(orden.status) === 'procesando' ? 'active' : ''}" 
                onclick="cambiarEstadoModal(${orden.id}, 'procesando')">
          🔵 Procesando
        </button>
        <button class="btn-estado enviado ${normalizeStatus(orden.status) === 'enviado' ? 'active' : ''}" 
                onclick="cambiarEstadoModal(${orden.id}, 'enviado')">
          🟣 Enviado
        </button>
        <button class="btn-estado entregado ${normalizeStatus(orden.status) === 'entregado' ? 'active' : ''}" 
                onclick="cambiarEstadoModal(${orden.id}, 'entregado')">
          🟢 Entregado
        </button>
        <button class="btn-estado cancelado ${normalizeStatus(orden.status) === 'cancelado' ? 'active' : ''}" 
                onclick="cambiarEstadoModal(${orden.id}, 'cancelado')">
          🔴 Cancelado
        </button>
      </div>
    </div>
  `;
  
  document.getElementById('orden-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

async function cambiarEstadoModal(ordenId, nuevoEstado) {
  await cambiarEstado(ordenId, nuevoEstado);
  cerrarModal();
}

function cerrarModal() {
  document.getElementById('orden-modal').classList.remove('open');
  document.body.style.overflow = '';
}

// Cerrar modal con Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    cerrarModal();
  }
});

// Cerrar modal haciendo clic fuera
document.getElementById('orden-modal')?.addEventListener('click', (e) => {
  if (e.target.id === 'orden-modal') {
    cerrarModal();
  }
});

function formatPaymentMethod(method) {
  const methods = {
    'efectivo': 'Efectivo',
    'tarjeta': 'Tarjeta',
    'transferencia': 'Transferencia',
    'sin_especificar': 'No especificado'
  };
  return methods[method] || method;
}

function limpiarFiltros() {
  document.getElementById('filtro-status').value = '';
  document.getElementById('filtro-cliente').value = '';
  document.getElementById('filtro-desde').value = '';
  document.getElementById('filtro-hasta').value = '';
  cargarOrdenes();
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}
