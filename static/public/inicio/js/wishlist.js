/* ==========================================================================
 * Wishlist Module
 * Invitado + Multi-usuario con selector de tallas y carrito invitado
 * ======================================================================== */

export function initWishlist({
  selector          = '.wishlist-btn',
  storageKey        = 'wishlist_ids',
  backendURL        = '/api/wishlist/',
  csrfToken         = null,
  isAuthenticated   = false,
  fetchProductoURL  = '/api/productos_por_ids/?ids=',
  clienteId         = null
} = {}) {

  const IS_GUEST_ID   = 0;
  const safeClienteId = clienteId ?? IS_GUEST_ID;

  const keyUser = (isAuthenticated && clienteId)
    ? `${storageKey}_${clienteId}`
    : `${storageKey}_guest`;

  const getList = () => {
    try { return JSON.parse(localStorage.getItem(keyUser)) || []; }
    catch { return []; }
  };

  const setList = list => {
    localStorage.setItem(keyUser, JSON.stringify(list));
    updateHeaderUI(list);
  };

  /* ========== Migración invitado → usuario ========== */
  if (isAuthenticated && clienteId) {
    try {
      const guestRaw = localStorage.getItem(`${storageKey}_guest`);
      const userRaw  = localStorage.getItem(keyUser);

      const merged = [...new Set([
        ...(JSON.parse(userRaw  || '[]')),
        ...(JSON.parse(guestRaw || '[]'))
      ])];

      localStorage.setItem(keyUser, JSON.stringify(merged));
      localStorage.removeItem(`${storageKey}_guest`);

      if (guestRaw) {
        for (const id of JSON.parse(guestRaw)) {
          // 🔐 JWT: fetchPost agrega token automáticamente
          fetchPost(`${backendURL}${clienteId}/`, { producto_id: id })
            .catch(console.error);
        }
      }
    } catch {}
  } else {
    Object.keys(localStorage)
      .filter(k => k.startsWith(storageKey) && !k.endsWith('_guest'))
      .forEach(k => localStorage.removeItem(k));
  }

  /* ========== DOM Refs ========== */
  const dom = {
    wishlistPanel   : document.getElementById('wishlist-panel'),
    // Contenedor principal: primero buscar en panel separado, luego en cascada
    wishlistContent : document.querySelector('#wishlist-panel .wishlist-header-content') 
                     || document.querySelector('#view-cliente-wishlist .wishlist-content'),
    // También referencia al contenedor de cascada para renderizar en ambos
    wishlistCascade : document.querySelector('#view-cliente-wishlist .wishlist-content'),
    overlay         : document.querySelector('.page-overlay'),
    wishlistBtn     : document.getElementById('btn-wishlist-panel'),
    closeBtn        : document.getElementById('close-wishlist-header'), // Botón X del panel separado
    wishlistIcon    : document.querySelector('#btn-wishlist-panel i'),
    wishlistCount   : document.querySelector('#btn-wishlist-panel .wishlist-count'),
    headerTitle     : document.getElementById('wishlist-header-title')
  };

  const toggleBtn = (btn, on) => {
    btn.classList.toggle('active', on);
    const ic = btn.querySelector('i');
    ic?.classList.toggle('fa-solid',   on);
    ic?.classList.toggle('fa-regular', !on);
  };

  const updateHeaderUI = list => {
    const { wishlistIcon, wishlistCount } = dom;
    const count = list.length;

    // Ícono principal (btn del panel)
    if (wishlistIcon) {
      wishlistIcon.classList.toggle('fa-solid', !!count);
      wishlistIcon.classList.toggle('fa-regular', !count);
      wishlistIcon.style.color = count ? '#ff4d6d' : '';
    }

    // Contador badge
    if (wishlistCount) {
      const prev = parseInt(wishlistCount.textContent, 10) || 0;
      wishlistCount.textContent = count;
      wishlistCount.hidden = !count;

      if (count !== prev) {
        wishlistCount.classList.remove('changed');
        void wishlistCount.offsetWidth; // ⚡ reflow para reiniciar animación
        wishlistCount.classList.add('changed');
      }
    }

    // Actualizar también el icono independiente del header
    const headerHeart = document.getElementById('icon-wishlist-header');
    if (headerHeart) {
      headerHeart.classList.toggle('active', !!count);
    }
  };

  /* ========== Hidratación inicial ========== */
  let hydrateDoneResolve;
  const hydrateDone = new Promise(res => (hydrateDoneResolve = res));

  (async () => {
    let validIds = [];
    
    if (isAuthenticated && clienteId) {
      try {
        // 🔐 JWT: fetchGet agrega token automáticamente
        const r = await fetchGet(`${backendURL}${clienteId}/`);
        if (r.ok) {
          const { productos = [] } = await r.json();
          validIds = productos.map(String);
          setList([...new Set([...getList(), ...validIds])]);
        }
      } catch (err) { console.error('[Wishlist] pull', err); }
    } else {
      // ✅ Validar IDs de invitado contra la BD
      const guestIds = getList();
      if (guestIds.length) {
        try {
          const r = await fetchGet(`${fetchProductoURL}${guestIds.join(',')}`);
          if (r.ok) {
            const { productos = [] } = await r.json();
            validIds = productos.map(p => String(p.id));
            // Si hay IDs inválidos, limpiar localStorage
            if (validIds.length !== guestIds.length) {
              setList(validIds);
            }
          }
        } catch (err) { 
          console.error('[Wishlist] validate guest', err); 
          validIds = guestIds; // Fallback: usar los IDs locales
        }
      }
    }

    const idsSet = new Set(getList());
    document.querySelectorAll(selector)
      .forEach(btn => toggleBtn(btn, idsSet.has(btn.dataset.productId)));

    // Forzar actualización inicial de contador
    updateHeaderUI(getList());

    hydrateDoneResolve();
  })();

  /* ========== Panel toggle ========== */
  const showWishlist = async () => {
    await hydrateDone;
    renderWishlistPanel();
    dom.wishlistPanel.classList.add('open');
    dom.overlay.classList.add('active');
  };
  const hideWishlist = () => {
    closeSizePicker(dom.wishlistPanel.querySelector('.size-picker'), 'side');
    dom.wishlistPanel.classList.remove('open');
    dom.overlay.classList.remove('active');
  };
  dom.wishlistBtn ?.addEventListener('click', showWishlist);
  dom.closeBtn    ?.addEventListener('click', hideWishlist);
  dom.overlay     ?.addEventListener('click', hideWishlist);

  /* ========== Corazones catálogo ========== */
  document.body.addEventListener('click', e => {
    const heart = e.target.closest(selector);
    if (!heart) return;

    const id = heart.dataset.productId;
    let list = getList();
    const add = !heart.classList.contains('active');

    toggleBtn(heart, add);

    if (add) {
      list.push(id);
    } else {
      list = list.filter(x => x !== id);
    }

    setList(list);
    updateHeaderUI(list);

    if (!isAuthenticated) return;
    
    // 🔐 JWT: Usa fetchWithAuth en lugar de fetch manual
    const method = add ? 'POST' : 'DELETE';
    fetchWithAuth(`${backendURL}${clienteId}/`, {
      method,
      body: JSON.stringify({ producto_id: id })
    }).catch(console.error);
  });

  /* ========== Eventos dentro del panel ========== */
  dom.wishlistPanel?.addEventListener('click', async e => {
    // Mini-carrusel de imágenes
    const miniPrev = e.target.closest('.carrusel-mini-prev');
    const miniNext = e.target.closest('.carrusel-mini-next');
    
    if (miniPrev || miniNext) {
      const viewport = (miniPrev || miniNext).closest('.carrusel-mini-viewport');
      const track = viewport?.querySelector('.carrusel-mini-track');
      const slides = track?.querySelectorAll('.carrusel-mini-slide');
      
      if (track && slides && slides.length > 1) {
        let currentIndex = 0;
        const transform = track.style.transform;
        const match = transform.match(/translateX\((-?\d+)%\)/);
        if (match) {
          currentIndex = Math.abs(parseInt(match[1]) / 100);
        }
        
        if (miniNext) {
          currentIndex = (currentIndex + 1) % slides.length;
        } else {
          currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        }
        
        track.style.transform = `translateX(-${currentIndex * 100}%)`;
      }
      return;
    }

    const pickerOpen = dom.wishlistPanel.querySelector('.size-picker');
    if (pickerOpen && !e.target.closest('.size-picker') &&
                      !e.target.matches('.btn-carrito-mini')) {
      closeSizePicker(pickerOpen, 'down');
    }

    // Eliminar de favoritos
    if (e.target.closest('.btn-remove-wishlist')) {
      const btn = e.target.closest('.btn-remove-wishlist');
      const pid = btn.dataset.id;
      
      // Remover visualmente
      const card = btn.closest('.wishlist-item');
      card.style.opacity = '0';
      card.style.transform = 'translateX(20px)';
      
      setTimeout(() => {
        // Actualizar localStorage
        let list = getList();
        list = list.filter(x => x !== pid);
        setList(list);
        
        // Actualizar backend si está autenticado
        if (isAuthenticated && clienteId) {
          fetchWithAuth(`${backendURL}${clienteId}/`, {
            method: 'DELETE',
            body: JSON.stringify({ producto_id: pid })
          }).catch(console.error);
        }
        
        // Actualizar corazones del catálogo
        document.querySelectorAll(`${selector}[data-product-id="${pid}"]`)
          .forEach(heart => toggleBtn(heart, false));
        
        // Re-renderizar panel
        renderWishlistPanel();
      }, 300);
      
      return;
    }

    if (e.target.matches('.btn-carrito-mini')) {
      const pid = e.target.dataset.id;
      if (pickerOpen && pickerOpen.dataset.productId === pid) {
        closeSizePicker(pickerOpen, 'down'); return;
      }
      pickerOpen && closeSizePicker(pickerOpen, 'down');

      let tallas = [];
      try {
        // 🔐 Endpoint público, no requiere token pero fetchGet es compatible
        const r = await fetchGet(`/api/productos/${pid}/`);
        tallas = (await r.json()).tallas || ['Única'];
      } catch { tallas = ['Única']; }

      const picker = document.createElement('div');
      picker.className = 'size-picker slide-up-full';
      picker.dataset.productId = pid;
      picker.innerHTML = `
        <div class="size-picker-inner">
          <h3>Selecciona tu talla</h3>
          <div class="size-options">
            ${tallas.map(t => `<button class="size-option" data-size="${t}">${t}</button>`).join('')}
          </div>
          <button class="close-size-picker">✕</button>
        </div>`;
      dom.wishlistPanel.appendChild(picker);

      const r = dom.wishlistPanel.getBoundingClientRect();
      picker.style.left  = `${r.left}px`;
      picker.style.width = `${r.width}px`;
      dom.wishlistPanel.dataset.prevOverflow = dom.wishlistPanel.style.overflowY || '';
      dom.wishlistPanel.style.overflowY = 'hidden';
      dom.wishlistContent.classList.add('blurred');
    }

    if (e.target.matches('.size-option')) {
      const talla = e.target.dataset.size;
      const pid   = e.target.closest('.size-picker').dataset.productId;
      e.target.classList.add('chosen');
      await addToCart(pid, talla, 1);
      setTimeout(() => closeSizePicker(
        e.target.closest('.size-picker'), 'down'), 160);
    }

    if (e.target.matches('.close-size-picker')) {
      closeSizePicker(e.target.closest('.size-picker'), 'down');
    }
  });

  /* ========== Utils ========== */
  function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => toast.classList.remove('show'), 2500);
    setTimeout(() => toast.remove(), 3000);
  }

  async function addToCart(pid, talla, cant = 1) {
    try {
      // 🔐 JWT: fetchPost agrega token automáticamente
      const r = await fetchPost(`/api/carrito/create/${safeClienteId}/`, {
        producto_id: pid,
        talla,
        cantidad: cant
      });
      
      if (!r.ok) throw new Error(await r.text());
      console.log('🛒', await r.json());

      const card = dom.wishlistPanel.querySelector(
        `.wishlist-item .btn-carrito-mini[data-id="${pid}"]`
      )?.closest('.wishlist-item');

      if (card) {
        const actions = card.querySelector('.wishlist-actions');
        const btn = actions.querySelector('.btn-carrito-mini');
        if (btn) {
          btn.classList.add('fade-out');
          btn.addEventListener('animationend', () => {
            btn.remove();
            const span = document.createElement('span');
            span.className = 'in-cart-note fade-in';
            span.textContent = 'Ya en carrito';
            actions.appendChild(span);
          }, { once: true });
        }
      }

      showToast('Producto agregado al carrito');
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    } catch (err) {
      alert('No se pudo agregar.\n' + err.message);
    }
  }

  function closeSizePicker(node, dir = 'down') {
    if (!node) return;
    node.classList.add(dir === 'side' ? 'fade-out-side' : 'fade-out-down');
    dom.wishlistPanel.style.overflowY =
      dom.wishlistPanel.dataset.prevOverflow || 'auto';
    delete dom.wishlistPanel.dataset.prevOverflow;
    dom.wishlistContent.classList.remove('blurred');
    node.addEventListener('animationend', () => node.remove(), { once: true });
  }

  /* ========== Render panel ========== */
  async function getCartIds() {
    if (!isAuthenticated) return new Set();
    try {
      // 🔐 JWT: fetchGet agrega token automáticamente
      const r = await fetchGet(`/api/carrito/${clienteId}/`);
      if (!r.ok) throw new Error(r.status);
      const { items = [] } = await r.json();
      return new Set(items.map(it => String(it.producto_id)));
    } catch (err) {
      console.error(err);
      return new Set();
    }
  }

  const buildCards = (prods, inCart = new Set()) => prods.map(p => `
    <div class="wishlist-item" data-id="${p.id}">
      <div class="wishlist-img-col">
        ${(() => {
          const imagenes = p.imagenes_galeria || [];
          const allImages = [p.imagen, ...imagenes].filter(Boolean);
          if (allImages.length > 1) {
            return `
              <div class="carrusel-mini-viewport">
                <div class="carrusel-mini-track" style="transform: translateX(0%);">
                  ${allImages.map(img => `<img src="${img}" alt="${p.nombre}" class="carrusel-mini-slide">`).join('')}
                </div>
                <button class="carrusel-mini-prev" data-product-id="${p.id}">‹</button>
                <button class="carrusel-mini-next" data-product-id="${p.id}">›</button>
              </div>
            `;
          } else {
            return `<img src="${p.imagen}" alt="${p.nombre}" onerror="this.src='/static/images/placeholder.png'">`;
          }
        })()}
      </div>
      <div class="wishlist-info-col">
        <h4 class="nombre">${p.nombre}</h4>
        <p class="precio">$${parseFloat(p.precio).toFixed(2)}</p>
      </div>
      <div class="wishlist-actions">
        ${inCart.has(String(p.id))
          ? `<span class="in-cart-note"><i class="fa-solid fa-check"></i></span>`
          : `<button class="btn-carrito-mini" data-id="${p.id}" title="Agregar al carrito">
              <i class="fa-solid fa-cart-plus"></i>
            </button>`
        }
        <button class="btn-remove-wishlist" data-id="${p.id}" title="Eliminar de favoritos">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>
    </div>
  `).join('');

  // Helper para renderizar en un contenedor específico
  function renderToContainer(container, html) {
    if (container) container.innerHTML = html;
  }

  async function renderWishlistPanel() {
    const ids = getList();
    const containers = [dom.wishlistContent, dom.wishlistCascade].filter(Boolean);
    
    if (!ids.length) {
      const emptyHTML = isAuthenticated ? EMPTY_USER : EMPTY_GUEST;
      containers.forEach(c => renderToContainer(c, emptyHTML));
      updateHeaderUI([]);
      return;
    }

    try {
      containers.forEach(c => c.textContent = 'Cargando…');
      const url = isAuthenticated
        ? `${backendURL}${safeClienteId}/?full=true`
        : `${fetchProductoURL}${ids.join(',')}`;
      
      // 🔐 JWT: fetchGet agrega token automáticamente si el usuario está logueado
      const { productos = [] } = await (await fetchGet(url)).json();
      const inCart = await getCartIds();

      // ✅ Sincronizar localStorage con productos que realmente existen
      const validIds = productos.map(p => String(p.id));
      if (validIds.length !== ids.length) {
        setList(validIds); // Actualiza localStorage con solo IDs válidos
      }

      const resultHTML = productos.length
        ? buildCards(productos, inCart)
        : 'No tienes productos en tu wishlist.';
      
      containers.forEach(c => renderToContainer(c, resultHTML));
      updateHeaderUI(validIds);
    } catch (err) {
      containers.forEach(c => c.textContent = 'Error al cargar tu wishlist.');
    }

    if (!isAuthenticated) injectHint();
  }

  const EMPTY_ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="1.2"
         stroke-linecap="round" stroke-linejoin="round">
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z"/>
    </svg>`;
  const EMPTY_USER = `
    <div class="wishlist-empty-state">
      <div class="wishlist-empty-icon">${EMPTY_ICON}</div>
      <h3>No tienes productos<br>en tu wishlist.</h3>
      <p class="wishlist-sub">Agrega productos para verlos aquí.</p>
    </div>`;
  const EMPTY_GUEST = `
    <div class="wishlist-empty-state">
      <div class="wishlist-empty-icon">${EMPTY_ICON}</div>
      <h3>No tienes productos<br>en tu wishlist.</h3>
      <p class="wishlist-sub">¿Quieres conservar tus favoritos?</p>
      <p class="wishlist-links">
        <a href="#" id="open-login-hint" class="wishlist-link">Inicia sesión</a> o
        <a href="/registrarse/" class="wishlist-link">crea una cuenta</a>.
      </p>
    </div>`;

  function injectHint() {
    const hint = `
      <div class="wishlist-hint">
        ¿Quieres conservar tus favoritos?
        <a href="#" id="open-login-hint" class="wishlist-link">Inicia sesión</a> o
        <a href="/registrarse/" class="wishlist-link">crea una cuenta</a>.
      </div>`;
    [dom.wishlistContent, dom.wishlistCascade].filter(Boolean).forEach(c => {
      if (!c.querySelector('.wishlist-hint')) {
        c.insertAdjacentHTML('beforeend', hint);
      }
    });
  }

  // 👇 corregido: cerrar wishlist al abrir login
  document.body.addEventListener('click', e => {
    if (e.target.id === 'open-login-hint') {
      e.preventDefault();
      hideWishlist(); // cerrar panel de favoritos
      window.mostrarLoginPanel?.(); // abrir login
    }
  });

  function clearWishlist() {
    const ids = getList();
    localStorage.removeItem(keyUser);
    updateHeaderUI([]);
    dom.wishlistContent && (dom.wishlistContent.textContent =
      'No tienes productos en tu wishlist.');

    if (isAuthenticated && clienteId && ids.length) {
      ids.forEach(id => {
        // 🔐 JWT: fetchDelete agrega token automáticamente
        fetchDelete(`${backendURL}${clienteId}/`, {
          body: JSON.stringify({ producto_id: id })
        }).catch(console.error);
      });
    }
  }

  function nukeAllKeys() {
    Object.keys(localStorage)
      .filter(k => k.startsWith(storageKey))
      .forEach(k => localStorage.removeItem(k));
    updateHeaderUI([]);
  }

  window.renderWishlistPanel = renderWishlistPanel;

  if (!window.__wishlistCarritoListenerRegistered) {
    window.__wishlistCarritoListenerRegistered = true;
    document.addEventListener('carrito-actualizado', async () => {
      if (dom.wishlistPanel?.classList.contains('open') &&
          typeof window.renderWishlistPanel === 'function') {
        await window.renderWishlistPanel();
      }
    });
  }

  const api = { clearWishlist, nukeAllKeys };
  window.__wishlistAPI = api;
  return api;
}
