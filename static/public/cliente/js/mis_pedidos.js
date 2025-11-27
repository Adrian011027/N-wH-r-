/**
 * MIS PEDIDOS - JavaScript
 * Carga y muestra el historial de pedidos del cliente
 */

document.addEventListener('DOMContentLoaded', () => {
  initPedidos();
});

function initPedidos() {
  const isLogged = !!localStorage.getItem('access');
  
  if (!isLogged) {
    mostrarEstado('not-logged');
    return;
  }
  
  cargarPedidos();
}

async function cargarPedidos() {
  mostrarEstado('loading');
  
  try {
    const token = localStorage.getItem('access');
    const response = await fetch('/api/cliente/ordenes/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 401) {
      // Token expirado
      mostrarEstado('not-logged');
      return;
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Error al cargar pedidos');
    }
    
    if (data.ordenes.length === 0) {
      mostrarEstado('empty');
      return;
    }
    
    renderPedidos(data.ordenes);
    mostrarEstado('list');
    
  } catch (error) {
    console.error('Error:', error);
    document.getElementById('error-message').textContent = error.message;
    mostrarEstado('error');
  }
}

function mostrarEstado(estado) {
  const estados = ['loading', 'empty', 'error', 'not-logged'];
  
  estados.forEach(e => {
    const el = document.getElementById(`${e === 'loading' ? 'loading-state' : e === 'empty' ? 'empty-state' : e === 'error' ? 'error-state' : e}`);
    if (el) el.style.display = 'none';
  });
  
  document.getElementById('pedidos-list').style.display = 'none';
  
  switch (estado) {
    case 'loading':
      document.getElementById('loading-state').style.display = 'flex';
      break;
    case 'empty':
      document.getElementById('empty-state').style.display = 'block';
      break;
    case 'error':
      document.getElementById('error-state').style.display = 'block';
      break;
    case 'not-logged':
      document.getElementById('not-logged').style.display = 'block';
      break;
    case 'list':
      document.getElementById('pedidos-list').style.display = 'flex';
      break;
  }
}

function renderPedidos(ordenes) {
  const container = document.getElementById('pedidos-list');
  container.innerHTML = '';
  
  ordenes.forEach(orden => {
    const card = crearOrdenCard(orden);
    container.appendChild(card);
  });
}

function crearOrdenCard(orden) {
  const card = document.createElement('div');
  card.className = 'orden-card';
  
  // Preparar productos preview (máx 4)
  const productosPreview = orden.items.slice(0, 4);
  const masProductos = orden.items.length > 4 ? orden.items.length - 4 : 0;
  
  card.innerHTML = `
    <div class="orden-header">
      <div class="orden-info">
        <span class="orden-id">Pedido #${orden.id}</span>
        <span class="orden-fecha">${orden.created_at}</span>
      </div>
      <span class="orden-status" style="background: ${orden.status_display.color}15; color: ${orden.status_display.color}">
        ${getStatusIcon(orden.status_display.icon)}
        ${orden.status_display.text}
      </span>
    </div>
    
    <div class="orden-productos">
      ${productosPreview.map(item => `
        <div class="producto-thumb">
          ${item.producto_imagen 
            ? `<img src="${item.producto_imagen}" alt="${item.producto_nombre}">`
            : `<div class="producto-thumb-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" 
                     stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <path d="M21 15l-5-5L5 21"/>
                </svg>
              </div>`
          }
          ${item.cantidad > 1 ? `<span class="producto-cantidad">×${item.cantidad}</span>` : ''}
        </div>
      `).join('')}
      ${masProductos > 0 ? `<div class="mas-productos">+${masProductos}</div>` : ''}
    </div>
    
    <div class="orden-footer">
      <div class="orden-total">
        <span>Total:</span> $${orden.total_amount.toLocaleString('es-MX', {minimumFractionDigits: 2})}
      </div>
      <div class="orden-actions">
        <button class="btn-ver-detalle" onclick="verDetalle(${orden.id})">Ver detalle</button>
      </div>
    </div>
  `;
  
  // Guardar datos para el modal
  card.dataset.orden = JSON.stringify(orden);
  
  return card;
}

