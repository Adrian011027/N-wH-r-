/**
 * nav-menu.js
 * Menú estilo Louis Vuitton - Navegación en cascada de 3 niveles
 * Nivel 1: Géneros → Nivel 2: Categorías → Nivel 3: Subcategorías
 */

(function() {
  'use strict';

  // Estado
  const state = {
    cache: {
      categorias: {},
      subcategorias: {}
    },
    currentGenero: null,
    currentCategoria: null
  };

  // DOM Elements
  const dom = {
    navMenu: null,
    panelCategories: null,
    panelSubcategories: null,
    categoriesContent: null,
    subcategoriesContent: null,
    categoriesTitle: null,
    subcategoriesTitle: null,
    backToMain: null,
    backToCategories: null
  };

  // Inicializar
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    dom.navMenu = document.getElementById('nav-menu');
    dom.panelCategories = document.getElementById('lv-panel-categories');
    dom.panelSubcategories = document.getElementById('lv-panel-subcategories');
    dom.categoriesContent = document.getElementById('lv-categories-content');
    dom.subcategoriesContent = document.getElementById('lv-subcategories-content');
    dom.categoriesTitle = document.getElementById('lv-categories-title');
    dom.subcategoriesTitle = document.getElementById('lv-subcategories-title');
    dom.backToMain = document.getElementById('lv-back-to-main');
    dom.backToCategories = document.getElementById('lv-back-to-categories');
    
    if (!dom.navMenu || !dom.panelCategories || !dom.panelSubcategories) {
      console.warn('nav-menu.js: Elementos del menú no encontrados');
      return;
    }

    setupEventListeners();
    
  }

  /**
   * Setup event listeners
   */
  function setupEventListeners() {
    // Género triggers - abrir panel de categorías
    document.querySelectorAll('.genero-trigger').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const genero = trigger.dataset.genero;
        
        if (genero) {
          openCategoriesPanel(genero);
        }
      });
    });

    // Botón volver a géneros
    if (dom.backToMain) {
      dom.backToMain.addEventListener('click', () => {
        closeCategoriesPanel();
      });
    }

    // Botón volver a categorías
    if (dom.backToCategories) {
      dom.backToCategories.addEventListener('click', () => {
        closeSubcategoriesPanel();
      });
    }

    // Cerrar menú al hacer clic fuera
    document.addEventListener('click', (e) => {
      if (dom.navMenu?.classList.contains('open') && 
          !e.target.closest('.nav-menu') && 
          !e.target.closest('.lv-panel') &&
          !e.target.closest('#btn-burger')) {
        closeAllPanels();
      }
    });

    // Botón cerrar menú principal
    const btnClose = document.getElementById('btn-close-menu');
    if (btnClose) {
        btnClose.addEventListener('click', closeAllPanels);
    }
  }

  function closeAllPanels() {
    // Cerrar paneles de categorías y subcategorías
    dom.panelCategories.classList.remove('active');
    dom.panelSubcategories.classList.remove('active');
    
    // Cerrar menú principal (replicando la función cerrarMenu de main.js)
    dom.navMenu.classList.remove('open', 'has-active-panel');
    
    // Cerrar overlay si existe
    const overlay = document.querySelector('.page-overlay');
    const burger = document.getElementById('btn-burger');
    if (overlay) overlay.classList.remove('active');
    if (burger) burger.classList.remove('active');
    
    // Restaurar scroll
    document.body.classList.remove('no-scroll');
    document.body.style.overflow = '';
    
    // Limpiar estado
    state.currentGenero = null;
    state.currentCategoria = null;
  }

  function closeCategoriesPanel() {
    dom.panelCategories.classList.remove('active');
    dom.navMenu.classList.remove('has-active-panel');
    closeSubcategoriesPanel();
  }

  function closeSubcategoriesPanel() {
    dom.panelSubcategories.classList.remove('active');
  }

  async function openCategoriesPanel(genero) {
    state.currentGenero = genero;
    
    // Actualizar título
    dom.categoriesTitle.textContent = genero.charAt(0).toUpperCase() + genero.slice(1);
    
    // Mostrar panel de categorías
    dom.panelCategories.classList.add('active');
    
    // En móvil, ocultar el nav-menu principal
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      dom.navMenu.classList.add('has-active-panel');
    }
    
    // Mostrar loading
    dom.categoriesContent.innerHTML = `
      <div class="lv-loading">
        <div class="lv-loading-spinner"></div>
        <div class="lv-loading-text">Cargando categorías...</div>
      </div>
    `;
    
    // Cargar categorías
    await loadCategorias(genero);
  }

  async function loadCategorias(genero) {
    console.log('📂 Cargando categorías para género:', genero);
    try {
      // Usar caché si existe
      if (state.cache.categorias[genero]) {
        renderCategorias(state.cache.categorias[genero], genero);
        return;
      }

      const url = '/api/categorias-por-genero/?genero=' + genero;
      const response = await fetch(url);
      if (!response.ok) throw new Error('HTTP ' + response.status);

      const data = await response.json();
      state.cache.categorias[genero] = data.categorias || [];

      renderCategorias(state.cache.categorias[genero], genero);
    } catch (error) {
      console.error('❌ Error cargando categorías:', error);
      dom.categoriesContent.innerHTML = '<div class="lv-loading"><div class="lv-loading-text" style="color: #e74c3c;">Error al cargar categorías</div></div>';
    }
  }

  function renderCategorias(categorias, genero) {
    dom.categoriesContent.innerHTML = '';

    if (!categorias || categorias.length === 0) {
      dom.categoriesContent.innerHTML = '<div class="lv-loading"><div class="lv-loading-text">No hay categorías disponibles</div></div>';
      return;
    }

    // Agregar imagen de banner del género
    const banner = document.createElement('div');
    banner.className = 'lv-gender-banner';
    
    // Imágenes temporales de Unsplash (puedes cambiarlas después)
    const generoImages = {
      'hombre': 'https://images.unsplash.com/photo-1490578474895-699cd4e2cf59?w=800&h=400&fit=crop',
      'mujer': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800&h=400&fit=crop'
    };
    
    const imageUrl = generoImages[genero.toLowerCase()] || '';
    
    if (imageUrl) {
      banner.innerHTML = `
        <img src="${imageUrl}" alt="${genero}" class="lv-gender-banner-img" onerror="this.parentElement.style.display='none'">
      `;
      dom.categoriesContent.appendChild(banner);
    }

    // Lista de categorías
    const list = document.createElement('ul');
    list.className = 'lv-categories-list';

    // Agregar opción "TODO" al inicio
    const todoItem = document.createElement('li');
    todoItem.className = 'lv-category-item';
    
    const todoButton = document.createElement('button');
    todoButton.className = 'lv-category-trigger';
    todoButton.innerHTML = `
      <span class="cat-name">TODO</span>
      <svg class="lv-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <polyline points="9 18 15 12 9 6"></polyline>
      </svg>
    `;
    
    // Click handler - redirigir a la página de género completo
    todoButton.addEventListener('click', function(e) {
      e.preventDefault();
      window.location.href = '/coleccion/' + genero + '/';
      closeAllPanels();
    });
    
    todoItem.appendChild(todoButton);
    list.appendChild(todoItem);

    categorias.forEach((cat) => {
      const item = document.createElement('li');
      item.className = 'lv-category-item';
      
      // Botón de categoría
      const button = document.createElement('button');
      button.className = 'lv-category-trigger';
      button.dataset.categoriaId = cat.id;
      button.dataset.categoriaNombre = cat.nombre;
      button.dataset.genero = genero;
      button.innerHTML = `
        <span class="cat-name">${cat.nombre}</span>
        <svg class="lv-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      `;
      
      // Click handler - navegar al panel de subcategorías
      button.addEventListener('click', function(e) {
        e.preventDefault();
        openSubcategoriesPanel(cat.id, cat.nombre, genero);
      });
      
      item.appendChild(button);
      list.appendChild(item);
    });

    dom.categoriesContent.appendChild(list);
  }

  async function openSubcategoriesPanel(categoriaId, categoriaNombre, genero) {
    state.currentCategoria = categoriaId;
    
    // Actualizar título
    dom.subcategoriesTitle.textContent = categoriaNombre;
    
    // Mostrar panel de subcategorías
    dom.panelSubcategories.classList.add('active');
    
    // Mostrar loading
    dom.subcategoriesContent.innerHTML = `
      <div class="lv-loading">
        <div class="lv-loading-spinner"></div>
        <div class="lv-loading-text">Cargando subcategorías...</div>
      </div>
    `;
    
    // Cargar subcategorías
    await loadSubcategorias(categoriaId, genero);
  }

  async function loadSubcategorias(categoriaId, genero) {
    console.log('📂 Cargando subcategorías para categoría:', categoriaId);
    
    const cacheKey = `${genero}-${categoriaId}`;
    
    try {
      // Usar caché si existe
      if (state.cache.subcategorias[cacheKey]) {
        renderSubcategorias(state.cache.subcategorias[cacheKey], genero);
        return;
      }

      const url = '/api/subcategorias-por-categoria/?categoria_id=' + categoriaId + '&genero=' + genero;
      const response = await fetch(url);
      if (!response.ok) throw new Error('HTTP ' + response.status);

      const data = await response.json();
      const subcategorias = data.subcategorias || [];
      
      state.cache.subcategorias[cacheKey] = subcategorias;
      renderSubcategorias(subcategorias, genero);
    } catch (error) {
      console.error('❌ Error cargando subcategorías:', error);
      dom.subcategoriesContent.innerHTML = '<div class="lv-loading"><div class="lv-loading-text" style="color: #e74c3c;">Error al cargar subcategorías</div></div>';
    }
  }

  function renderSubcategorias(subcategorias, genero) {
    dom.subcategoriesContent.innerHTML = '';

    if (!subcategorias || subcategorias.length === 0) {
      dom.subcategoriesContent.innerHTML = '<div class="lv-loading"><div class="lv-loading-text">No hay subcategorías disponibles</div></div>';
      return;
    }

    const list = document.createElement('ul');
    list.className = 'lv-subcategories-list';

    // Agregar opción "TODO" al inicio
    const todoItem = document.createElement('li');
    todoItem.className = 'lv-subcategory-item lv-subcategory-todo';
    
    const todoTitle = document.createElement('h3');
    todoTitle.className = 'lv-subcat-title';
    todoTitle.textContent = 'TODO';
    
    const todoGrid = document.createElement('div');
    todoGrid.className = 'lv-subcat-products-grid';
    
    // Crear 2 productos aleatorios de todas las subcategorías
    for (let i = 0; i < 2; i++) {
      const link = document.createElement('a');
      link.href = '/coleccion/' + genero + '/?categoria=' + state.currentCategoria;
      link.className = 'lv-subcategory-card';
      
      link.innerHTML = `
        <div class="lv-subcat-image-wrapper">
          <div class="lv-subcat-image-placeholder">
            <div class="lv-loading-spinner-small"></div>
          </div>
        </div>
      `;
      
      // Cargar producto aleatorio de cualquier subcategoría
      const randomSub = subcategorias[Math.floor(Math.random() * subcategorias.length)];
      loadRandomProductImage(randomSub.id, link);
      
      link.addEventListener('click', function() {
        closeAllPanels();
      });
      
      todoGrid.appendChild(link);
    }
    
    todoItem.appendChild(todoTitle);
    todoItem.appendChild(todoGrid);
    list.appendChild(todoItem);

    subcategorias.forEach((sub) => {
      const item = document.createElement('li');
      item.className = 'lv-subcategory-item';
      
      // Título de la subcategoría centrado arriba
      const title = document.createElement('h3');
      title.className = 'lv-subcat-title';
      title.textContent = sub.nombre;
      
      // Grid de productos (2 columnas)
      const productsGrid = document.createElement('div');
      productsGrid.className = 'lv-subcat-products-grid';
      
      // Crear 2 productos para esta subcategoría
      for (let i = 0; i < 2; i++) {
        const link = document.createElement('a');
        link.href = '/coleccion/' + genero + '/?subcategoria=' + sub.id;
        link.className = 'lv-subcategory-card';
        
        link.innerHTML = `
          <div class="lv-subcat-image-wrapper">
            <div class="lv-subcat-image-placeholder">
              <div class="lv-loading-spinner-small"></div>
            </div>
          </div>
        `;
        
        // Cargar producto aleatorio
        loadRandomProductImage(sub.id, link);
        
        // Cerrar menú al hacer clic
        link.addEventListener('click', function() {
          closeAllPanels();
        });
        
        productsGrid.appendChild(link);
      }
      
      item.appendChild(title);
      item.appendChild(productsGrid);
      list.appendChild(item);
    });

    dom.subcategoriesContent.appendChild(list);
  }

  // Función para cargar imagen de producto aleatorio
  async function loadRandomProductImage(subcategoriaId, linkElement) {
    try {
      const response = await fetch(`/api/producto-aleatorio-subcategoria/?subcategoria_id=${subcategoriaId}`);
      if (!response.ok) {
        // Si no hay endpoint, usar una imagen placeholder
        updateProductImage(linkElement, null);
        return;
      }
      
      const data = await response.json();
      const producto = data.producto;
      
      if (producto && producto.imagen) {
        updateProductImage(linkElement, producto.imagen);
      } else {
        updateProductImage(linkElement, null);
      }
    } catch (error) {
      console.log('No se pudo cargar producto aleatorio:', error);
      updateProductImage(linkElement, null);
    }
  }

  function updateProductImage(linkElement, imageUrl) {
    const wrapper = linkElement.querySelector('.lv-subcat-image-wrapper');
    if (!wrapper) return;
    
    if (imageUrl) {
      wrapper.innerHTML = `<img src="${imageUrl}" alt="Producto" class="lv-subcat-image">`;
    } else {
      // Imagen placeholder con gradiente
      wrapper.innerHTML = `<div class="lv-subcat-image-placeholder-empty"></div>`;
    }
  }

})();
