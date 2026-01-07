/**
 * Carrusel de imágenes para detalle de producto
 * Auto-rotación cada 10 segundos
 * Controles: flechas prev/next, indicadores (dots)
 */

class ProductoCarrusel {
  constructor() {
    this.track = document.getElementById('carrusel-track');
    this.dotsContainer = document.getElementById('carrusel-dots');
    this.prevBtn = document.getElementById('carrusel-prev');
    this.nextBtn = document.getElementById('carrusel-next');
    
    if (!this.track) return; // Si no hay carrusel, salir
    
    this.slides = this.track.querySelectorAll('.carrusel-slide');
    this.totalSlides = this.slides.length;
    this.currentSlide = 0;
    this.autoplayInterval = null;
    this.AUTOPLAY_DELAY = 10000; // 10 segundos
    
    if (this.totalSlides <= 1) {
      // Si hay una o menos imágenes, no mostrar controles
      if (this.prevBtn) this.prevBtn.style.display = 'none';
      if (this.nextBtn) this.nextBtn.style.display = 'none';
      return;
    }
    
    this.init();
  }
  
  init() {
    // Crear indicadores (dots)
    this.createDots();
    
    // Listeners de botones
    if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.prevSlide());
    if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.nextSlide());
    
    // Listeners de dots
    const dots = this.dotsContainer.querySelectorAll('.carrusel-dot');
    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => this.goToSlide(index));
    });
    
    // Auto-play
    this.startAutoplay();
    
    // Pausar auto-play al hover y reanudar cuando se va el mouse
    const viewport = this.track.closest('.carrusel-viewport');
    if (viewport) {
      viewport.addEventListener('mouseenter', () => this.stopAutoplay());
      viewport.addEventListener('mouseleave', () => this.startAutoplay());
    }
    
    // Actualizar vista inicial
    this.updateCarousel();
  }
  
  createDots() {
    for (let i = 0; i < this.totalSlides; i++) {
      const dot = document.createElement('div');
      dot.className = 'carrusel-dot';
      if (i === 0) dot.classList.add('active');
      this.dotsContainer.appendChild(dot);
    }
  }
  
  prevSlide() {
    this.currentSlide = (this.currentSlide - 1 + this.totalSlides) % this.totalSlides;
    this.updateCarousel();
    this.resetAutoplay();
  }
  
  nextSlide() {
    this.currentSlide = (this.currentSlide + 1) % this.totalSlides;
    this.updateCarousel();
    this.resetAutoplay();
  }
  
  goToSlide(index) {
    if (index >= 0 && index < this.totalSlides) {
      this.currentSlide = index;
      this.updateCarousel();
      this.resetAutoplay();
    }
  }
  
  updateCarousel() {
    // Mover el track
    const translateX = -this.currentSlide * 100;
    this.track.style.transform = `translateX(${translateX}%)`;
    
    // Actualizar dots
    const dots = this.dotsContainer.querySelectorAll('.carrusel-dot');
    dots.forEach((dot, index) => {
      if (index === this.currentSlide) {
        dot.classList.add('active');
      } else {
        dot.classList.remove('active');
      }
    });
  }
  
  startAutoplay() {
    this.autoplayInterval = setInterval(() => {
      this.nextSlide();
    }, this.AUTOPLAY_DELAY);
  }
  
  stopAutoplay() {
    if (this.autoplayInterval) {
      clearInterval(this.autoplayInterval);
      this.autoplayInterval = null;
    }
  }
  
  resetAutoplay() {
    this.stopAutoplay();
    this.startAutoplay();
  }
  
  destroy() {
    this.stopAutoplay();
    if (this.prevBtn) this.prevBtn.removeEventListener('click', () => this.prevSlide());
    if (this.nextBtn) this.nextBtn.removeEventListener('click', () => this.nextSlide());
  }

  /**
   * Cambia las imágenes del carrusel dinámicamente
   * @param {Array<string>} imageUrls - Array de URLs de imágenes
   */
  changeImages(imageUrls) {
    if (!Array.isArray(imageUrls) || imageUrls.length === 0) {
      console.warn('No se proporcionaron imágenes válidas');
      return;
    }

    // Limpiar slides actuales
    this.track.innerHTML = '';

    // Crear nuevos slides
    imageUrls.forEach(url => {
      const slide = document.createElement('div');
      slide.className = 'carrusel-slide';
      const img = document.createElement('img');
      img.src = url;
      img.alt = 'Producto imagen';
      img.className = 'slide-img';
      slide.appendChild(img);
      this.track.appendChild(slide);
    });

    // Actualizar referencias
    this.slides = this.track.querySelectorAll('.carrusel-slide');
    this.totalSlides = this.slides.length;
    this.currentSlide = 0;

    // Limpiar y recrear dots
    this.dotsContainer.innerHTML = '';
    this.createDots();

    // Reattach listeners a dots
    const dots = this.dotsContainer.querySelectorAll('.carrusel-dot');
    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => this.goToSlide(index));
    });

    // Mostrar/ocultar botones según cantidad de imágenes
    if (this.totalSlides <= 1) {
      if (this.prevBtn) this.prevBtn.style.display = 'none';
      if (this.nextBtn) this.nextBtn.style.display = 'none';
    } else {
      if (this.prevBtn) this.prevBtn.style.display = '';
      if (this.nextBtn) this.nextBtn.style.display = '';
    }

    // Actualizar vista
    this.updateCarousel();
    this.resetAutoplay();
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  window.productoCarrusel = new ProductoCarrusel();
});
