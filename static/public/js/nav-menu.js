/**
 * nav-menu.js
 * Carga dinámica del menú de navegación con géneros y categorías
 */

(function() {
  'use strict';

  // Cargar el menú al cargar la página
  document.addEventListener('DOMContentLoaded', loadNavMenu);

  async function loadNavMenu() {
    try {
      const response = await fetch('/api/nav-menu/');
      if (!response.ok) {
        throw new Error('Error al cargar el menú');
      }

      const data = await response.json();
      renderNavMenu(data.generos);
    } catch (error) {
      console.error('Error cargando menú:', error);
      // Mantener el menú estático si falla
    }
  }

  function renderNavMenu(generos) {
    const menuContainer = document.querySelector('.nav-menu .menu');
    if (!menuContainer) return;

    // Limpiar menú actual (excepto botón de cierre)
    menuContainer.innerHTML = '';

    // Agregar "Inicio"
    const inicioItem = document.createElement('li');
    inicioItem.innerHTML = '<a href="/">Inicio</a>';
    menuContainer.appendChild(inicioItem);

    // Agregar cada género con sus categorías
    generos.forEach(genero => {
      const li = document.createElement('li');
      li.className = 'menu-item-with-submenu';

      // Link principal del género (puede ser clickeable o solo toggle)
      const generoLink = document.createElement('a');
      generoLink.href = `/coleccion/${genero.slug}/`;
      generoLink.textContent = genero.nombre;
      generoLink.className = 'genero-link';

      // Botón toggle para desplegar categorías
      const toggleBtn = document.createElement('button');
      toggleBtn.className = 'submenu-toggle';
      toggleBtn.setAttribute('aria-label', `Ver categorías de ${genero.nombre}`);
      toggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" 
             fill="none" stroke="currentColor" stroke-width="2" 
             stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      `;

      // Contenedor de categorías (submenú)
      const submenu = document.createElement('ul');
      submenu.className = 'submenu';

      // Agregar "Ver todo" del género
      const verTodoItem = document.createElement('li');
      verTodoItem.innerHTML = `<a href="/coleccion/${genero.slug}/">Ver todo ${genero.nombre}</a>`;
      submenu.appendChild(verTodoItem);

      // Agregar cada categoría
      genero.categorias.forEach(categoria => {
        const catItem = document.createElement('li');
        catItem.innerHTML = `
          <a href="/coleccion/${genero.slug}/?categoria=${categoria.slug}">
            ${categoria.nombre}
            <span class="count">(${categoria.count})</span>
          </a>
        `;
        submenu.appendChild(catItem);
      });

      // Construir el elemento completo
      const itemWrapper = document.createElement('div');
      itemWrapper.className = 'menu-item-header';
      itemWrapper.appendChild(generoLink);
      
      // Solo agregar toggle si hay categorías
      if (genero.categorias.length > 0) {
        itemWrapper.appendChild(toggleBtn);
      }

      li.appendChild(itemWrapper);
      
      if (genero.categorias.length > 0) {
        li.appendChild(submenu);
      }

      menuContainer.appendChild(li);

      // Event listener para toggle
      if (genero.categorias.length > 0) {
        toggleBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          toggleSubmenu(li);
        });
      }
    });

    // Agregar "Ver Todo"
    const todoItem = document.createElement('li');
    todoItem.innerHTML = '<a href="/coleccion/todo/">Ver Todo</a>';
    menuContainer.appendChild(todoItem);
  }

  function toggleSubmenu(menuItem) {
    const wasOpen = menuItem.classList.contains('submenu-open');
    
    // Cerrar todos los otros submenús
    document.querySelectorAll('.menu-item-with-submenu').forEach(item => {
      item.classList.remove('submenu-open');
    });

    // Toggle el submenú actual
    if (!wasOpen) {
      menuItem.classList.add('submenu-open');
    }
  }

  // Cerrar submenús al hacer clic fuera
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.menu-item-with-submenu')) {
      document.querySelectorAll('.menu-item-with-submenu').forEach(item => {
        item.classList.remove('submenu-open');
      });
    }
  });

})();
