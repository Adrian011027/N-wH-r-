/* lista.js – Dashboard de Productos (Diseño Moderno) */

let todosLosProductos = [];
let categorias = new Set();

document.addEventListener('DOMContentLoaded', () => {
  cargarProductos();
  setupFiltros();
});

/* ---------- Helpers JWT ---------- */
function getAccessToken() {
  return localStorage.getItem("access");
}

/* ---------- CARGA Y RENDER ---------- */
async function cargarProductos() {
  const container = document.getElementById('productos-container');
  
  try {
    const res = await fetch('/api/productos/', {
      headers: {
        "Authorization": `Bearer ${getAccessToken()}`,
        "Content-Type": "application/json",
      }
    });
    
    if (!res.ok) throw new Error('Error al obtener productos');
    const productos = await res.json();
    
    todosLosProductos = productos;
    
    // Extraer categorías únicas
    productos.forEach(p => categorias.add(p.categoria));
    llenarSelectCategorias();
    
    // Actualizar estadísticas
    actualizarEstadisticas(productos);
    
    // Renderizar productos
    renderizarProductos(productos);
    
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <h3>Error al cargar</h3>
        <p>${err.message}</p>
      </div>
    `;
  }
}

function actualizarEstadisticas(productos) {
  document.getElementById('stat-total').textContent = productos.length;
  
  const stockTotal = productos.reduce((sum, p) => sum + (p.stock_total || 0), 0);
  document.getElementById('stat-stock').textContent = stockTotal.toLocaleString();
  
  const enOferta = productos.filter(p => p.en_oferta).length;
  document.getElementById('stat-ofertas').textContent = enOferta;
  
  document.getElementById('stat-categorias').textContent = categorias.size;
}

function llenarSelectCategorias() {
  const select = document.getElementById('filtro-categoria');
  categorias.forEach(cat => {
    const option = document.createElement('option');
    option.value = cat;
    option.textContent = cat;
    select.appendChild(option);
  });
}

function renderizarProductos(productos) {
  const container = document.getElementById('productos-container');
  container.innerHTML = '';
  
  if (!productos.length) {
    container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
        </svg>
        <h3>No hay productos</h3>
        <p>Agrega tu primer producto para comenzar</p>
      </div>
    `;
    return;
  }
  
  productos.forEach(p => container.appendChild(crearCard(p)));
}

function crearCard(p) {
  const card = document.createElement('div');
  card.className = 'producto-card';
  card.dataset.id = p.id;
  
  // Calcular precio mínimo de variantes
  let precioMin = 0;
  if (p.variantes?.length) {
    precioMin = Math.min(...p.variantes.map(v => parseFloat(v.precio)));
  }
  
  // Determinar nivel de stock
  let stockClass = 'stock-alto';
  let stockText = `${p.stock_total} en stock`;
  if (p.stock_total === 0) {
    stockClass = 'stock-bajo';
    stockText = 'Sin stock';
  } else if (p.stock_total < 10) {
    stockClass = 'stock-bajo';
    stockText = `¡Solo ${p.stock_total}!`;
  } else if (p.stock_total < 30) {
    stockClass = 'stock-medio';
  }
  
  // Badges
  let badgesHTML = '';
  if (p.en_oferta) {
    badgesHTML += '<span class="badge badge-oferta">🔥 Oferta</span>';
  }
  if (p.genero) {
    badgesHTML += `<span class="badge badge-genero">${capitalizar(p.genero)}</span>`;
  }
  
  card.innerHTML = `
    <div class="producto-imagen">
      <img src="${p.imagen || '/static/images/no-image.png'}" alt="${p.nombre}" loading="lazy">
      <div class="producto-badges">
        ${badgesHTML}
      </div>
      <span class="stock-indicator ${stockClass}">${stockText}</span>
    </div>
    
    <div class="producto-content">
      <span class="producto-categoria">${p.categoria || 'Sin categoría'}</span>
      <h3 class="producto-nombre">${p.nombre}</h3>
      <p class="producto-descripcion">${p.descripcion || 'Sin descripción'}</p>
      
      <div class="producto-precios">
        <span class="precio-actual">$${precioMin.toLocaleString()}</span>
        ${p.precio_mayorista ? `<span class="precio-mayorista">Mayorista: $${p.precio_mayorista}</span>` : ''}
      </div>
      
      <div class="producto-info">
        <div class="info-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
          ${p.variantes?.length || 0} variantes
        </div>
        <div class="info-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
          </svg>
          ${p.stock_total} unidades
        </div>
      </div>
    </div>
    
    <div class="producto-actions">
      <button class="btn-action btn-variantes" onclick="verVariantes(${p.id})">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
        Variantes
      </button>
      <button class="btn-action btn-editar" onclick="editarProducto(${p.id})">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        </svg>
        Editar
      </button>
      <button class="btn-action btn-eliminar" onclick="eliminarProducto(${p.id}, this)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    </div>
  `;
  
  return card;
}

