/**
 * Sistema de búsqueda y filtros de productos
 */

// Estado de la aplicación
let currentPage = 1;
let currentFilters = {
  q: '',
  categoria: '',
  genero: '',
  precio_min: '',
  precio_max: '',
  tallas: [],
  en_oferta: false,
  disponibles: true,
  ordenar: 'nuevo',
  page: 1,
  per_page: 20
};

// ========== INICIALIZACIÓN ==========
document.addEventListener('DOMContentLoaded', () => {
  initSearchBar();
  initFilters();
  initPagination();
  initSort();
  
  // Cargar productos iniciales
  loadProducts();
  
  // Verificar si hay query params en la URL
  const urlParams = new URLSearchParams(window.location.search);
  const queryParam = urlParams.get('q');
  if (queryParam) {
    document.getElementById('searchInput').value = queryParam;
    currentFilters.q = queryParam;
    loadProducts();
  }
});

// ========== BARRA DE BÚSQUEDA ==========
function initSearchBar() {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  
  // Búsqueda al hacer clic
  searchBtn.addEventListener('click', () => {
    performSearch();
  });
  
  // Búsqueda con Enter
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });
  
  // Búsqueda en tiempo real (opcional, con debounce)
  let searchTimeout;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      // Comentar esta línea si solo quieres búsqueda al presionar Enter/botón
      // performSearch();
    }, 500);
  });
}

function performSearch() {
  const searchInput = document.getElementById('searchInput');
  currentFilters.q = searchInput.value.trim();
  currentFilters.page = 1;
  loadProducts();
}

// ========== FILTROS ==========
function initFilters() {
  // Categoría
  document.getElementById('filterCategoria').addEventListener('change', (e) => {
    currentFilters.categoria = e.target.value;
    applyFilters();
  });
  
  // Género
  document.querySelectorAll('input[name="genero"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      currentFilters.genero = e.target.value;
    });
  });
  
  // Precio - inputs
  const precioMin = document.getElementById('precioMin');
  const precioMax = document.getElementById('precioMax');
  
  precioMin.addEventListener('change', (e) => {
    currentFilters.precio_min = e.target.value;
  });
  
  precioMax.addEventListener('change', (e) => {
    currentFilters.precio_max = e.target.value;
  });
  
  // Precio - range sliders
  const rangeMin = document.getElementById('rangeMin');
  const rangeMax = document.getElementById('rangeMax');
  
  rangeMin.addEventListener('input', (e) => {
    const value = parseInt(e.target.value);
    const maxValue = parseInt(rangeMax.value);
    
    if (value > maxValue - 100) {
      e.target.value = maxValue - 100;
    }
    
    precioMin.value = e.target.value;
    currentFilters.precio_min = e.target.value;
  });
  
  rangeMax.addEventListener('input', (e) => {
    const value = parseInt(e.target.value);
    const minValue = parseInt(rangeMin.value);
    
    if (value < minValue + 100) {
      e.target.value = minValue + 100;
    }
    
    precioMax.value = e.target.value;
    currentFilters.precio_max = e.target.value;
  });
  
  // Checkboxes de oferta y disponibilidad
  document.getElementById('soloOferta').addEventListener('change', (e) => {
    currentFilters.en_oferta = e.target.checked;
  });
  
  document.getElementById('soloDisponibles').addEventListener('change', (e) => {
    currentFilters.disponibles = e.target.checked;
  });
  
  // Botón aplicar filtros
  document.getElementById('applyFilters').addEventListener('click', applyFilters);
  
  // Botón limpiar filtros
  document.getElementById('clearFilters').addEventListener('click', clearFilters);
  
  // Toggle filtros en móvil
  const toggleBtn = document.getElementById('toggleFilters');
  const sidebar = document.getElementById('filtersSidebar');
  
  toggleBtn?.addEventListener('click', () => {
    sidebar.classList.toggle('active');
  });
  
  // Cerrar sidebar al hacer clic fuera (móvil)
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 992) {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('active');
      }
    }
  });
}

function applyFilters() {
  // Recoger tallas seleccionadas
  const tallasCheckboxes = document.querySelectorAll('input[name="talla"]:checked');
  currentFilters.tallas = Array.from(tallasCheckboxes).map(cb => cb.value);
  
  // Resetear página
  currentFilters.page = 1;
  
  // Cargar productos
  loadProducts();
  
  // Cerrar sidebar en móvil
  if (window.innerWidth <= 992) {
    document.getElementById('filtersSidebar').classList.remove('active');
  }
}

