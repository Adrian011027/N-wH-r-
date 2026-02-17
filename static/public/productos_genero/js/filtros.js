/**
 * filtros.js - Sistema de filtros dinámicos para página de colección
 * Carga opciones de filtros y maneja la aplicación de filtros en tiempo real
 */

(function() {
  'use strict';

  // Estado global de filtros
  const state = {
    genero: window.COLECCION_DATA?.genero || '',
    genero_cod: window.COLECCION_DATA?.genero_cod || '',
    filtros: {
      categoria: '',
      subcategoria: '',
      tallas: [],
      colores: [],
      marcas: [],
      precio_min: '',
      precio_max: '',
      en_oferta: false,
      q: '',
      orden: 'nuevo'
    },
    filtrosDisponibles: {
      tallas: [],
      colores: [],
      marcas: [],
      precio: { min: 0, max: 10000 }
    }
  };

  // DOM Elements
  const dom = {
    sidebar: null,
    overlay: null,
    btnToggle: null,
    btnCerrar: null,
    btnLimpiar: null,
    filtrosBusqueda: null,
    filtrosOrden: null,
    precioMin: null,
    precioMax: null,
    filtroTallas: null,
    filtroColores: null,
    filtroMarcas: null,
    filtroOferta: null,
    productosGrid: null,
    filtrosPills: null,
    productosCounter: null
  };

  // Inicializar cuando el DOM esté listo
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    console.log('🎨 Inicializando sistema de filtros...');
    
    // Obtener elementos DOM
    dom.sidebar = document.getElementById('filtros-sidebar');
    dom.overlay = document.getElementById('filtros-overlay');
    dom.btnToggle = document.getElementById('btn-toggle-filtros');
    dom.btnCerrar = document.getElementById('btn-cerrar-filtros');
    dom.btnLimpiar = document.getElementById('btn-limpiar-filtros');
    dom.filtrosBusqueda = document.getElementById('filtro-busqueda');
    dom.filtrosOrden = document.getElementById('filtro-orden');
    dom.precioMin = document.getElementById('precio-min');
    dom.precioMax = document.getElementById('precio-max');
    dom.filtroTallas = document.getElementById('filtro-tallas');
    dom.filtroColores = document.getElementById('filtro-colores');
    dom.filtroMarcas = document.getElementById('filtro-marcas');
    dom.filtroOferta = document.getElementById('filtro-oferta');
    dom.productosGrid = document.getElementById('productos-grid');
    dom.filtrosPills = document.getElementById('filtros-pills');
    
    if (!dom.sidebar) {
      console.error('❌ No se encontró el sidebar de filtros');
      return;
    }

    // Cargar filtros activos desde URL/datos
    cargarFiltrosActivos();
    
    // Cargar opciones de filtros disponibles
    cargarFiltrosDisponibles();
    
    // Event listeners
    setupEventListeners();
    
    console.log('✅ Sistema de filtros inicializado');
  }

  function setupEventListeners() {
    // Abrir/Cerrar sidebar
    if (dom.btnToggle) {
      dom.btnToggle.addEventListener('click', abrirSidebar);
    }

    if (dom.btnCerrar) {
      dom.btnCerrar.addEventListener('click', cerrarSidebar);
    }

    if (dom.overlay) {
      dom.overlay.addEventListener('click', cerrarSidebar);
    }

    // Limpiar filtros
    if (dom.btnLimpiar) {
      dom.btnLimpiar.addEventListener('click', limpiarFiltros);
    }

    // Botón VER RESULTADOS
    const btnVerResultados = document.getElementById('btn-ver-resultados');
    if (btnVerResultados) {
      btnVerResultados.addEventListener('click', () => {
        cerrarSidebar();
      });
    }

    // Búsqueda con debounce
    if (dom.filtrosBusqueda) {
      let timeoutId;
      dom.filtrosBusqueda.addEventListener('input', (e) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          state.filtros.q = e.target.value.trim();
          aplicarFiltros();
        }, 500);
      });
    }

    // Ordenamiento con radio buttons
    const radiosOrden = document.querySelectorAll('input[name="orden"]');
    radiosOrden.forEach(radio => {
      radio.addEventListener('change', (e) => {
        state.filtros.orden = e.target.value;
        aplicarFiltros();
      });
    });

    // Precio
    if (dom.precioMin) {
      dom.precioMin.addEventListener('change', (e) => {
        state.filtros.precio_min = e.target.value;
        aplicarFiltros();
      });
    }

    if (dom.precioMax) {
      dom.precioMax.addEventListener('change', (e) => {
        state.filtros.precio_max = e.target.value;
        aplicarFiltros();
      });
    }

    // En oferta
    if (dom.filtroOferta) {
      dom.filtroOferta.addEventListener('change', (e) => {
        state.filtros.en_oferta = e.target.checked;
        aplicarFiltros();
      });
    }
  }

  function abrirSidebar() {
    dom.sidebar.classList.add('active');
    dom.overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function cerrarSidebar() {
    dom.sidebar.classList.remove('active');
    dom.overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  function cargarFiltrosActivos() {
    const activos = window.COLECCION_DATA?.filtros_activos || {};
    
    // Cargar valores desde datos pasados por el servidor
    state.filtros.q = activos.q || '';
    state.filtros.orden = activos.orden || 'nuevo';
    state.filtros.precio_min = activos.precio_min || '';
    state.filtros.precio_max = activos.precio_max || '';
    state.filtros.en_oferta = activos.en_oferta === '1';
    state.filtros.tallas = activos.tallas ? activos.tallas.split(',').filter(t => t.trim()) : [];
    state.filtros.colores = activos.colores ? activos.colores.split(',').filter(c => c.trim()) : [];
    state.filtros.marcas = activos.marcas ? activos.marcas.split(',').filter(m => m.trim()) : [];
    state.filtros.categoria = activos.categoria || '';
    state.filtros.subcategoria = activos.subcategoria || '';

    console.log('📋 Filtros activos cargados:', state.filtros);
  }

  async function cargarFiltrosDisponibles() {
    console.log('🔄 Cargando opciones de filtros disponibles...');
    
    try {
      const params = new URLSearchParams();
      if (state.genero_cod) params.append('genero', state.genero_cod);
      if (state.filtros.categoria) params.append('categoria', state.filtros.categoria);
      if (state.filtros.subcategoria) params.append('subcategoria', state.filtros.subcategoria);

      const url = `/api/filtros-disponibles/?${params.toString()}`;
      const response = await fetch(url);
      
      if (!response.ok) throw new Error('Error al cargar filtros');
      
      const data = await response.json();
      
      if (data.success) {
        state.filtrosDisponibles = data.filtros;
        console.log('✅ Filtros disponibles:', state.filtrosDisponibles);
        
        // Renderizar opciones de filtros
        renderTallas();
        renderColores();
        renderMarcas();
        actualizarRangoPrecio();
        renderFiltrosPills();
      }
    } catch (error) {
      console.error('❌ Error cargando filtros:', error);
      mostrarErrorFiltros();
    }
  }

  function renderTallas() {
    if (!dom.filtroTallas) return;
    
    const tallas = state.filtrosDisponibles.tallas || [];
    
    if (tallas.length === 0) {
      dom.filtroTallas.innerHTML = '<span class="loading-text">No disponible</span>';
      return;
    }

    dom.filtroTallas.innerHTML = tallas.map(talla => `
      <label class="filtro-check-zara">
        <input type="checkbox" 
               value="${talla}" 
               ${state.filtros.tallas.includes(talla) ? 'checked' : ''}
               onchange="window.filtrosHandler.toggleTalla('${talla}')">
        <span>${talla}</span>
      </label>
    `).join('');
  }

  function renderColores() {
    if (!dom.filtroColores) return;
    
    const colores = state.filtrosDisponibles.colores || [];
    
    if (colores.length === 0) {
      dom.filtroColores.innerHTML = '<span class="loading-text">No disponible</span>';
      return;
    }

    dom.filtroColores.innerHTML = colores.map(color => {
      const isSelected = state.filtros.colores.includes(color);
      
      return `
        <label class="filtro-check-zara">
          <input type="checkbox" 
                 value="${color}"
                 ${isSelected ? 'checked' : ''}
                 onchange="window.filtrosHandler.toggleColor('${color}')">
          <span>${color.toUpperCase()}</span>
        </label>
      `;
    }).join('');
  }

  function renderMarcas() {
    if (!dom.filtroMarcas) return;
    
    const marcas = state.filtrosDisponibles.marcas || [];
    
    if (marcas.length === 0) {
      dom.filtroMarcas.innerHTML = '<span class="loading-text">No disponible</span>';
      return;
    }

    dom.filtroMarcas.innerHTML = marcas.map(marca => `
      <label class="filtro-check-zara">
        <input type="checkbox" 
               value="${marca}"
               ${state.filtros.marcas.includes(marca) ? 'checked' : ''}
               onchange="window.filtrosHandler.toggleMarca('${marca}')">
        <span>${marca.toUpperCase()}</span>
      </label>
    `).join('');
  }

  function actualizarRangoPrecio() {
    const { min, max } = state.filtrosDisponibles.precio || { min: 0, max: 10000 };
    
    if (dom.precioMin) {
      dom.precioMin.min = min;
      dom.precioMin.max = max;
      dom.precioMin.placeholder = `$${min}`;
    }
    
    if (dom.precioMax) {
      dom.precioMax.min = min;
      dom.precioMax.max = max;
      dom.precioMax.placeholder = `$${max}`;
    }
  }

  function renderFiltrosPills() {
    if (!dom.filtrosPills) return;

    const pills = [];

    // Pill de búsqueda
    if (state.filtros.q) {
      pills.push(`
        <span class="filtro-pill">
          "${state.filtros.q}"
          <button onclick="window.filtrosHandler.removerFiltro('q')">×</button>
        </span>
      `);
    }

    // Pills de tallas
    state.filtros.tallas.forEach(talla => {
      pills.push(`
        <span class="filtro-pill">
          TALLA ${talla}
          <button onclick="window.filtrosHandler.toggleTalla('${talla}')">×</button>
        </span>
      `);
    });

    // Pills de colores
    state.filtros.colores.forEach(color => {
      pills.push(`
        <span class="filtro-pill">
          ${color.toUpperCase()}
          <button onclick="window.filtrosHandler.toggleColor('${color}')">×</button>
        </span>
      `);
    });

    // Pills de marcas
    state.filtros.marcas.forEach(marca => {
      pills.push(`
        <span class="filtro-pill">
          ${marca.toUpperCase()}
          <button onclick="window.filtrosHandler.toggleMarca('${marca}')">×</button>
        </span>
      `);
    });

    // Pill de precio
    if (state.filtros.precio_min || state.filtros.precio_max) {
      const min = state.filtros.precio_min || '0';
      const max = state.filtros.precio_max || '∞';
      pills.push(`
        <span class="filtro-pill">
          $${min} - $${max}
          <button onclick="window.filtrosHandler.removerFiltro('precio')">×</button>
        </span>
      `);
    }

    // Pill de oferta
    if (state.filtros.en_oferta) {
      pills.push(`
        <span class="filtro-pill">
          EN OFERTA
          <button onclick="window.filtrosHandler.removerFiltro('oferta')">×</button>
        </span>
      `);
    }

    dom.filtrosPills.innerHTML = pills.join('');
    
    // Usar clase para mostrar/ocultar
    if (pills.length > 0) {
      dom.filtrosPills.classList.add('has-pills');
    } else {
      dom.filtrosPills.classList.remove('has-pills');
    }
  }

  function toggleTalla(talla) {
    const index = state.filtros.tallas.indexOf(talla);
    if (index > -1) {
      state.filtros.tallas.splice(index, 1);
    } else {
      state.filtros.tallas.push(talla);
    }
    aplicarFiltros();
  }

  function toggleColor(color) {
    const index = state.filtros.colores.indexOf(color);
    if (index > -1) {
      state.filtros.colores.splice(index, 1);
    } else {
      state.filtros.colores.push(color);
    }
    aplicarFiltros();
  }

  function toggleMarca(marca) {
    const index = state.filtros.marcas.indexOf(marca);
    if (index > -1) {
      state.filtros.marcas.splice(index, 1);
    } else {
      state.filtros.marcas.push(marca);
    }
    aplicarFiltros();
  }

  function removerFiltro(tipo) {
    switch(tipo) {
      case 'q':
        state.filtros.q = '';
        if (dom.filtrosBusqueda) dom.filtrosBusqueda.value = '';
        break;
      case 'precio':
        state.filtros.precio_min = '';
        state.filtros.precio_max = '';
        if (dom.precioMin) dom.precioMin.value = '';
        if (dom.precioMax) dom.precioMax.value = '';
        break;
      case 'oferta':
        state.filtros.en_oferta = false;
        if (dom.filtroOferta) dom.filtroOferta.checked = false;
        break;
    }
    aplicarFiltros();
  }

  function limpiarFiltros() {
    // Resetear estado
    state.filtros = {
      categoria: '',
      subcategoria: '',
      tallas: [],
      colores: [],
      marcas: [],
      precio_min: '',
      precio_max: '',
      en_oferta: false,
      q: '',
      orden: 'nuevo'
    };

    // Resetear inputs
    if (dom.filtrosBusqueda) dom.filtrosBusqueda.value = '';
    if (dom.precioMin) dom.precioMin.value = '';
    if (dom.precioMax) dom.precioMax.value = '';
    if (dom.filtroOferta) dom.filtroOferta.checked = false;
    
    // Resetear radios de orden
    const radiosOrden = document.querySelectorAll('input[name="orden"]');
    radiosOrden.forEach(radio => {
      radio.checked = false;
    });

    // Resetear checkboxes de tallas, colores, marcas
    const checkboxes = document.querySelectorAll('.filtro-check-zara input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);

    // Recargar página sin parámetros
    window.location.href = window.location.pathname;
  }

  function aplicarFiltros() {
    console.log('🔄 Aplicando filtros...', state.filtros);

    // Construir parámetros
    const params = new URLSearchParams();
    
    if (state.filtros.categoria) params.append('categoria', state.filtros.categoria);
    if (state.filtros.subcategoria) params.append('subcategoria', state.filtros.subcategoria);
    if (state.filtros.tallas.length > 0) params.append('tallas', state.filtros.tallas.join(','));
    if (state.filtros.colores.length > 0) params.append('colores', state.filtros.colores.join(','));
    if (state.filtros.marcas.length > 0) params.append('marcas', state.filtros.marcas.join(','));
    if (state.filtros.precio_min) params.append('precio_min', state.filtros.precio_min);
    if (state.filtros.precio_max) params.append('precio_max', state.filtros.precio_max);
    if (state.filtros.en_oferta) params.append('en_oferta', '1');
    if (state.filtros.q) params.append('q', state.filtros.q);
    if (state.filtros.orden && state.filtros.orden !== 'nuevo') params.append('orden', state.filtros.orden);

    // Actualizar URL sin recargar
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', newUrl);

    // Cargar productos con AJAX
    cargarProductosFiltrados(params);
    
    // Actualizar pills
    renderFiltrosPills();
  }

  async function cargarProductosFiltrados(params) {
    if (!dom.productosGrid) return;

    // Mostrar loading
    dom.productosGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f0f0f0; border-top-color: #1d1d1d; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
        <p style="margin-top: 15px; color: #999;">Cargando productos...</p>
      </div>
    `;

    try {
      // Añadir parámetro para AJAX
      params.append('ajax', '1');
      
      const response = await fetch(`${window.location.pathname}?${params.toString()}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) throw new Error('Error al cargar productos');

      const data = await response.json();

      if (data.success) {
        // Renderizar productos
        renderProductos(data.productos);
        
        // Actualizar contador
        actualizarContador(data.productos.length, data.total);
        
        // Actualizar paginación si existe
        actualizarPaginacion(data.paginacion);
      } else {
        throw new Error(data.message || 'Error al cargar productos');
      }

    } catch (error) {
      console.error('❌ Error al cargar productos:', error);
      dom.productosGrid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
          <p style="color: #999;">Error al cargar productos. Por favor, intenta de nuevo.</p>
        </div>
      `;
    }
  }

  function renderProductos(productos) {
    if (!productos || productos.length === 0) {
      dom.productosGrid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
          <p style="color: #999; font-size: 16px;">No se encontraron productos con los filtros seleccionados.</p>
        </div>
      `;
      return;
    }

    const html = productos.map(p => `
      <div class="producto-card">
        <div class="thumb">
          <a href="/producto/${p.id}/?from=${state.genero}">
            <img src="${p.imagen || 'https://via.placeholder.com/250?text=Sin+Imagen'}" 
                 alt="${p.nombre}" 
                 loading="lazy">
          </a>
        </div>
        <button class="wishlist-btn" aria-label="Añadir a favoritos" data-product-id="${p.id}">
          <i class="fa-regular fa-heart"></i>
        </button>
        ${p.en_oferta ? '<span class="badge-oferta">OFERTA</span>' : ''}
        <div class="card-info">
          <h4>${p.nombre}</h4>
          ${p.marca ? `<p class="producto-marca">${p.marca}</p>` : ''}
          <span class="card-price">$${Number(p.precio).toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})} <small>MXN</small></span>
        </div>
      </div>
    `).join('');

    dom.productosGrid.innerHTML = html;
  }

  function actualizarContador(mostrando, total) {
    const mostrandoEl = document.getElementById('productos-mostrando');
    const totalEl = document.getElementById('productos-total');
    
    if (mostrandoEl) mostrandoEl.textContent = mostrando;
    if (totalEl) totalEl.textContent = total;
  }

  function actualizarPaginacion(paginacionData) {
    const paginacionEl = document.querySelector('.paginacion');
    if (!paginacionEl || !paginacionData) return;

    let html = '';

    // Botón anterior
    if (paginacionData.pagina_actual > 1) {
      html += `<a href="?pagina=${paginacionData.pagina_actual - 1}">← Anterior</a>`;
    }

    // Páginas
    for (let i = 1; i <= paginacionData.total_paginas; i++) {
      if (i === paginacionData.pagina_actual) {
        html += `<span class="actual">${i}</span>`;
      } else {
        html += `<a href="?pagina=${i}">${i}</a>`;
      }
    }

    // Botón siguiente
    if (paginacionData.pagina_actual < paginacionData.total_paginas) {
      html += `<a href="?pagina=${paginacionData.pagina_actual + 1}">Siguiente →</a>`;
    }

    paginacionEl.innerHTML = html;
  }

  function mostrarErrorFiltros() {
    if (dom.filtroTallas) dom.filtroTallas.innerHTML = '<p class="error">Error al cargar filtros</p>';
    if (dom.filtroColores) dom.filtroColores.innerHTML = '<p class="error">Error al cargar filtros</p>';
    if (dom.filtroMarcas) dom.filtroMarcas.innerHTML = '<p class="error">Error al cargar filtros</p>';
  }

  // Exponer funciones al scope global para onclick handlers
  window.filtrosHandler = {
    toggleTalla,
    toggleColor,
    toggleMarca,
    removerFiltro,
    limpiarFiltros,
    abrirFiltros: abrirSidebar,
    cerrarFiltros: cerrarSidebar
  };

})();
