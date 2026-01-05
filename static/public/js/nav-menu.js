/**
 * nav-menu.js
 * Menú elegante con navegación en cascada: Género → Categoría → Subcategoría
 * Paneles que se deslizan para una experiencia móvil fluida
 */

(function() {
  'use strict';

  // Estado
  const state = {
    currentGenero: null,
    currentCategoria: null,
    cache: {
      categorias: {},
      subcategorias: {}
    }
  };

  // DOM Elements
  const dom = {
    navMenu: null,
    panelMain: null,
    panelCategorias: null,
    panelSubcategorias: null,
    categoriasTitle: null,
    subcategoriasTitle: null,
    categoriasList: null,
    subcategoriasList: null
  };

  // Inicializar
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    // Obtener elementos del DOM
    dom.navMenu = document.getElementById('nav-menu');
    dom.panelMain = document.getElementById('panel-main');
    dom.panelCategorias = document.getElementById('panel-categorias');
    dom.panelSubcategorias = document.getElementById('panel-subcategorias');
    dom.categoriasTitle = document.getElementById('categorias-title');
    dom.subcategoriasTitle = document.getElementById('subcategorias-title');
    dom.categoriasList = document.getElementById('categorias-list');
    dom.subcategoriasList = document.getElementById('subcategorias-list');

    if (!dom.navMenu) {
      console.warn('nav-menu.js: Menú no encontrado');
      return;
    }

    setupEventListeners();
    console.log('✅ Menú de navegación inicializado');
  }

  /**
   * Setup event listeners
   */
  function setupEventListeners() {
    // Género triggers
    document.querySelectorAll('.genero-trigger').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const li = trigger.closest('.nav-item-expandable');
        const genero = li?.dataset.genero;
        if (genero) {
          openCategorias(genero);
        }
      });
    });

    // Botón volver a géneros
    const btnBackGeneros = document.getElementById('btn-back-generos');
    if (btnBackGeneros) {
      btnBackGeneros.addEventListener('click', () => {
        closeCategorias();
      });
    }

    // Botón volver a categorías
    const btnBackCategorias = document.getElementById('btn-back-categorias');
    if (btnBackCategorias) {
      btnBackCategorias.addEventListener('click', () => {
        closeSubcategorias();
      });
    }

    // Cerrar menú al hacer clic fuera
    document.addEventListener('click', (e) => {
      if (dom.navMenu?.classList.contains('open') && 
          !e.target.closest('.nav-menu') && 
          !e.target.closest('#btn-burger')) {
        resetToMain();
      }
    });
  }

  /**
   * Abrir panel de categorías para un género
   */
  async function openCategorias(genero) {
    state.currentGenero = genero;

    // Actualizar título
    const generoNombres = {
      'ambos': '👥 Ambos',
      'mujer': '👩 Mujer', 
      'hombre': '👨 Hombre'
    };
    dom.categoriasTitle.textContent = generoNombres[genero] || genero;

    // Mostrar loading
    dom.categoriasList.innerHTML = `
      <li class="nav-item nav-loading">
        <div class="loading-spinner"></div>
        <span>Cargando categorías...</span>
      </li>
    `;

    // Transición de paneles
    dom.panelMain.classList.add('slide-out');
    dom.panelMain.classList.remove('active');
    dom.panelCategorias.classList.add('active');

    // Cargar categorías
    await loadCategorias(genero);
  }

  /**
   * Cerrar panel de categorías
   */
  function closeCategorias() {
    dom.panelMain.classList.remove('slide-out');
    dom.panelMain.classList.add('active');
    dom.panelCategorias.classList.remove('active');
    state.currentGenero = null;
  }

  /**
   * Abrir panel de subcategorías
   */
  async function openSubcategorias(categoriaId, categoriaNombre) {
    state.currentCategoria = categoriaId;

    // Actualizar título
    dom.subcategoriasTitle.textContent = categoriaNombre;

    // Mostrar loading
    dom.subcategoriasList.innerHTML = `
      <li class="nav-item nav-loading">
        <div class="loading-spinner"></div>
        <span>Cargando...</span>
      </li>
    `;

    // Transición de paneles
    dom.panelCategorias.classList.add('slide-out');
    dom.panelCategorias.classList.remove('active');
    dom.panelSubcategorias.classList.add('active');

    // Cargar subcategorías
    await loadSubcategorias(categoriaId, state.currentGenero);
  }

  /**
   * Cerrar panel de subcategorías
   */
  function closeSubcategorias() {
    dom.panelCategorias.classList.remove('slide-out');
    dom.panelCategorias.classList.add('active');
    dom.panelSubcategorias.classList.remove('active');
    state.currentCategoria = null;
  }

  /**
   * Resetear al panel principal
   */
  function resetToMain() {
    dom.panelMain.classList.remove('slide-out');
    dom.panelMain.classList.add('active');
    dom.panelCategorias.classList.remove('active', 'slide-out');
    dom.panelSubcategorias.classList.remove('active');
    state.currentGenero = null;
    state.currentCategoria = null;
  }

  /**
   * Cargar categorías desde API
   */
  async function loadCategorias(genero) {
    console.log(`📂 Cargando categorías para género: ${genero}`);
    try {
      // Verificar cache
      if (state.cache.categorias[genero]) {
        console.log(`📦 Usando cache para ${genero}:`, state.cache.categorias[genero]);
        renderCategorias(state.cache.categorias[genero]);
        return;
      }

      const url = `/api/categorias-por-genero/?genero=${genero}`;
      console.log(`🔗 Llamando a: ${url}`);
      
      const response = await fetch(url);
      console.log(`📡 Response status: ${response.status}`);
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      console.log(`✅ Categorías recibidas:`, data);
      
      state.cache.categorias[genero] = data.categorias || [];

      renderCategorias(state.cache.categorias[genero]);
    } catch (error) {
      console.error('❌ Error cargando categorías:', error);
      dom.categoriasList.innerHTML = `
        <li class="nav-item nav-error">Error al cargar categorías: ${error.message}</li>
      `;
    }
  }

  /**
   * Renderizar categorías
   */
  function renderCategorias(categorias) {
    dom.categoriasList.innerHTML = '';

    if (!categorias || categorias.length === 0) {
      dom.categoriasList.innerHTML = `
        <li class="nav-item nav-empty">No hay categorías disponibles</li>
      `;
      return;
    }

    categorias.forEach((cat, index) => {
      const li = document.createElement('li');
      li.className = 'nav-item';
      li.style.animationDelay = `${0.1 + index * 0.05}s`;

      const link = document.createElement('a');
      link.href = '#';
      link.className = 'nav-link categoria-trigger';
      link.innerHTML = `
        ${cat.imagen ? `<img src="${cat.imagen}" alt="${cat.nombre}" class="cat-thumb">` : `<span class="nav-icon">📁</span>`}
        <span>${cat.nombre}</span>
        <svg class="nav-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      `;

      link.addEventListener('click', (e) => {
        e.preventDefault();
        openSubcategorias(cat.id, cat.nombre);
      });

      li.appendChild(link);
      dom.categoriasList.appendChild(li);
    });

    // Agregar link "Ver todos" al final
    const verTodosLi = document.createElement('li');
    verTodosLi.className = 'nav-item';
    const verTodosLink = document.createElement('a');
    verTodosLink.href = `/catalogo/?genero=${state.currentGenero}`;
    verTodosLink.className = 'nav-link nav-link-highlight';
    verTodosLink.innerHTML = `<span>Ver todos de ${state.currentGenero}</span>`;
    verTodosLi.appendChild(verTodosLink);
    dom.categoriasList.appendChild(verTodosLi);
  }

  /**
   * Cargar subcategorías desde API
   */
  async function loadSubcategorias(categoriaId, genero) {
    try {
      const cacheKey = `${genero}-${categoriaId}`;

      // Verificar cache
      if (state.cache.subcategorias[cacheKey]) {
        renderSubcategorias(state.cache.subcategorias[cacheKey]);
        return;
      }

      const response = await fetch(
        `/api/subcategorias-por-categoria/?categoria_id=${categoriaId}&genero=${genero}`
      );
      if (!response.ok) throw new Error('Error cargando subcategorías');

      const data = await response.json();
      state.cache.subcategorias[cacheKey] = data.subcategorias || [];

      renderSubcategorias(state.cache.subcategorias[cacheKey]);
    } catch (error) {
      console.error('Error cargando subcategorías:', error);
      dom.subcategoriasList.innerHTML = `
        <li class="nav-item nav-error">Error al cargar subcategorías</li>
      `;
    }
  }

  /**
   * Renderizar subcategorías (sin agrupación por tipo ya que el modelo no tiene ese campo)
   */
  function renderSubcategorias(subcategorias) {
    dom.subcategoriasList.innerHTML = '';

    if (!subcategorias || subcategorias.length === 0) {
      dom.subcategoriasList.innerHTML = `
        <li class="nav-item nav-empty">No hay subcategorías disponibles</li>
      `;

      // Agregar enlace para ver categoría completa
      const verCatLi = document.createElement('li');
      verCatLi.className = 'nav-item';
      const verCatLink = document.createElement('a');
      verCatLink.href = `/catalogo/?categoria=${state.currentCategoria}`;
      verCatLink.className = 'nav-link nav-link-highlight';
      verCatLink.innerHTML = `<span>Ver toda la categoría</span>`;
      verCatLi.appendChild(verCatLink);
      dom.subcategoriasList.appendChild(verCatLi);
      return;
    }

    // Renderizar subcategorías directamente (sin agrupar por tipo)
    subcategorias.forEach((sub, index) => {
      const li = document.createElement('li');
      li.className = 'nav-item';
      li.style.animationDelay = `${0.1 + index * 0.03}s`;

      const link = document.createElement('a');
      link.href = `/catalogo/?subcategoria=${sub.id}`;
      link.className = 'nav-link';
      link.innerHTML = `
        ${sub.imagen ? `<img src="${sub.imagen}" alt="${sub.nombre}" class="sub-thumb">` : ''}
        <span>${sub.nombre}</span>
      `;

      li.appendChild(link);
      dom.subcategoriasList.appendChild(li);
    });

    // Agregar link "Ver todos" al final
    const verTodosLi = document.createElement('li');
    verTodosLi.className = 'nav-item';
    const verTodosLink = document.createElement('a');
    verTodosLink.href = `/catalogo/?categoria=${state.currentCategoria}`;
    verTodosLink.className = 'nav-link nav-link-highlight';
    verTodosLink.innerHTML = `<span>Ver toda la categoría</span>`;
    verTodosLi.appendChild(verTodosLink);
    dom.subcategoriasList.appendChild(verTodosLi);
  }

  // Exponer función de reset para uso externo
  window.navMenuReset = resetToMain;

})();
