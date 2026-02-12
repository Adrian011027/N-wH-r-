/**
 * Search Overlay - Sistema de búsqueda integrado en header
 * Búsqueda en tiempo real con resultados instantáneos
 */

class SearchOverlay {
  constructor() {
    // Elementos del DOM
    this.overlay = document.getElementById('search-overlay');
    this.input = document.getElementById('search-overlay-input');
    this.clearBtn = document.getElementById('search-clear-btn');
    this.closeBtn = document.getElementById('search-close-btn');
    this.btnSearch = document.getElementById('btn-search');
    this.btnSearchMobile = document.getElementById('btn-search-mobile'); // Botón móvil
    
    // Secciones de contenido
    this.suggestions = document.getElementById('search-suggestions');
    this.loading = document.getElementById('search-loading');
    this.results = document.getElementById('search-results');
    this.noResults = document.getElementById('search-no-results');
    this.resultsGrid = document.getElementById('search-results-grid');
    this.resultsCount = document.getElementById('search-results-count');
    this.viewAllLink = document.getElementById('search-view-all');
    
    // Estado
    this.isOpen = false;
    this.searchTimeout = null;
    this.currentQuery = '';
    this.minChars = 2;
    this.debounceTime = 300;
    
    // Inicializar
    this.init();
  }
  
  init() {
    if (!this.overlay || !this.input) {
      console.warn('SearchOverlay: Elementos no encontrados');
      return;
    }
    
    this.bindEvents();
  }
  
  bindEvents() {
    // Abrir buscador al hacer clic en el botón (desktop)
    this.btnSearch?.addEventListener('click', (e) => {
      e.preventDefault();
      this.open();
    });
    
    // Abrir buscador al hacer clic en el botón (móvil)
    this.btnSearchMobile?.addEventListener('click', (e) => {
      e.preventDefault();
      this.open();
    });
    
    // Cerrar buscador
    this.closeBtn?.addEventListener('click', () => this.close());
    
    // Cerrar con ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
    
    // Cerrar al hacer clic fuera del contenedor
    this.overlay?.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.close();
      }
    });
    
    // Input de búsqueda
    this.input?.addEventListener('input', () => this.handleInput());
    
    // Limpiar búsqueda
    this.clearBtn?.addEventListener('click', () => this.clearSearch());
    
    // Enter para ir a página de resultados completa
    this.input?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && this.currentQuery.length >= this.minChars) {
        this.goToSearchPage();
      }
    });
    
    // Tags de sugerencias
    document.querySelectorAll('.suggestion-tag').forEach(tag => {
      tag.addEventListener('click', () => {
        const query = tag.dataset.query;
        this.input.value = query;
        this.handleInput();
      });
    });
    
    // Ver todos los resultados
    this.viewAllLink?.addEventListener('click', (e) => {
      e.preventDefault();
      this.goToSearchPage();
    });
  }
  
  open() {
    this.isOpen = true;
    this.overlay.classList.add('active');
    document.body.classList.add('search-open');
    
    // Focus en el input después de la animación
    setTimeout(() => {
      this.input?.focus();
    }, 100);
    
    // Mostrar sugerencias si no hay búsqueda activa
    if (!this.currentQuery) {
      this.showSuggestions();
    }
  }
  
  close() {
    this.isOpen = false;
    this.overlay.classList.remove('active');
    document.body.classList.remove('search-open');
    
    // Limpiar después de cerrar
    setTimeout(() => {
      this.clearSearch();
    }, 300);
  }
  
  handleInput() {
    const query = this.input.value.trim();
    this.currentQuery = query;
    
    // Mostrar/ocultar botón de limpiar
    this.clearBtn.style.display = query.length > 0 ? 'flex' : 'none';
    
    // Cancelar búsqueda anterior
    clearTimeout(this.searchTimeout);
    
    if (query.length < this.minChars) {
      this.showSuggestions();
      return;
    }
    
    // Debounce para evitar muchas peticiones
    this.searchTimeout = setTimeout(() => {
      this.performSearch(query);
    }, this.debounceTime);
  }
  
  clearSearch() {
    this.input.value = '';
    this.currentQuery = '';
    this.clearBtn.style.display = 'none';
    this.showSuggestions();
    this.input?.focus();
  }
  
  showSuggestions() {
    this.hideAll();
    this.suggestions.style.display = 'block';
  }
  
  showLoading() {
    this.hideAll();
    this.loading.style.display = 'flex';
  }
  
  showResults() {
    this.hideAll();
    this.results.style.display = 'block';
  }
  
  showNoResults() {
    this.hideAll();
    this.noResults.style.display = 'flex';
  }
  
  hideAll() {
    this.suggestions.style.display = 'none';
    this.loading.style.display = 'none';
    this.results.style.display = 'none';
    this.noResults.style.display = 'none';
  }
  
  async performSearch(query) {
    this.showLoading();
    
    try {
      const params = new URLSearchParams({
        q: query,
        per_page: 8,
        disponibles: 'true'
      });
      
      const response = await fetch(`/api/search/?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error('Error en la búsqueda');
      }
      
      const data = await response.json();
      
      // Verificar que la query no haya cambiado mientras cargaba
      if (query !== this.currentQuery) return;
      
      if (data.productos.length === 0) {
        this.showNoResults();
      } else {
        this.renderResults(data);
      }
      
    } catch (error) {
      console.error('Error en búsqueda:', error);
      this.showNoResults();
    }
  }
  
  renderResults(data) {
    // Actualizar contador
    const total = data.total;
    this.resultsCount.textContent = `${total} resultado${total !== 1 ? 's' : ''}`;
    
    // Actualizar link de ver todos
    this.viewAllLink.href = `/buscar/?q=${encodeURIComponent(this.currentQuery)}`;
    
    // Limpiar grid
    this.resultsGrid.innerHTML = '';
    
    // Renderizar productos
    data.productos.forEach((producto, index) => {
      const card = this.createProductCard(producto, index);
      this.resultsGrid.appendChild(card);
    });
    
    this.showResults();
  }
  
  createProductCard(producto, index) {
    const genero = producto.genero?.toLowerCase() === 'mujer' ? 'dama' : 'caballero';
    const link = `/producto/${producto.id}/?from=${genero}`;
    
    const card = document.createElement('a');
    card.href = link;
    card.className = 'search-product-card';
    card.style.animationDelay = `${index * 0.05}s`;
    
    card.innerHTML = `
      <div class="search-product-image">
        <img src="${producto.imagen || '/static/images/no-image.jpg'}" 
             alt="${producto.nombre}" 
             loading="lazy">
        ${producto.en_oferta ? '<span class="search-product-badge">Oferta</span>' : ''}
      </div>
      <div class="search-product-info">
        <h4 class="search-product-name">${producto.nombre}</h4>
        <p class="search-product-price">$${producto.precio.toFixed(2)}</p>
        <p class="search-product-category">${producto.categoria}</p>
      </div>
    `;
    
    return card;
  }
  
  goToSearchPage() {
    if (this.currentQuery.length >= this.minChars) {
      window.location.href = `/buscar/?q=${encodeURIComponent(this.currentQuery)}`;
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  window.searchOverlay = new SearchOverlay();
});

// Exportar para uso en módulos si es necesario
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SearchOverlay;
}