function getStatusIcon(icon) {
  const icons = {
    clock: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`,
    settings: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
    truck: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="1" y="3" width="15" height="13"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`,
    check: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>`,
    x: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>`,
    info: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>`
  };
  return icons[icon] || icons.info;
}

function verDetalle(ordenId) {
  // Buscar la orden en las cards
  const cards = document.querySelectorAll('.orden-card');
  let ordenData = null;
  
  cards.forEach(card => {
    const data = JSON.parse(card.dataset.orden);
    if (data.id === ordenId) {
      ordenData = data;
    }
  });
  
  if (!ordenData) return;
  
  // Llenar modal
  document.getElementById('modal-orden-id').textContent = `#${ordenData.id}`;
  
  const modalBody = document.getElementById('modal-body');
  modalBody.innerHTML = `
    <!-- Timeline de estado -->
    <div class="modal-section">
      <h3>Estado del pedido</h3>
      ${renderTimeline(ordenData.status)}
    </div>
    
    <!-- Info del pedido -->
    <div class="modal-section">
      <h3>Información</h3>
      <div class="modal-info-grid">
        <div class="modal-info-item">
          <label>Fecha</label>
          <span>${ordenData.created_at}</span>
        </div>
        <div class="modal-info-item">
          <label>Método de pago</label>
          <span>${formatPaymentMethod(ordenData.payment_method)}</span>
        </div>
        <div class="modal-info-item">
          <label>Productos</label>
          <span>${ordenData.total_items} artículo${ordenData.total_items > 1 ? 's' : ''}</span>
        </div>
        <div class="modal-info-item">
          <label>Estado</label>
          <span style="color: ${ordenData.status_display.color}">${ordenData.status_display.text}</span>
        </div>
      </div>
    </div>
    
    <!-- Productos -->
    <div class="modal-section">
      <h3>Productos</h3>
      <div class="modal-productos">
        ${ordenData.items.map(item => `
          <div class="modal-producto">
            <div class="modal-producto-img">
              ${item.producto_imagen 
                ? `<img src="${item.producto_imagen}" alt="${item.producto_nombre}">`
                : `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" 
                       stroke="#ccc" stroke-width="1.5" viewBox="0 0 24 24" style="margin: 24px auto; display: block;">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <path d="M21 15l-5-5L5 21"/>
                  </svg>`
              }
            </div>
            <div class="modal-producto-info">
              <h4 class="modal-producto-nombre">${item.producto_nombre}</h4>
              <p class="modal-producto-attrs">
                ${item.atributos.map(a => `${a.nombre}: ${a.valor}`).join(' · ') || 'Sin variantes'}
              </p>
              <div class="modal-producto-precio">
                <span>${item.cantidad} × $${item.precio_unitario.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                <span>$${item.subtotal.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
    
    <!-- Total -->
    <div class="modal-total">
      <span>Total del pedido</span>
      <span>$${ordenData.total_amount.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
    </div>
  `;
  
  // Abrir modal
  document.getElementById('orden-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function renderTimeline(status) {
  const steps = [
    { key: 'pendiente', label: 'Pendiente', icon: 'clock' },
    { key: 'procesando', label: 'Procesando', icon: 'settings' },
    { key: 'enviado', label: 'Enviado', icon: 'truck' },
    { key: 'entregado', label: 'Entregado', icon: 'check' }
  ];
  
  const statusNormalized = status.toLowerCase();
  let currentIndex = steps.findIndex(s => s.key === statusNormalized || (statusNormalized === 'proces' && s.key === 'procesando'));
  if (currentIndex === -1) currentIndex = 0;
  
  return `
    <div class="status-timeline">
      ${steps.map((step, index) => {
        let className = 'timeline-step';
        if (index < currentIndex) className += ' completed';
        if (index === currentIndex) className += ' active';
        
        return `
          <div class="${className}">
            <div class="timeline-dot">
              ${getStatusIcon(step.icon)}
            </div>
            <span class="timeline-label">${step.label}</span>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function formatPaymentMethod(method) {
  const methods = {
    'efectivo': 'Efectivo',
    'tarjeta': 'Tarjeta',
    'transferencia': 'Transferencia',
    'sin_especificar': 'No especificado'
  };
  return methods[method] || method;
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
