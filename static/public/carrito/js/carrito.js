/* ==========================================================================
 * carrito.js – Enterprise Cart (JWT + Invitado)
 * Optimistic UI + Auto-corrección con servidor
 * ==========================================================================
 */
document.addEventListener('DOMContentLoaded', () => {
  const TOKEN      = localStorage.getItem('access') || null;
  const RAW_ID     = localStorage.getItem('user_id');
  const CLIENTE_ID = RAW_ID && !isNaN(RAW_ID) ? Number(RAW_ID) : 0;
  const IS_LOGGED  = Boolean(TOKEN && CLIENTE_ID > 0);
  const API_BASE   = IS_LOGGED ? `/api/carrito/${CLIENTE_ID}` : '/api/carrito/guest';
  const SESSION_KEY = document.cookie.match(/sessionid=([^;]+)/)?.[1] || '';

  // ── Helpers ──────────────────────────────────────────────
  const getHeaders = () => IS_LOGGED ? {} : (SESSION_KEY ? { 'X-Session-Key': SESSION_KEY } : {});

  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };

  const toggleMinusBtn = (wrap, qty) => {
    const btn = wrap.querySelector('.btn-minus');
    if (btn) btn.style.visibility = qty <= 1 ? 'hidden' : 'visible';
  };

  const precioItem = (item, mayoreo) =>
    mayoreo ? item.precio_mayorista : item.precio_menudeo;

  // ── PATCH cantidad (servidor) ────────────────────────────
  async function patchCantidad(varId, cant) {
    const res = await fetchWithAuth(`${API_BASE}/item/${varId}/actualizar/`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({ cantidad: cant })
    });
    return res.ok;
  }

  // ── Render carrito desde API ─────────────────────────────
  async function renderCarritoDesdeAPI() {
    const res = await fetchWithAuth(`${API_BASE}/`, { headers: getHeaders() });
    if (!res.ok) return;

    const data = await res.json();
    const contenedor = document.getElementById('carrito-items');
    if (!contenedor || !Array.isArray(data.items)) return;

    const actuales = new Set([...contenedor.children].map(el => el.dataset.varianteId));
    const nuevos   = new Set(data.items.map(item => String(item.variante_id)));

    // Quitar items eliminados
    [...contenedor.children].forEach(child => {
      if (!nuevos.has(child.dataset.varianteId)) {
        child.classList.add('fade-out');
        child.addEventListener('animationend', () => child.remove(), { once: true });
      }
    });

    // Renderizar items nuevos
    for (const item of data.items) {
      const id = String(item.variante_id);
      if (actuales.has(id)) continue;

      const precio  = precioItem(item, data.mayoreo);
      const galeria = item.imagenes_galeria || [item.imagen];

      const div = document.createElement('div');
      div.className = 'carrito-item';
      div.dataset.varianteId    = id;
      div.dataset.precioMenudeo   = item.precio_menudeo;
      div.dataset.precioMayorista = item.precio_mayorista;

      let imagenHTML = '';
      if (galeria.length > 1) {
        imagenHTML = `
          <div class="carrusel-mini-viewport">
            <div class="carrusel-mini-track">
              ${galeria.map(img => `<img src="${img}" class="carrusel-mini-slide" alt="${item.producto}">`).join('')}
            </div>
          </div>
          <button class="carrusel-mini-prev">\u2039</button>
          <button class="carrusel-mini-next">\u203A</button>`;
      } else {
        imagenHTML = `<img src="${item.imagen || '/static/images/placeholder.png'}" alt="${item.producto}">`;
      }

      const minusVis = item.cantidad > 1 ? '' : ' style="visibility:hidden"';
      const tallaText = item.talla ? `Talla: ${item.talla}` : 'Talla \u00FAnica';
      const colorText = item.color && item.color !== 'N/A' ? ` \u00B7 Color: ${item.color}` : '';

      div.innerHTML = `
        <div class="item-imagen">${imagenHTML}</div>
        <div class="item-detalles">
          <h4>${item.producto}</h4>
          <span>${tallaText}${colorText}</span>
          <div class="item-precio-cantidad">
            <div class="item-precio">
              <span class="precio-unitario-wrapper">$${precio.toFixed(2)}</span>
              ${data.mayoreo && item.precio_menudeo !== item.precio_mayorista
                ? `<span class="precio-original">$${item.precio_menudeo.toFixed(2)}</span>` : ''}
            </div>
            <div class="item-cantidad qty-wrap">
              <button class="btn-minus"${minusVis}>&minus;</button>
              <input type="number" class="qty" min="1" value="${item.cantidad}">
              <button class="btn-plus">+</button>
            </div>
            <div class="item-subtotal">$${(precio * item.cantidad).toFixed(2)}</div>
          </div>
        </div>
        <button class="item-remove" title="Eliminar" data-variante="${item.variante_id}">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>`;

      contenedor.appendChild(div);
      requestAnimationFrame(() => div.classList.add('fade-in'));
      initMiniCarrusel(div);
    }

    // Sincronizar data-attributes de items existentes
    data.items.forEach(item => {
      const el = document.querySelector(`.carrito-item[data-variante-id="${item.variante_id}"]`);
      if (el) {
        el.dataset.precioMenudeo   = item.precio_menudeo;
        el.dataset.precioMayorista = item.precio_mayorista;
      }
    });

    // Calcular totales con lógica de mayoreo
    calcularTotalesOptimistas();

    // Variables globales para checkout
    window.CARRITO_ID = data.carrito_id;
    window.CARRITO_ITEMS = data.items.map(item => {
      const p = precioItem(item, data.mayoreo);
      return {
        variante_id: item.variante_id,
        nombre: item.producto,
        talla: item.talla || '\u00DAnica',
        color: item.color || '',
        cantidad: item.cantidad,
        precio: p,
        subtotal: p * item.cantidad,
        imagen: item.imagenes_galeria?.[0] || item.imagen
      };
    });

    window.alternarVistaCarrito?.(data.items.length);
  }

  // ── Mini carrusel ────────────────────────────────────────
  function initMiniCarrusel(itemEl) {
    const track = itemEl.querySelector('.carrusel-mini-track');
    const prev  = itemEl.querySelector('.carrusel-mini-prev');
    const next  = itemEl.querySelector('.carrusel-mini-next');
    if (!track || !prev || !next) return;

    const slides = track.querySelectorAll('.carrusel-mini-slide');
    let current = 0;

    const go = dir => {
      current = (current + dir + slides.length) % slides.length;
      track.style.transform = `translateX(-${current * 100}%)`;
    };

    prev.addEventListener('click', e => { e.stopPropagation(); go(-1); });
    next.addEventListener('click', e => { e.stopPropagation(); go(1); });
  }

  // ── Cálculo optimista con lógica de mayoreo ──────────────
  function calcularTotalesOptimistas() {
    const items = document.querySelectorAll('.carrito-item');

    if (!items.length) {
      setText('carrito-main-subtotal', '$0.00');
      setText('resumen-total', '$0.00');
      setText('carrito-count', '0 artículos');
      const alertaMay  = document.getElementById('alerta-mayoreo');
      const alertaMeta = document.getElementById('alerta-meta-mayoreo');
      if (alertaMay)  alertaMay.style.display  = 'none';
      if (alertaMeta) alertaMeta.style.display = 'none';
      return;
    }

    // Paso 1: Total de piezas
    let totalCantidad = 0;
    items.forEach(item => {
      totalCantidad += parseInt(item.querySelector('.qty')?.value) || 0;
    });

    // Paso 2: ¿Aplica mayoreo? (>= 6 piezas)
    const aplicarMayoreo = totalCantidad >= 6;

    // Paso 3: Recalcular precios y subtotales
    let totalPrecio = 0;

    items.forEach(item => {
      const cantidad       = parseInt(item.querySelector('.qty')?.value) || 0;
      const precioMenudeo  = parseFloat(item.dataset.precioMenudeo) || 0;
      const precioMayorista = parseFloat(item.dataset.precioMayorista) || 0;
      const precioActual   = aplicarMayoreo ? precioMayorista : precioMenudeo;
      const subtotal       = precioActual * cantidad;

      // Actualizar precio unitario
      const precioEl = item.querySelector('.precio-unitario-wrapper');
      if (precioEl) precioEl.textContent = `$${precioActual.toFixed(2)}`;

      // Precio tachado (menudeo vs mayoreo)
      const hayDescuento = aplicarMayoreo && precioMenudeo !== precioMayorista;
      let precioOriginalEl = item.querySelector('.precio-original');

      if (hayDescuento) {
        if (!precioOriginalEl) {
          precioOriginalEl = document.createElement('span');
          precioOriginalEl.className = 'precio-original';
          item.querySelector('.item-precio')?.appendChild(precioOriginalEl);
        }
        precioOriginalEl.textContent = `$${precioMenudeo.toFixed(2)}`;
        precioOriginalEl.style.display = 'inline-block';
      } else if (precioOriginalEl) {
        precioOriginalEl.style.display = 'none';
      }

      // Subtotal del item
      const subtotalEl = item.querySelector('.item-subtotal');
      if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)}`;

      totalPrecio += subtotal;
    });

    // Paso 4: Actualizar UI global
    setText('carrito-count', `${totalCantidad} artículo${totalCantidad !== 1 ? 's' : ''}`);
    setText('carrito-main-subtotal', `$${totalPrecio.toFixed(2)}`);
    setText('resumen-total', `$${totalPrecio.toFixed(2)}`);

    // Alertas de mayoreo
    const faltan = Math.max(6 - totalCantidad, 0);
    document.querySelectorAll('.piezas-restantes').forEach(el => el.textContent = faltan);

    const alertaMay  = document.getElementById('alerta-mayoreo');
    const alertaMeta = document.getElementById('alerta-meta-mayoreo');
    if (alertaMay)  alertaMay.style.display  = aplicarMayoreo ? 'flex' : 'none';
    if (alertaMeta) alertaMeta.style.display = (!aplicarMayoreo && faltan > 0) ? 'flex' : 'none';

    window.CARRITO_TOTAL = totalPrecio;
  }

  // ── Sincronizar con servidor (background) ────────────────
  async function sincronizarConServidor() {
    const res = await fetchWithAuth(`${API_BASE}/`, { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    window.alternarVistaCarrito?.(data.items?.length);

    if (!data.items?.length) {
      calcularTotalesOptimistas();
      return;
    }

    // Actualizar data-attributes con valores del servidor
    data.items.forEach(item => {
      const el = document.querySelector(`.carrito-item[data-variante-id="${item.variante_id}"]`);
      if (el) {
        el.dataset.precioMenudeo   = item.precio_menudeo;
        el.dataset.precioMayorista = item.precio_mayorista;
      }
    });

    // Recalcular con valores corregidos
    calcularTotalesOptimistas();
  }

  // ── Click: +, -, eliminar ────────────────────────────────
  document.body.addEventListener('click', e => {
    // Botón eliminar (X)
    const removeBtn = e.target.closest('.item-remove');
    if (removeBtn) {
      const varId = removeBtn.dataset.variante;
      const item  = removeBtn.closest('.carrito-item');
      item.classList.add('fade-out');
      item.addEventListener('animationend', async () => {
        const r = await fetchWithAuth(`${API_BASE}/item/${varId}/eliminar/`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json', ...getHeaders() }
        });
        if (r.ok) {
          item.remove();
          calcularTotalesOptimistas();
          sincronizarConServidor();
        } else {
          item.classList.remove('fade-out');
        }
      }, { once: true });
      return;
    }

    // Botones + / -
    const plus  = e.target.closest('.btn-plus');
    const minus = e.target.closest('.btn-minus');
    if (!plus && !minus) return;

    const wrap  = (plus || minus).closest('.qty-wrap');
    const input = wrap.querySelector('.qty');
    const varId = wrap.closest('.carrito-item').dataset.varianteId;
    if (!varId) return;

    let val = parseInt(input.value) || 1;
    if (plus)  val++;
    else if (val <= 1) return;
    else val--;

    // UI inmediata
    input.value = val;
    toggleMinusBtn(wrap, val);
    calcularTotalesOptimistas();

    // Servidor en background
    patchCantidad(varId, val);
  });

  // ── Cambio manual en input qty ───────────────────────────
  document.body.addEventListener('change', e => {
    if (!e.target.classList.contains('qty')) return;

    const input = e.target;
    const wrap  = input.closest('.qty-wrap');
    const varId = input.closest('.carrito-item').dataset.varianteId;
    let val = Math.max(1, parseInt(input.value) || 1);
    input.value = val;

    toggleMinusBtn(wrap, val);
    calcularTotalesOptimistas();
    patchCantidad(varId, val);
  });

  // ── Vaciar carrito ───────────────────────────────────────
  document.querySelector('.btn-vaciar')?.addEventListener('click', async () => {
    if (!confirm('\u00BFVaciar todo el carrito?')) return;

    const r = await fetchWithAuth(`${API_BASE}/empty/`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', ...getHeaders() }
    });
    if (r.ok) document.dispatchEvent(new CustomEvent('carrito-actualizado'));
  });

  // ── Modal invitado ───────────────────────────────────────
  function modalGuest() {
    let m = document.getElementById('guest-checkout-modal');
    if (m) { m.classList.add('open'); return; }

    m = document.createElement('div');
    m.id = 'guest-checkout-modal';
    m.className = 'modal-overlay';
    m.innerHTML = `<div class="modal">
      <h3>\u00BFC\u00F3mo deseas continuar?</h3>
      <button class="btn-guest-checkout">Comprar como invitado</button>
      <button class="btn-login">Iniciar sesi\u00F3n / Registrarse</button>
      <button class="modal-close">\u2715</button>
    </div>`;
    document.body.appendChild(m);

    m.addEventListener('click', e => {
      if (e.target === m || e.target.classList.contains('modal-close')) m.remove();
      if (e.target.classList.contains('btn-login'))           { m.remove(); window.mostrarLoginPanel?.(); }
      if (e.target.classList.contains('btn-guest-checkout'))   { m.remove(); window.location.href = '/checkout/guest/'; }
    });
  }

  // ── Alternar vista vacío / activo ────────────────────────
  window.alternarVistaCarrito = hay => {
    const activo = document.getElementById('carrito-activo');
    const vacio  = document.getElementById('carrito-vacio');
    const btn    = document.getElementById('btn-checkout');
    const vaciar = document.getElementById('vaciar-wrapper');

    if (activo) {
      activo.style.display = hay ? '' : 'none';
      activo.classList.toggle('visible', !!hay);
    }
    if (vacio)  vacio.style.display  = hay ? 'none' : 'flex';
    if (btn)    btn.disabled         = !hay;
    if (vaciar) vaciar.style.display = hay ? 'flex' : 'none';
  };

  // ── Exponer para uso externo ─────────────────────────────
  window.updateTotals = sincronizarConServidor;
  window.calcularTotalesOptimistas = calcularTotalesOptimistas;

  // ── Eventos e inicialización ─────────────────────────────
  document.addEventListener('carrito-actualizado', renderCarritoDesdeAPI);
  renderCarritoDesdeAPI();
});
