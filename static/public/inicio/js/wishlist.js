/* ==========================================================================
 * Wishlist Module
 * Invitado + Multi-usuario con selector de tallas y carrito invitado
 * --------------------------------------------------------------------------
 * Invitado  → localStorage (wishlist_ids_guest)
 * Login     → migra guest → wishlist_ids_<userId> y sincroniza backend
 * Logout    → nukeAllKeys() borra TODAS las claves wishlist_ids_*
 * ======================================================================== */

export function initWishlist({
  selector          = '.wishlist-btn',              // Selector CSS de los corazones
  storageKey        = 'wishlist_ids',               // Prefijo en localStorage
  backendURL        = '/api/wishlist/',             // Endpoint REST → /<cliente>/
  csrfToken         = null,                         // CSRF (Django, por ej.)
  isAuthenticated   = false,                        // Usuario logueado
  fetchProductoURL  = '/api/productos_por_ids/?ids=',
  clienteId         = null                          // ID numérico del cliente o null
} = {}) {

  /* ≡≡≡ 0.  CONSTANTES Y UTILITARIOS DE ALMACENAMIENTO ≡≡≡ */

  const IS_GUEST_ID   = 0;                                   // ID ficticio para invitados
  const safeClienteId = clienteId ?? IS_GUEST_ID;            // Nunca null en peticiones

  // Clave específica para este usuario (o invitado) en localStorage
  const keyUser = (isAuthenticated && clienteId)
    ? `${storageKey}_${clienteId}`
    : `${storageKey}_guest`;

  /**
   * Devuelve la lista de IDs guardada para este usuario.
   * @returns {string[]} array de IDs como strings
   */
  const getList = () => {
    try { return JSON.parse(localStorage.getItem(keyUser)) || []; }
    catch { return []; }
  };

  /** Persiste lista en LS y actualiza el contador en header. */
  const setList = list => {
    localStorage.setItem(keyUser, JSON.stringify(list));
    updateHeaderUI(list);
  };

  /* ≡≡≡ 1.  MIGRACIÓN INVITADO → USUARIO Y SINCRONIZACIÓN BACKEND ≡≡≡ */

  if (isAuthenticated && clienteId) {
    try {
      // 1-A. Fusiona posible lista invitado + lista ya existente del usuario
      const guestRaw = localStorage.getItem(`${storageKey}_guest`);
      const userRaw  = localStorage.getItem(keyUser);

      const merged = [...new Set([
        ...(JSON.parse(userRaw  || '[]')),
        ...(JSON.parse(guestRaw || '[]'))
      ])];

      localStorage.setItem(keyUser, JSON.stringify(merged));
      localStorage.removeItem(`${storageKey}_guest`);

      // 1-B. Sube al backend los likes heredados del invitado
      if (guestRaw) {
        for (const id of JSON.parse(guestRaw)) {
          // 🔐 JWT: fetchPost agrega token automáticamente
          fetchPost(`${backendURL}${clienteId}/`, { producto_id: id })
            .catch(console.error);
        }
      }
    } catch { /* silencioso */ }
  } else {
    // Invitado: elimina listas pertenecientes a otros usuarios
    Object.keys(localStorage)
      .filter(k => k.startsWith(storageKey) && !k.endsWith('_guest'))
      .forEach(k => localStorage.removeItem(k));
  }

  /* ≡≡≡ 2.  REFERENCIAS A NODOS DEL DOM (una sola búsqueda) ≡≡≡ */

  const dom = {
    wishlistPanel   : document.getElementById('wishlist-panel'),
    wishlistContent : document.querySelector('#wishlist-panel .wishlist-content'),
    overlay         : document.querySelector('.page-overlay'),
    wishlistBtn     : document.getElementById('btn-wishlist-panel'),
    closeBtn        : document.getElementById('close-wishlist-panel'),
    wishlistIcon    : document.querySelector('#btn-wishlist-panel i'),
    wishlistCount   : document.querySelector('#btn-wishlist-panel .wishlist-count'),
    headerTitle     : document.getElementById('wishlist-header-title')
  };

  /* ≡≡≡ 3.  HELPER VISUALES (corazones + contador header) ≡≡≡ */

  /**
   * Activa / desactiva un corazón concreto.
   * @param {HTMLElement} btn  Elemento botón/ícono
   * @param {boolean} on       Estado activo
   */
  const toggleBtn = (btn, on) => {
    btn.classList.toggle('active', on);
    const ic = btn.querySelector('i');
    ic?.classList.toggle('fa-solid',   on);
    ic?.classList.toggle('fa-regular', !on);
  };

  /** Actualiza ícono de cabecera y badge con el # de favoritos. */
  const updateHeaderUI = list => {
    const { wishlistIcon, wishlistCount } = dom;
    wishlistIcon?.classList.toggle('fa-solid', !!list.length);
    wishlistIcon?.classList.toggle('fa-regular', !list.length);
    if (wishlistIcon) wishlistIcon.style.color = list.length ? '#ff4d6d' : '';

    if (wishlistCount) {
      wishlistCount.textContent = list.length;
      wishlistCount.hidden      = !list.length;
    }
  };

  /* ≡≡≡ 4.  HIDRATACIÓN INICIAL (pull de servidor si login) ≡≡≡ */

  let hydrateDoneResolve;
  const hydrateDone = new Promise(res => (hydrateDoneResolve = res));

  (async () => {
    // 4-A. Trae lista del backend si user logueado
    if (isAuthenticated && clienteId) {
      try {
        // 🔐 JWT: fetchGet agrega token automáticamente
        const r = await fetchGet(`${backendURL}${clienteId}/`);
        if (r.ok) {
          const { productos = [] } = await r.json();
          setList([...new Set([...getList(), ...productos.map(String)])]);
        }
      } catch (err) {
        console.error('[Wishlist] pull', err);
      }
    }

    // 4-B. Marca corazones ya activos
    const idsSet = new Set(getList());
    document.querySelectorAll(selector)
      .forEach(btn => toggleBtn(btn, idsSet.has(btn.dataset.productId)));

    hydrateDoneResolve();      // ✅ listo
  })();

  /* ≡≡≡ 5.  ABRIR / CERRAR PANEL DE WISHLIST ≡≡≡ */

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

  /* ≡≡≡ 6.  CORAZONES EN CATÁLOGO (LS + backend) ≡≡≡ */

  document.body.addEventListener('click', e => {
    const heart = e.target.closest(selector);
    if (!heart) return;

    const id = heart.dataset.productId;
    let list = getList();
    const add = !heart.classList.contains('active');   // toggle

    toggleBtn(heart, add);
    add ? list.push(id) : list = list.filter(x => x !== id);
    setList(list);

    // Sincroniza backend si user
    if (!isAuthenticated) return;
    
    // 🔐 JWT: Usa fetchWithAuth en lugar de fetch manual
    const method = add ? 'POST' : 'DELETE';
    fetchWithAuth(`${backendURL}${clienteId}/`, {
      method,
      body: JSON.stringify({ producto_id: id })
    }).catch(console.error);
  });

  /* -------------------------------------------------
   * 7.  EVENTOS DENTRO DEL PANEL (picker de tallas, qty…)
   * ------------------------------------------------- */

  dom.wishlistPanel?.addEventListener('click', async e => {

    /* 7-A · Cierre auto picker si clic fuera */
    const pickerOpen = dom.wishlistPanel.querySelector('.size-picker');
    if (pickerOpen && !e.target.closest('.size-picker') &&
                      !e.target.matches('.btn-carrito-mini')) {
      closeSizePicker(pickerOpen, 'down');
    }

    /* 7-B · Botón “Agregar” (abre picker) */
    if (e.target.matches('.btn-carrito-mini')) {
      const pid = e.target.dataset.id;

      // Si ya hay picker abierto para este prod → ciérralo
      if (pickerOpen && pickerOpen.dataset.productId === pid) {
        closeSizePicker(pickerOpen, 'down');
        return;
      }
      pickerOpen && closeSizePicker(pickerOpen, 'down');

      // Trae tallas y construye picker
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

      // Posiciona picker y aplica blur
      const r = dom.wishlistPanel.getBoundingClientRect();
      picker.style.left  = `${r.left}px`;
      picker.style.width = `${r.width}px`;
      dom.wishlistPanel.dataset.prevOverflow = dom.wishlistPanel.style.overflowY || '';
      dom.wishlistPanel.style.overflowY = 'hidden';
      dom.wishlistContent.classList.add('blurred');
    }

    /* 7-C · Selección de talla (envía al carrito) */
    if (e.target.matches('.size-option')) {
      const talla = e.target.dataset.size;
      const pid   = e.target.closest('.size-picker').dataset.productId;
      e.target.classList.add('chosen');
      await addToCart(pid, talla, 1);
      setTimeout(() => closeSizePicker(
        e.target.closest('.size-picker'), 'down'), 160);
    }

    /* 7-D · Botón ✕ dentro del picker */
    if (e.target.matches('.close-size-picker')) {
      closeSizePicker(e.target.closest('.size-picker'), 'down');
    }
  });

  /* ≡≡≡ 7-bis.  +/- cantidad (delegado global) ≡≡≡ */

  document.body.addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (!btn) return;

    const wrapper = btn.closest('.qty-wrap');
    if (!wrapper) return;

    const input = wrapper.querySelector('input.qty');
    let val = parseInt(input.value, 10) || 1;

    if (btn.classList.contains('btn-plus'))  input.value = val + 1;
    if (btn.classList.contains('btn-minus') && val > 1) input.value = val - 1;
  });

  /* ≡≡≡ 8.  FUNCIONES DE UTILIDAD PRINCIPALES ≡≡≡ */

  /**
   * Muestra toast flotante.
   * @param {string} msg
   */
  function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = msg;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => toast.classList.remove('show'), 2500);
    setTimeout(() => toast.remove(), 3000);
  }

  /**
   * POST: agrega item al carrito (backend) y actualiza UI local.
   * @param {string} pid    ID producto
   * @param {string} talla  Talla elegida
   * @param {number} cant   Cantidad
   */
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

      // Reemplaza botón “Agregar” por texto “Ya en carrito”
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

  /**
   * Cierra selector de talla con animación.
   * @param {HTMLElement} node
   * @param {'side'|'down'} dir
   */
  function closeSizePicker(node, dir = 'down') {
    if (!node) return;
    node.classList.add(dir === 'side' ? 'fade-out-side' : 'fade-out-down');
    dom.wishlistPanel.style.overflowY =
      dom.wishlistPanel.dataset.prevOverflow || 'auto';
    delete dom.wishlistPanel.dataset.prevOverflow;
    dom.wishlistContent.classList.remove('blurred');
    node.addEventListener('animationend', () => node.remove(), { once: true });
  }

  /* ≡≡≡ 9.  RENDER DEL PANEL + UTILITARIOS RELACIONADOS ≡≡≡ */

  /** Consulta carrito y devuelve set de IDs ya en carrito. */
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

  /** Genera HTML de las tarjetas dentro del panel. */
  const buildCards = (prods, inCart = new Set()) => prods.map(p => `
    <div class="wishlist-item" data-id="${p.id}">
      <div class="wishlist-img-col">
        <img src="${p.imagen}" alt="${p.nombre}">
      </div>
      <div class="wishlist-info-col">
        <h4 class="nombre">${p.nombre}</h4>
        <p class="precio">$${p.precio}</p>
        <div class="wishlist-controls">
          <div class="qty-wrap">
            <button class="btn-minus">−</button>
            <input type="number" class="qty" value="1" readonly>
            <button class="btn-plus">+</button>
          </div>
          ${inCart.has(String(p.id))
            ? `<span class="in-cart-note">Ya en carrito</span>`
            : `<button class="btn-carrito-mini" data-id="${p.id}">Agregar al carrito</button>`
          }
          <button class="remove-item"><i class="fa-regular fa-trash-can"></i></button>
        </div>
      </div>
    </div>
  `).join('');

  /**
   * Rellena el panel de wishlist con sus productos.
   * Llama a buildCards y se ocupa de estados vacíos.
   */
  async function renderWishlistPanel() {
    const ids = getList();

    // ---- Estado vacío ----
    if (!ids.length) {
      dom.headerTitle && (dom.headerTitle.style.visibility = 'hidden');
      dom.wishlistContent.innerHTML = isAuthenticated ? EMPTY_USER : EMPTY_GUEST;
      return;
    }
    dom.headerTitle && (dom.headerTitle.style.visibility = 'visible');

    // ---- Trae datos de productos ----
    try {
      dom.wishlistContent.textContent = 'Cargando…';
      const url = isAuthenticated
        ? `${backendURL}${clienteId}/?full=true`
        : `${fetchProductoURL}${ids.join(',')}`;
      
      // 🔐 JWT: fetchGet agrega token automáticamente si el usuario está logueado
      const { productos = [] } = await (await fetchGet(url)).json();
      const inCart = await getCartIds();

      dom.wishlistContent.innerHTML = productos.length
        ? buildCards(productos, inCart)
        : 'No tienes productos en tu wishlist.';
    } catch (err) {
      dom.wishlistContent.textContent = 'Error al cargar tu wishlist.';
    }

    // Hint para invitados
    if (!isAuthenticated) injectHint();
  }

  /* Plantillas de estados vacíos */
  const EMPTY_ICON = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
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
        <a href="#" id="open-login-hint">Inicia sesión</a> o
        <a href="/registrarse/">crea una cuenta</a>.
      </p>
    </div>`;

  /** Inyecta aviso de login al final (invitados). */
  function injectHint() {
    dom.wishlistContent.insertAdjacentHTML('beforeend', `
      <div class="wishlist-hint">
        ¿Quieres conservar tus favoritos?
        <a href="#" id="open-login-hint">Inicia sesión</a> o
        <a href="/registrarse/">crea una cuenta</a>.
      </div>`);
  }

  /* Apertura panel de login si usuario toca hint */
  document.body.addEventListener('click', e => {
    if (e.target.id === 'open-login-hint') {
      e.preventDefault();
      window.mostrarLoginPanel?.();
    }
  });

  /* ≡≡≡ 10.  API PÚBLICA + LISTENERS GLOBALES ≡≡≡ */

  /** Borra wishlist actual del usuario. */
  function clearWishlist() {
    const ids = getList();
    localStorage.removeItem(keyUser);
    updateHeaderUI([]);
    dom.wishlistContent && (dom.wishlistContent.textContent =
      'No tienes productos en tu wishlist.');

    // Limpia backend
    if (isAuthenticated && clienteId && ids.length) {
      ids.forEach(id => {
        // 🔐 JWT: fetchDelete agrega token automáticamente
        fetchDelete(`${backendURL}${clienteId}/`, {
          body: JSON.stringify({ producto_id: id })
        }).catch(console.error);
      });
    }
  }

  /** Elimina TODAS las keys wishlist_* (en logout). */
  function nukeAllKeys() {
    Object.keys(localStorage)
      .filter(k => k.startsWith(storageKey))
      .forEach(k => localStorage.removeItem(k));
    updateHeaderUI([]);
  }

  // Expone para scripts externos (ej: refresh desde fuera)
  window.renderWishlistPanel = renderWishlistPanel;

  // Listener global para recibir evento “carrito-actualizado”
  if (!window.__wishlistCarritoListenerRegistered) {
    window.__wishlistCarritoListenerRegistered = true;

    document.addEventListener('carrito-actualizado', async () => {
      if (
        dom.wishlistPanel?.classList.contains('open') &&
        typeof window.renderWishlistPanel === 'function'
      ) {
        await window.renderWishlistPanel();
      }
    });
  }

  // === Devolvemos API público ===
  const api = { clearWishlist, nukeAllKeys };
  window.__wishlistAPI = api;
  return api;
} // ← initWishlist