function clearFilters() {
  // Resetear valores
  currentFilters = {
    q: document.getElementById('searchInput').value.trim(),
    categoria: '',
    genero: '',
    precio_min: '',
    precio_max: '',
    tallas: [],
    en_oferta: false,
    disponibles: true,
    ordenar: currentFilters.ordenar,
    page: 1,
    per_page: 20
  };
  
  // Resetear UI
  document.getElementById('filterCategoria').value = '';
  document.querySelectorAll('input[name="genero"]')[0].checked = true;
  document.getElementById('soloOferta').checked = false;
  document.getElementById('soloDisponibles').checked = true;
  document.querySelectorAll('input[name="talla"]').forEach(cb => cb.checked = false);
  
  // Resetear precios
  const rangeMin = document.getElementById('rangeMin');
  const rangeMax = document.getElementById('rangeMax');
  const precioMin = document.getElementById('precioMin');
  const precioMax = document.getElementById('precioMax');
  
  rangeMin.value = rangeMin.min;
  rangeMax.value = rangeMax.max;
  precioMin.value = rangeMin.min;
  precioMax.value = rangeMax.max;
  
  // Recargar productos
  loadProducts();
}

// ========== ORDENAMIENTO ==========
function initSort() {
  document.getElementById('sortSelect').addEventListener('change', (e) => {
    currentFilters.ordenar = e.target.value;
    currentFilters.page = 1;
    loadProducts();
  });
}

// ========== PAGINACIÓN ==========
function initPagination() {
  document.getElementById('prevPage').addEventListener('click', () => {
    if (currentFilters.page > 1) {
      currentFilters.page--;
      loadProducts();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });
  
  document.getElementById('nextPage').addEventListener('click', () => {
    currentFilters.page++;
    loadProducts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

function updatePagination(data) {
  const pagination = document.getElementById('pagination');
  const prevBtn = document.getElementById('prevPage');
  const nextBtn = document.getElementById('nextPage');
  const pageInfo = document.getElementById('pageInfo');
  
  if (data.total_pages > 1) {
    pagination.style.display = 'flex';
    pageInfo.textContent = `Página ${data.page} de ${data.total_pages}`;
    
    prevBtn.disabled = !data.has_prev;
    nextBtn.disabled = !data.has_next;
  } else {
    pagination.style.display = 'none';
  }
}

// ========== CARGAR PRODUCTOS ==========
async function loadProducts() {
  const grid = document.getElementById('productosGrid');
  const loading = document.getElementById('loadingSpinner');
  const noResults = document.getElementById('noResults');
  const resultsCount = document.getElementById('resultsCount');
  
  // Mostrar loading
  grid.innerHTML = '';
  loading.style.display = 'flex';
  noResults.style.display = 'none';
  
  try {
    // Construir query string
    const params = new URLSearchParams();
    
    Object.entries(currentFilters).forEach(([key, value]) => {
      if (key === 'tallas') {
        if (value.length > 0) {
          params.append('tallas', value.join(','));
        }
      } else if (value !== '' && value !== false) {
        params.append(key, value);
      }
    });
    
    // Hacer petición
    const response = await fetch(`/api/search/?${params.toString()}`);
    const data = await response.json();
    
    // Ocultar loading
    loading.style.display = 'none';
    
    // Actualizar contador
    resultsCount.textContent = `${data.total} producto${data.total !== 1 ? 's' : ''} encontrado${data.total !== 1 ? 's' : ''}`;
    
    if (data.productos.length === 0) {
      noResults.style.display = 'block';
      return;
    }
    
    // Renderizar productos
    renderProducts(data.productos);
    
    // Actualizar paginación
    updatePagination(data);
    
  } catch (error) {
    console.error('Error cargando productos:', error);
    loading.style.display = 'none';
    noResults.style.display = 'block';
    document.querySelector('.no-results h3').textContent = 'Error al cargar productos';
    document.querySelector('.no-results p').textContent = 'Por favor, intenta de nuevo más tarde';
  }
}

// ========== RENDERIZAR PRODUCTOS ==========
function renderProducts(productos) {
  const grid = document.getElementById('productosGrid');
  grid.innerHTML = '';
  
  productos.forEach(producto => {
    const card = createProductCard(producto);
    grid.appendChild(card);
  });
}

function createProductCard(producto) {
  const card = document.createElement('div');
  card.className = 'producto-card';
  
  // Determinar género para el link
  const genero = producto.genero.toLowerCase() === 'mujer' ? 'dama' : 'caballero';
  
  card.innerHTML = `
    <div class="imagen-zoom">
      <a href="/producto/${producto.id}/?from=${genero}">
        <img src="${producto.imagen || '/static/images/no-image.jpg'}" alt="${producto.nombre}">
      </a>
      <button class="wishlist-btn" aria-label="Añadir a favoritos" data-product-id="${producto.id}">
        <i class="fa-regular fa-heart"></i>
      </button>
    </div>
    <div class="info">
      ${producto.en_oferta ? '<span class="badge">OFERTA</span>' : ''}
      <h4>${producto.nombre}</h4>
      <h5>$${producto.precio.toFixed(2)}</h5>
      ${producto.tallas_disponibles.length > 0 ? `<p style="font-size: 0.875rem; color: #666; margin-top: 0.5rem;">Tallas: ${producto.tallas_disponibles.join(', ')}</p>` : ''}
      ${producto.stock_total === 0 ? '<p style="color: #ff4444; font-size: 0.875rem;">Sin stock</p>' : ''}
    </div>
  `;
  
  return card;
}

// ========== UTILIDADES ==========
window.searchProducts = loadProducts; // Exportar para uso externo si es necesario
