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
          fetch(`${backendURL}${safeClienteId}/`, {
            method  : 'POST',
            headers : {
              'Content-Type': 'application/json',
              ...(csrfToken && { 'X-CSRFToken': csrfToken })
            },
            body    : JSON.stringify({ producto_id: id })
          }).catch(console.error);
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
    wishlistContent : document.querySelector('#wishlist-panel .wishlist-content'),
    overlay         : document.querySelector('.page-overlay'),
    wishlistBtn     : document.getElementById('btn-wishlist-panel'),
    closeBtn        : document.getElementById('close-wishlist-panel'),
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
    if (isAuthenticated && clienteId) {
      try {
        const r = await fetch(`${backendURL}${safeClienteId}/`);
        if (r.ok) {
          const { productos = [] } = await r.json();
          setList([...new Set([...getList(), ...productos.map(String)])]);
        }
      } catch (err) { console.error('[Wishlist] pull', err); }
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
    fetch(`${backendURL}${safeClienteId}/`, {
      method  : add ? 'POST' : 'DELETE',
      headers : {
        'Content-Type': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken })
      },
      body    : JSON.stringify({ producto_id: id })
    }).catch(console.error);
  });

  /* ========== Eventos dentro del panel ========== */
  dom.wishlistPanel?.addEventListener('click', async e => {
    const pickerOpen = dom.wishlistPanel.querySelector('.size-picker');
    if (pickerOpen && !e.target.closest('.size-picker') &&
                      !e.target.matches('.btn-carrito-mini')) {
      closeSizePicker(pickerOpen, 'down');
    }

    if (e.target.matches('.btn-carrito-mini')) {
      const pid = e.target.dataset.id;
      if (pickerOpen && pickerOpen.dataset.productId === pid) {
        closeSizePicker(pickerOpen, 'down'); return;
      }
      pickerOpen && closeSizePicker(pickerOpen, 'down');

      let tallas = [];
      try {
        const r = await fetch(`/api/productos/${pid}/`);
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
      const r = await fetch(`/api/carrito/create/${safeClienteId}/`, {
        method  : 'POST',
        headers : {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRFToken': csrfToken })
        },
        body    : JSON.stringify({ producto_id: pid, talla, cantidad: cant })
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
      const r = await fetch(`/api/carrito/${safeClienteId}/`, { credentials: 'same-origin' });
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
        <img src="${p.imagen}" alt="${p.nombre}">
      </div>
      <div class="wishlist-info-col">
        <h4 class="nombre">${p.nombre}</h4>
        <p class="precio">$${p.precio}</p>
        <div class="wishlist-actions">
          ${inCart.has(String(p.id))
            ? `<span class="in-cart-note">Ya en carrito</span>`
            : `<button class="btn-carrito-mini" data-id="${p.id}">Agregar al carrito</button>`
          }
        </div>
      </div>
    </div>
  `).join('');

  async function renderWishlistPanel() {
    const ids = getList();
    if (!ids.length) {
      dom.headerTitle && (dom.headerTitle.style.visibility = 'hidden');
      dom.wishlistContent.innerHTML = isAuthenticated ? EMPTY_USER : EMPTY_GUEST;
      updateHeaderUI([]);
      return;
    }
    dom.headerTitle && (dom.headerTitle.style.visibility = 'visible');

    try {
      dom.wishlistContent.textContent = 'Cargando…';
      const url = isAuthenticated
        ? `${backendURL}${safeClienteId}/?full=true`
        : `${fetchProductoURL}${ids.join(',')}`;
      const { productos = [] } = await (await fetch(url)).json();
      const inCart = await getCartIds();

      dom.wishlistContent.innerHTML = productos.length
        ? buildCards(productos, inCart)
        : 'No tienes productos en tu wishlist.';

      updateHeaderUI(ids);
    } catch (err) {
      dom.wishlistContent.textContent = 'Error al cargar tu wishlist.';
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
    dom.wishlistContent.insertAdjacentHTML('beforeend', `
      <div class="wishlist-hint">
        ¿Quieres conservar tus favoritos?
        <a href="#" id="open-login-hint" class="wishlist-link">Inicia sesión</a> o
        <a href="/registrarse/" class="wishlist-link">crea una cuenta</a>.
      </div>`);
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
        fetch(`${backendURL}${safeClienteId}/`, {
          method  : 'DELETE',
          headers : {
            'Content-Type': 'application/json',
            ...(csrfToken && { 'X-CSRFToken': csrfToken })
          },
          body    : JSON.stringify({ producto_id: id })
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