/* ---------- FILTROS ---------- */
function setupFiltros() {
  const buscar = document.getElementById('buscar-producto');
  const categoria = document.getElementById('filtro-categoria');
  const genero = document.getElementById('filtro-genero');
  const stock = document.getElementById('filtro-stock');
  
  [buscar, categoria, genero, stock].forEach(el => {
    if (el) el.addEventListener('input', aplicarFiltros);
    if (el) el.addEventListener('change', aplicarFiltros);
  });
}

function aplicarFiltros() {
  const busqueda = document.getElementById('buscar-producto').value.toLowerCase();
  const categoria = document.getElementById('filtro-categoria').value;
  const genero = document.getElementById('filtro-genero').value;
  const stock = document.getElementById('filtro-stock').value;
  
  let filtrados = todosLosProductos.filter(p => {
    // Búsqueda por texto
    if (busqueda && !p.nombre.toLowerCase().includes(busqueda) && 
        !p.descripcion?.toLowerCase().includes(busqueda)) {
      return false;
    }
    
    // Filtro por categoría
    if (categoria && p.categoria !== categoria) return false;
    
    // Filtro por género
    if (genero && p.genero !== genero) return false;
    
    // Filtro por stock
    if (stock === 'disponible' && p.stock_total === 0) return false;
    if (stock === 'agotado' && p.stock_total > 0) return false;
    
    return true;
  });
  
  renderizarProductos(filtrados);
}

/* ---------- MODAL VARIANTES ---------- */
function verVariantes(id) {
  const producto = todosLosProductos.find(p => p.id === id);
  if (!producto) return;
  
  document.getElementById('modal-producto-nombre').textContent = producto.nombre;
  
  const body = document.getElementById('modal-variantes-body');
  
  if (!producto.variantes?.length) {
    body.innerHTML = '<p style="text-align:center;color:#6b7280;">No hay variantes registradas</p>';
  } else {
    body.innerHTML = `
      <table class="variantes-table">
        <thead>
          <tr>
            <th>Talla</th>
            <th>Precio</th>
            <th>Mayorista</th>
            <th>Stock</th>
          </tr>
        </thead>
        <tbody>
          ${producto.variantes.map(v => `
            <tr>
              <td><span class="talla-badge">${v.atributos?.Talla || '—'}</span></td>
              <td><strong>$${parseFloat(v.precio).toLocaleString()}</strong></td>
              <td>$${parseFloat(v.precio_mayorista || 0).toLocaleString()}</td>
              <td>${v.stock} unidades</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
  
  document.getElementById('modal-variantes').style.display = 'flex';
}

function cerrarModalVariantes() {
  document.getElementById('modal-variantes').style.display = 'none';
}

// Cerrar modal al hacer click fuera
document.addEventListener('click', (e) => {
  const modal = document.getElementById('modal-variantes');
  if (e.target === modal) {
    cerrarModalVariantes();
  }
});

/* ---------- ACCIONES ---------- */
function editarProducto(id) {
  window.location.href = `/dashboard/productos/editar/${id}/`;
}

async function eliminarProducto(id, btnEl) {
  if (!confirm('¿Seguro que deseas eliminar este producto?')) return;
  
  const card = btnEl.closest('.producto-card');
  
  try {
    const res = await fetch(`/api/productos/delete/${id}/`, {
      method: 'DELETE',
      headers: {
        "Authorization": `Bearer ${getAccessToken()}`,
        "Content-Type": "application/json",
      }
    });
    
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(`Error ${res.status}: ${msg}`);
    }
    
    // Animación de eliminación
    card.style.transform = 'scale(0.9)';
    card.style.opacity = '0';
    setTimeout(() => {
      card.remove();
      // Actualizar lista local
      todosLosProductos = todosLosProductos.filter(p => p.id !== id);
      actualizarEstadisticas(todosLosProductos);
    }, 300);
    
    toast('Producto eliminado correctamente', 'success');
    
  } catch (err) {
    toast('No se pudo eliminar: ' + err.message, 'error');
  }
}

/* ---------- UTILIDADES ---------- */
function capitalizar(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function toast(msg, type = 'success') {
  // Remover toast anterior si existe
  const existente = document.querySelector('.toast');
  if (existente) existente.remove();
  
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  
  requestAnimationFrame(() => {
    t.classList.add('show');
  });
  
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 400);
  }, 3000);
}
