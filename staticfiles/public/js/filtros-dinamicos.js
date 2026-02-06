/**
 * filtros-dinamicos.js
 * Sistema de filtros dinámicos: Género → Categoría → Subcategoría → Productos
 * 
 * Flujo:
 * 1. Usuario selecciona género en navbar
 * 2. Se cargan categorías disponibles para ese género
 * 3. Al seleccionar categoría, se cargan sus subcategorías
 * 4. Productos se filtran según selección
 */

(function() {
  'use strict';

  // Estado global de filtros
  const state = {
    generoSeleccionado: 'ambos',
    categoriaSeleccionada: null,
    subcategoriasSeleccionadas: new Set(),
    productos: []
  };

  // Cache de datos para evitar llamadas repetidas
  const cache = {
    categorias: {},
    subcategorias: {}
  };

  // DOM Elements
  const dom = {
    generoSelector: null,
    categoriasContainer: null,
    subcategoriasContainer: null,
    productosContainer: null,
    filtrosPill: null
  };

  // Inicializar cuando el DOM esté listo
  document.addEventListener('DOMContentLoaded', init);

  async function init() {
    // Buscar elementos del DOM
    dom.generoSelector = document.querySelector('[data-genero-selector]');
    dom.categoriasContainer = document.querySelector('[data-categorias-container]');
    dom.subcategoriasContainer = document.querySelector('[data-subcategorias-container]');
    dom.productosContainer = document.querySelector('[data-productos-container]');
    dom.filtrosPill = document.querySelector('[data-filtros-pill]');

    if (!dom.categoriasContainer || !dom.subcategoriasContainer) {
      console.warn('Contenedores de filtros no encontrados');
      return;
    }

    // Event listeners para género
    if (dom.generoSelector) {
      dom.generoSelector.addEventListener('change', onGeneroChange);
    }

    // Cargar categorías iniciales (género "ambos")
    await cargarCategorias('ambos');
  }

  /**
   * Cuando cambia el género seleccionado
   */
  async function onGeneroChange(e) {
    const genero = e.target.value || 'ambos';
    state.generoSeleccionado = genero;
    state.categoriaSeleccionada = null;
    state.subcategoriasSeleccionadas.clear();

    console.log(`📍 Género seleccionado: ${genero}`);

    // Cargar nuevas categorías
    await cargarCategorias(genero);

    // Limpiar subcategorías
    dom.subcategoriasContainer.innerHTML = '';
    dom.subcategoriasContainer.classList.add('hidden');

    // Limpiar productos
    if (dom.productosContainer) {
      dom.productosContainer.innerHTML = '';
    }

    actualizarPills();
  }

  /**
   * Cargar categorías según género
   */
  async function cargarCategorias(genero) {
    try {
      // Verificar cache
      if (cache.categorias[genero]) {
        renderCategorias(cache.categorias[genero]);
        return;
      }

      const response = await fetch(`/api/categorias-por-genero/?genero=${genero}`);
      if (!response.ok) throw new Error('Error cargando categorías');

      const data = await response.json();
      cache.categorias[genero] = data.categorias;

      renderCategorias(data.categorias);
    } catch (error) {
      console.error('Error cargando categorías:', error);
      dom.categoriasContainer.innerHTML = '<p class="error">No se pudieron cargar las categorías</p>';
    }
  }

  /**
   * Renderizar categorías como botones clickeables
   */
  function renderCategorias(categorias) {
    dom.categoriasContainer.innerHTML = '';

    if (categorias.length === 0) {
      dom.categoriasContainer.innerHTML = '<p class="empty">No hay categorías disponibles</p>';
      return;
    }

    const container = document.createElement('div');
    container.className = 'categorias-grid';

    categorias.forEach(cat => {
      const btn = document.createElement('button');
      btn.className = 'categoria-btn';
      btn.dataset.id = cat.id;
      btn.innerHTML = `
        <img src="${cat.imagen || '/static/images/placeholder.png'}" alt="${cat.nombre}" />
        <span>${cat.nombre}</span>
      `;
      btn.addEventListener('click', () => onCategoriaSelect(cat.id, cat.nombre));

      container.appendChild(btn);
    });

    dom.categoriasContainer.appendChild(container);
  }

  /**
   * Cuando selecciona una categoría
   */
  async function onCategoriaSelect(categoriaId, categoriaNombre) {
    state.categoriaSeleccionada = categoriaId;
    state.subcategoriasSeleccionadas.clear();

    console.log(`📂 Categoría seleccionada: ${categoriaNombre} (ID: ${categoriaId})`);

    // Actualizar estado visual (highlight)
    document.querySelectorAll('.categoria-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.id == categoriaId);
    });

    // Cargar subcategorías
    await cargarSubcategorias(categoriaId);
    actualizarPills();

    // Mostrar productos vacíos inicialmente
    if (dom.productosContainer) {
      dom.productosContainer.innerHTML = '<p class="info">Selecciona subcategorías para ver productos</p>';
    }
  }

  /**
   * Cargar subcategorías según categoría y género
   */
  async function cargarSubcategorias(categoriaId) {
    try {
      const cacheKey = `${state.generoSeleccionado}-${categoriaId}`;

      if (cache.subcategorias[cacheKey]) {
        renderSubcategorias(cache.subcategorias[cacheKey]);
        return;
      }

      const response = await fetch(
        `/api/subcategorias-por-categoria/?categoria_id=${categoriaId}&genero=${state.generoSeleccionado}`
      );
      if (!response.ok) throw new Error('Error cargando subcategorías');

      const data = await response.json();
      cache.subcategorias[cacheKey] = data.subcategorias;

      renderSubcategorias(data.subcategorias);
    } catch (error) {
      console.error('Error cargando subcategorías:', error);
      dom.subcategoriasContainer.innerHTML = '<p class="error">No se pudieron cargar las subcategorías</p>';
    }
  }

  /**
   * Renderizar subcategorías como checkboxes
   */
  function renderSubcategorias(subcategorias) {
    dom.subcategoriasContainer.innerHTML = '';

    if (subcategorias.length === 0) {
      dom.subcategoriasContainer.innerHTML = '<p class="empty">No hay filtros disponibles</p>';
      dom.subcategoriasContainer.classList.add('hidden');
      return;
    }

    dom.subcategoriasContainer.classList.remove('hidden');

    // Agrupar por tipo
    const porTipo = {};
    subcategorias.forEach(sub => {
      if (!porTipo[sub.tipo]) {
        porTipo[sub.tipo] = [];
      }
      porTipo[sub.tipo].push(sub);
    });

    // Renderizar cada grupo
    Object.entries(porTipo).forEach(([tipo, subs]) => {
      const grupoDiv = document.createElement('div');
      grupoDiv.className = 'subcategorias-grupo';

      const titulo = document.createElement('h4');
      titulo.textContent = getNombreTipo(tipo);
      grupoDiv.appendChild(titulo);

      const checkboxesDiv = document.createElement('div');
      checkboxesDiv.className = 'subcategorias-list';

      subs.forEach(sub => {
        const label = document.createElement('label');
        label.className = 'checkbox-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = sub.id;
        checkbox.dataset.nombre = sub.nombre;
        checkbox.addEventListener('change', onSubcategoriaChange);

        const span = document.createElement('span');
        span.textContent = sub.nombre;

        label.appendChild(checkbox);
        label.appendChild(span);
        checkboxesDiv.appendChild(label);
      });

      grupoDiv.appendChild(checkboxesDiv);
      dom.subcategoriasContainer.appendChild(grupoDiv);
    });
  }

  /**
   * Cuando cambian las subcategorías seleccionadas
   */
  async function onSubcategoriaChange() {
    // Actualizar set de subcategorías seleccionadas
    state.subcategoriasSeleccionadas.clear();

    document.querySelectorAll('[data-subcategorias-container] input[type="checkbox"]:checked').forEach(cb => {
      state.subcategoriasSeleccionadas.add(cb.value);
    });

    console.log(`🏷️  Subcategorías seleccionadas:`, Array.from(state.subcategoriasSeleccionadas));

    // Cargar productos
    await cargarProductos();
    actualizarPills();
  }

  /**
   * Cargar productos según filtros actuales
   */
  async function cargarProductos() {
    if (!state.categoriaSeleccionada || state.subcategoriasSeleccionadas.size === 0) {
      if (dom.productosContainer) {
        dom.productosContainer.innerHTML = '<p class="info">Selecciona una o más subcategorías</p>';
      }
      return;
    }

    try {
      const subcategorias = Array.from(state.subcategoriasSeleccionadas).join(',');
      const url = `/api/productos-filtrados/?genero=${state.generoSeleccionado}&categoria_id=${state.categoriaSeleccionada}&subcategorias=${subcategorias}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Error cargando productos');

      const data = await response.json();
      renderProductos(data.productos);
    } catch (error) {
      console.error('Error cargando productos:', error);
      if (dom.productosContainer) {
        dom.productosContainer.innerHTML = '<p class="error">Error cargando productos</p>';
      }
    }
  }

  /**
   * Renderizar productos encontrados
   */
  function renderProductos(productos) {
    if (!dom.productosContainer) return;

    dom.productosContainer.innerHTML = '';

    if (productos.length === 0) {
      dom.productosContainer.innerHTML = '<p class="empty">No hay productos disponibles con los filtros seleccionados</p>';
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'productos-grid';

    productos.forEach(p => {
      const card = document.createElement('a');
      card.href = `/producto/${p.id}/`;
      card.className = 'producto-card';

      card.innerHTML = `
        <img src="${p.imagen || '/static/images/placeholder.png'}" alt="${p.nombre}" />
        <h3>${p.nombre}</h3>
        <p class="precio">$${p.precio}</p>
        ${p.en_oferta ? '<span class="oferta-badge">EN OFERTA</span>' : ''}
      `;

      grid.appendChild(card);
    });

    dom.productosContainer.appendChild(grid);
  }

  /**
   * Actualizar pills de filtros activos
   */
  function actualizarPills() {
    if (!dom.filtrosPill) return;

    dom.filtrosPill.innerHTML = '';

    // Pill de género
    const pillGenero = document.createElement('span');
    pillGenero.className = 'filter-pill';
    pillGenero.textContent = `Género: ${state.generoSeleccionado}`;
    dom.filtrosPill.appendChild(pillGenero);

    // Pill de categoría
    if (state.categoriaSeleccionada) {
      const catBtn = document.querySelector(`.categoria-btn[data-id="${state.categoriaSeleccionada}"]`);
      if (catBtn) {
        const pillCat = document.createElement('span');
        pillCat.className = 'filter-pill';
        pillCat.textContent = `Categoría: ${catBtn.textContent.trim()}`;
        dom.filtrosPill.appendChild(pillCat);
      }
    }

    // Pills de subcategorías
    state.subcategoriasSeleccionadas.forEach(subcatId => {
      const checkbox = document.querySelector(`[data-subcategorias-container] input[value="${subcatId}"]:checked`);
      if (checkbox) {
        const pill = document.createElement('span');
        pill.className = 'filter-pill';
        pill.textContent = checkbox.dataset.nombre;
        dom.filtrosPill.appendChild(pill);
      }
    });
  }

  /**
   * Helpers
   */
  function getNombreTipo(tipo) {
    const tipos = {
      'marca': '🏷️ Marca',
      'oferta': '🎁 Promoción',
      'linea': '✨ Línea',
      'otro': '📌 Otro'
    };
    return tipos[tipo] || tipo;
  }

})();
