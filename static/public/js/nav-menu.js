/**
 * nav-menu.js
 * Menú elegante con navegación en cascada (Acordeón)
 * Despliega categorías en grid de 3 columnas dentro del mismo nivel
 */

(function() {
  'use strict';

  // Estado
  const state = {
    cache: {
      categorias: {}
    }
  };

  // DOM Elements
  const dom = {
    navMenu: null
  };

  // Inicializar
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    dom.navMenu = document.getElementById('nav-menu');
    
    if (!dom.navMenu) {
      console.warn('nav-menu.js: Menú no encontrado');
      return;
    }

    setupEventListeners();
    console.log('✅ Menú de navegación (Cascada) inicializado');
  }

  /**
   * Setup event listeners
   */
  function setupEventListeners() {
    // Género triggers (Expandir/Colapsar)
    document.querySelectorAll('.genero-trigger').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const li = trigger.closest('.nav-item-expandable');
        const genero = li?.dataset.genero;
        const container = li?.querySelector('.nav-categories-container');
        
        if (genero && container) {
          toggleGenero(li, genero, container);
        }
      });
    });

    // Cerrar menú al hacer clic fuera
    document.addEventListener('click', (e) => {
      if (dom.navMenu?.classList.contains('open') && 
          !e.target.closest('.nav-menu') && 
          !e.target.closest('#btn-burger')) {
        closeMenu();
      }
    });

    // Botón cerrar menú
    const btnClose = document.getElementById('btn-close-menu');
    if (btnClose) {
        btnClose.addEventListener('click', closeMenu);
    }
  }

  function closeMenu() {
      dom.navMenu.classList.remove('open');
      document.body.style.overflow = '';
  }

  async function toggleGenero(li, genero, container) {
    const isOpen = !container.classList.contains('hidden');

    if (isOpen) {
      container.classList.add('hidden');
      li.classList.remove('expanded');
    } else {
      container.classList.remove('hidden');
      li.classList.add('expanded');
      
      if (!container.dataset.loaded) {
          await loadCategorias(genero, container);
      }
    }
  }

  async function loadCategorias(genero, container) {
    console.log('📂 Cargando categorías para género:', genero);
    try {
      if (state.cache.categorias[genero]) {
        renderCategorias(state.cache.categorias[genero], container, genero);
        return;
      }

      const url = '/api/categorias-por-genero/?genero=' + genero;
      const response = await fetch(url);
      if (!response.ok) throw new Error('HTTP ' + response.status);

      const data = await response.json();
      state.cache.categorias[genero] = data.categorias || [];

      renderCategorias(state.cache.categorias[genero], container, genero);
    } catch (error) {
      console.error('❌ Error cargando categorías:', error);
      container.innerHTML = '<div class="nav-error">Error al cargar</div>';
    }
  }

  function renderCategorias(categorias, container, genero) {
    container.dataset.loaded = 'true';
    container.innerHTML = '';

    if (!categorias || categorias.length === 0) {
      container.innerHTML = '<div class="nav-empty">No hay categorías</div>';
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'nav-categories-grid';

    // Agregar opción "Ver Todo" al inicio
    const verTodoWrapper = document.createElement('div');
    verTodoWrapper.className = 'nav-category-item';
    
    const verTodoLink = document.createElement('a');
    verTodoLink.href = `/coleccion/${genero}/`;
    verTodoLink.className = 'nav-category-card nav-category-all';
    verTodoLink.innerHTML = `
      <span class="cat-name">Ver Todo</span>
      <svg class="nav-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    
    verTodoWrapper.appendChild(verTodoLink);
    grid.appendChild(verTodoWrapper);

    // Agregar categorías individuales
    categorias.forEach((cat) => {
      const cardWrapper = document.createElement('div');
      cardWrapper.className = 'nav-category-item';
      
      const card = document.createElement('div');
      card.className = 'nav-category-card';
      card.innerHTML = `
        <span class="cat-name">${cat.nombre}</span>
        <svg class="nav-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `;
      card.dataset.categoriaId = cat.id;
      card.dataset.genero = genero;
      
      // Al hacer clic, expandir subcategorías
      card.addEventListener('click', function(e) {
        e.preventDefault();
        toggleSubcategorias(cat.id, cat.nombre, genero, cardWrapper, card);
      });
      
      cardWrapper.appendChild(card);
      grid.appendChild(cardWrapper);
    });

    container.appendChild(grid);
  }

  async function toggleSubcategorias(categoriaId, categoriaNombre, genero, parentElement, card) {
    let subContainer = parentElement.querySelector('.nav-subcategories-container');
    
    if (subContainer) {
      // Ya existe, toggle visibility
      const isHidden = subContainer.classList.contains('hidden');
      subContainer.classList.toggle('hidden');
      card.classList.toggle('expanded');
      return;
    }
    
    // Marcar como expandido
    card.classList.add('expanded');
    
    // Crear contenedor de subcategorías
    subContainer = document.createElement('div');
    subContainer.className = 'nav-subcategories-container';
    subContainer.innerHTML = '<div class="loading-spinner"></div>';
    parentElement.appendChild(subContainer);
    
    // Cargar subcategorías
    await loadSubcategorias(categoriaId, genero, subContainer);
  }

  async function loadSubcategorias(categoriaId, genero, container) {
    console.log('📂 Cargando subcategorías para categoría:', categoriaId);
    try {
      const url = '/api/subcategorias-por-categoria/?categoria_id=' + categoriaId + '&genero=' + genero;
      const response = await fetch(url);
      if (!response.ok) throw new Error('HTTP ' + response.status);

      const data = await response.json();
      const subcategorias = data.subcategorias || [];

      renderSubcategorias(subcategorias, container, genero, categoriaId);
    } catch (error) {
      console.error('❌ Error cargando subcategorías:', error);
      container.innerHTML = '<div class="nav-error">Error al cargar subcategorías</div>';
    }
  }

  function renderSubcategorias(subcategorias, container, genero, categoriaId) {
    container.innerHTML = '';

    if (!subcategorias || subcategorias.length === 0) {
      container.innerHTML = '<div class="nav-empty">No hay subcategorías</div>';
      return;
    }

    const list = document.createElement('div');
    list.className = 'nav-subcategories-list';

    subcategorias.forEach((sub) => {
      const link = document.createElement('a');
      // Usar query params para filtrar por subcategoría
      link.href = '/coleccion/' + genero + '/?subcategoria=' + sub.id;
      link.className = 'nav-subcategory-link';
      link.innerHTML = sub.nombre;
      link.addEventListener('click', function() {
        closeMenu();
      });
      list.appendChild(link);
    });

    container.appendChild(list);
    container.classList.remove('hidden');
  }

})();
