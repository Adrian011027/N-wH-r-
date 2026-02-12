/* ==========================================================================
 * carrito.js ÔÇô versi├│n JWT + invitado funcional COMPLETA (con toggle trash/ÔêÆ)
 * ==========================================================================
 */
document.addEventListener('DOMContentLoaded', () => {
  const TOKEN = localStorage.getItem("access") || null;
  const RAW_ID = localStorage.getItem("user_id");
  const CLIENTE_ID = RAW_ID && !isNaN(RAW_ID) ? Number(RAW_ID) : 0;

  const IS_LOGGED = Boolean(TOKEN && CLIENTE_ID > 0);

  console.log("[carrito] CLIENTE_ID=", CLIENTE_ID, "TOKEN?", !!TOKEN, "IS_LOGGED?", IS_LOGGED);

  const API_BASE = IS_LOGGED
    ? `/api/carrito/${CLIENTE_ID}`
    : `/api/carrito/guest`;

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  async function patchCantidad(varId, cant) {
    const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };
    
    const res = await fetchWithAuth(`${API_BASE}/item/${varId}/actualizar/`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ cantidad: cant })
    });
    return res.ok;
  }

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  async function renderCarritoDesdeAPI() {
    const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };
    const res = await fetchWithAuth(`${API_BASE}/`, {
      headers
    });
    if (!res.ok) {
      console.error("[carrito] error al cargar:", res.status);
      return;
    }

    const data = await res.json();
    const contenedor = document.getElementById('carrito-items');
    if (!contenedor || !Array.isArray(data.items)) return;

    const actuales = new Set([...contenedor.children].map(el => el.dataset.varianteId));
    const nuevos   = new Set(data.items.map(item => String(item.variante_id)));

    // quitar items que ya no est├ín
    [...contenedor.children].forEach(child => {
      const id = child.dataset.varianteId;
      if (!nuevos.has(id)) {
        child.classList.add('fade-out');
        child.addEventListener('animationend', () => child.remove(), { once: true });
      }
    });

    // renderizar items nuevos
    for (const item of data.items) {
      const id = String(item.variante_id);
      if (actuales.has(id)) continue;

      const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
      const galeria = item.imagenes_galeria || [item.imagen];

      const div = document.createElement('div');
      div.className = 'carrito-item';
      div.dataset.varianteId = id;

      const minusBtn = item.cantidad === 1
        ? `<button class="btn-minus trash" title="Eliminar"><i class="fa-solid fa-trash"></i></button>`
        : `<button class="btn-minus">ÔêÆ</button>`;

      // Mini carrusel si hay m├║ltiples im├ígenes
      let imagenHTML = '';
      if (galeria.length > 1) {
        imagenHTML = `
          <div class="carrusel-mini-viewport">
            <div class="carrusel-mini-track">
              ${galeria.map(img => `<img src="${img}" class="carrusel-mini-slide" alt="${item.producto}">`).join('')}
            </div>
          </div>
          <button class="carrusel-mini-prev">ÔÇ╣</button>
          <button class="carrusel-mini-next">ÔÇ║</button>
        `;
      } else {
        imagenHTML = `<img src="${item.imagen || '/static/images/placeholder.png'}" alt="${item.producto}">`;
      }

      div.innerHTML = `
        <div class="item-imagen">
          ${imagenHTML}
        </div>

        <div class="item-detalles">
          <h4>${item.producto}</h4>
          <span>${item.talla ? `Talla: ${item.talla}` : 'Talla ├║nica'}${item.color && item.color !== 'N/A' ? ` ┬À Color: ${item.color}` : ''}</span>

          <div class="item-precio-cantidad">
            <div class="item-precio">
              <span class="precio-unitario-wrapper">$${precio.toFixed(2)}</span>
              ${data.mayoreo && item.precio_menudeo !== item.precio_mayorista ? 
                `<span class="precio-original">$${item.precio_menudeo.toFixed(2)}</span>` : ''}
            </div>

            <div class="item-cantidad qty-wrap">
              ${minusBtn}
              <input type="number" class="qty" min="1" value="${item.cantidad}">
              <button class="btn-plus">+</button>
            </div>

            <div class="item-subtotal">$${(precio * item.cantidad).toFixed(2)}</div>
          </div>
        </div>
        
        <button class="item-remove" title="Eliminar" data-variante="${item.variante_id}">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      `;

      contenedor.appendChild(div);
      requestAnimationFrame(() => div.classList.add('fade-in'));
      
      // Inicializar mini carrusel si existe
      initMiniCarrusel(div);
    }

    // Actualizar contador y subtotal
    const totalItems = data.items.reduce((acc, item) => acc + item.cantidad, 0);
    const total = data.items.reduce((acc, item) => {
      const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
      return acc + precio * item.cantidad;
    }, 0);
    
    const countEl = document.getElementById('carrito-count');
    if (countEl) countEl.textContent = `${totalItems} art├¡culo${totalItems !== 1 ? 's' : ''}`;
    
    // Update main subtotal
    const subEl = document.getElementById('carrito-main-subtotal');
    if (subEl) subEl.textContent = `$${total.toFixed(2)}`;
    
    const resumenTotal = document.getElementById('resumen-total');
    if (resumenTotal) resumenTotal.textContent = `$${total.toFixed(2)}`;

    console.log('[Carrito] data.carrito_id:', data.carrito_id, 'items.length:', data.items.length);
    
    // ÔòÉÔòÉÔòÉ GUARDAR EN VARIABLES GLOBALES PARA CHECKOUT ÔòÉÔòÉÔòÉ
    window.CARRITO_ID = data.carrito_id;
    window.CARRITO_TOTAL = total;
    window.CARRITO_ITEMS = data.items.map(item => ({
      variante_id: item.variante_id,
      nombre: item.producto,
      talla: item.talla || '├Ünica',
      color: item.color || '',
      cantidad: item.cantidad,
      precio: data.mayoreo ? item.precio_mayorista : item.precio_menudeo,
      subtotal: (data.mayoreo ? item.precio_mayorista : item.precio_menudeo) * item.cantidad,
      imagen: item.imagenes_galeria?.[0] || item.imagen
    }));
    console.log('[Carrito] Guardado en window:', window.CARRITO_ID, window.CARRITO_ITEMS.length, 'items');
    
    if (data.items.length > 0 && data.carrito_id) {
      ensureConfirmButtonVisible(data.carrito_id);
    } else {
      console.warn('[Carrito] No se llam├│ ensureConfirmButtonVisible - carrito_id:', data.carrito_id);
    }

    window.alternarVistaCarrito?.(data.items.length);
  }
  
  // Inicializar mini carrusel de im├ígenes
  function initMiniCarrusel(itemEl) {
    const track = itemEl.querySelector('.carrusel-mini-track');
    const prev = itemEl.querySelector('.carrusel-mini-prev');
    const next = itemEl.querySelector('.carrusel-mini-next');
    if (!track || !prev || !next) return;
    
    const slides = track.querySelectorAll('.carrusel-mini-slide');
    let current = 0;
    
    prev.addEventListener('click', (e) => {
      e.stopPropagation();
      current = (current - 1 + slides.length) % slides.length;
      track.style.transform = `translateX(-${current * 100}%)`;
    });
    
    next.addEventListener('click', (e) => {
      e.stopPropagation();
      current = (current + 1) % slides.length;
      track.style.transform = `translateX(-${current * 100}%)`;
    });
  }

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  async function updateTotals() {
    const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };
    const res = await fetchWithAuth(`${API_BASE}/`, {
      headers
    });
    if (!res.ok) return;
    const data = await res.json();

    const hay = data.items?.length;
    window.alternarVistaCarrito?.(hay);

    const alertaMeta = document.getElementById('alerta-meta-mayoreo');
    const alertaMay  = document.getElementById('alerta-mayoreo');

    if (!hay) {
      const subEl = document.getElementById('carrito-main-subtotal');
      if (subEl) subEl.textContent = '$0.00';
      const resumenTotal = document.getElementById('resumen-total');
      if (resumenTotal) resumenTotal.textContent = '$0.00';
      if (alertaMay)  alertaMay.style.display  = 'none';
      if (alertaMeta) alertaMeta.style.display = 'none';
      return;
    }

    const piezas = data.items.reduce((s, x) => s + x.cantidad, 0);
    const faltan = Math.max(6 - piezas, 0);
    document.querySelectorAll('.piezas-restantes')
      .forEach(el => el.textContent = faltan);

    if (alertaMay)  alertaMay.style.display  = data.mayoreo ? 'flex' : 'none';
    if (alertaMeta) alertaMeta.style.display = (!data.mayoreo && faltan > 0) ? 'flex' : 'none';

    // Calcular totales
    const total = data.items.reduce((acc, item) => {
      const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
      return acc + precio * item.cantidad;
    }, 0);

    console.log('[updateTotals] Total calculado:', total);

    // Actualizar subtotal y total en el resumen
    const subtotalEl = document.getElementById('carrito-main-subtotal');
    console.log('[updateTotals] Elemento subtotal:', subtotalEl);
    console.log('[updateTotals] Valor ANTES:', subtotalEl ? subtotalEl.textContent : 'ELEMENTO NO EXISTE');
    if (subtotalEl) {
      subtotalEl.textContent = `$${total.toFixed(2)}`;
      console.log('[updateTotals] Valor DESPUES:', subtotalEl.textContent);
      // Forzar actualizaci├│n visual
      subtotalEl.style.color = 'red';
      setTimeout(() => { subtotalEl.style.color = ''; }, 100);
    }
    
    const resumenTotal = document.getElementById('resumen-total');
    console.log('[updateTotals] Elemento total:', resumenTotal);
    console.log('[updateTotals] Total ANTES:', resumenTotal ? resumenTotal.textContent : 'ELEMENTO NO EXISTE');
    if (resumenTotal) {
      resumenTotal.textContent = `$${total.toFixed(2)}`;
      console.log('[updateTotals] Total DESPUES:', resumenTotal.textContent);
    }

    // Actualizar variables globales
    window.CARRITO_TOTAL = total;

    // Actualizar precios y subtotales si cambia a mayoreo
    if (Array.isArray(data.items)) {
      data.items.forEach(item => {
        const itemEl = document.querySelector(`.carrito-item[data-variante-id="${item.variante_id}"]`);
        if (!itemEl) return;

        const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
        const precioEl = itemEl.querySelector('.precio-unitario-wrapper');
        const subtotalEl = itemEl.querySelector('.item-subtotal');

        if (precioEl) precioEl.textContent = `$${precio.toFixed(2)}`;
        if (subtotalEl) subtotalEl.textContent = `$${(precio * item.cantidad).toFixed(2)}`;
      });
    }
  }

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  // click en + / ÔêÆ / eliminar
  document.body.addEventListener('click', async e => {
    // Bot├│n eliminar (X)
    const removeBtn = e.target.closest('.item-remove');
    if (removeBtn) {
      const varId = removeBtn.dataset.variante;
      const item = removeBtn.closest('.carrito-item');
      item.classList.add('fade-out');
      item.addEventListener('animationend', async () => {
        const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };
        const r = await fetchWithAuth(`${API_BASE}/item/${varId}/eliminar/`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            ...(IS_LOGGED && { Authorization: `Bearer ${TOKEN}` })
          }
        });
        if (r.ok) {
          item.remove();
          document.dispatchEvent(new CustomEvent('carrito-actualizado'));
        } else {
          item.classList.remove('fade-out');
        }
      }, { once: true });
      return;
    }
    
    const plus  = e.target.closest('.btn-plus');
    const minus = e.target.closest('.btn-minus');
    if (!plus && !minus) return;

    const wrap  = (plus || minus).closest('.qty-wrap');
    const input = wrap.querySelector('.qty');
    const varId = wrap.closest('.carrito-item').dataset.varianteId;
    if (!varId) return;

    let val = parseInt(input.value) || 1;

    if (plus) {
      val++;
    } else {
      if (val === 1) {
        // eliminar
        const item = wrap.closest('.carrito-item');
        item.classList.add('fade-out');
        item.addEventListener('animationend', async () => {
          const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };

          const r = await fetchWithAuth(`${API_BASE}/item/${varId}/eliminar/`, {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
              ...(IS_LOGGED && { Authorization: `Bearer ${TOKEN}` })
            }
          });
          if (r.ok) {
            item.remove();
            document.dispatchEvent(new CustomEvent('carrito-actualizado'));
          } else {
            alert('No se pudo eliminar el producto.');
            item.classList.remove('fade-out');
          }
        }, { once: true });
        return;
      }
      val--;
    }

    input.value = val;
    if (await patchCantidad(varId, val)) {
      // ­ƒöä actualizar icono din├ímicamente
      const btn = wrap.querySelector('.btn-minus');
      if (val === 1) {
        btn.classList.add('trash');
        btn.innerHTML = `<i class="fa-solid fa-trash"></i>`;
      } else {
        btn.classList.remove('trash');
        btn.textContent = 'ÔêÆ';
      }
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    }
  });

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  // cambio manual en input qty
  document.body.addEventListener('change', async e => {
    if (!e.target.classList.contains('qty')) return;
    const input = e.target;
    const wrap  = input.closest('.qty-wrap');
    const varId = input.closest('.carrito-item').dataset.varianteId;
    let val = parseInt(input.value) || 1;
    if (val < 1) val = 1;
    input.value = val;

    if (await patchCantidad(varId, val)) {
      // ­ƒöä tambi├®n actualizar icono din├ímicamente
      const btn = wrap.querySelector('.btn-minus');
      if (val === 1) {
        btn.classList.add('trash');
        btn.innerHTML = `<i class="fa-solid fa-trash"></i>`;
      } else {
        btn.classList.remove('trash');
        btn.textContent = 'ÔêÆ';
      }
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    }
  });

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  // vaciar carrito completo
  document.querySelector('.btn-vaciar')?.addEventListener('click', async () => {
    if (!confirm('┬┐Vaciar todo el carrito?')) return;

    // ­ƒöÉ JWT: fetchDelete agrega token autom├íticamente
    const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };

    const r = await fetchWithAuth(`${API_BASE}/empty/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...(IS_LOGGED && { Authorization: `Bearer ${TOKEN}` })
      }
    });
    if (r.ok) document.dispatchEvent(new CustomEvent('carrito-actualizado'));
  });

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  function ensureConfirmButtonVisible(carritoId) {
    console.log('[Carrito] ensureConfirmButtonVisible llamado con carritoId:', carritoId);
    
    // Guardar en variable global para el handler del HTML
    window.CARRITO_ID = carritoId;
    console.log('[Carrito] window.CARRITO_ID configurado a:', window.CARRITO_ID);
  }

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  function modalGuest() {
    let m = document.getElementById('guest-checkout-modal');
    if (m) { m.classList.add('open'); return; }
    m = document.createElement('div');
    m.id = 'guest-checkout-modal';
    m.className = 'modal-overlay';
    m.innerHTML = `<div class="modal">
      <h3>┬┐C├│mo deseas continuar?</h3>
      <button class="btn-guest-checkout">Comprar como invitado</button>
      <button class="btn-login">Iniciar sesi├│n / Registrarse</button>
      <button class="modal-close">Ô£ò</button>
    </div>`;
    document.body.appendChild(m);

    m.addEventListener('click', e => {
      if (e.target === m || e.target.classList.contains('modal-close')) m.remove();
      if (e.target.classList.contains('btn-login')) {
        m.remove(); window.mostrarLoginPanel?.();
      }
      if (e.target.classList.contains('btn-guest-checkout')) {
        m.remove(); window.location.href = '/checkout/guest/';
      }
    });
  }

  // ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  window.alternarVistaCarrito = hay => {
    const activo = document.getElementById('carrito-activo');
    const vacio = document.getElementById('carrito-vacio');
    const btnCheckout = document.getElementById('btn-checkout');
    
    if (activo) {
      if (hay) {
        activo.style.display = '';
        activo.classList.add('visible');
      } else {
        activo.style.display = 'none';
        activo.classList.remove('visible');
      }
    }
    if (vacio) vacio.style.display = hay ? 'none' : 'flex';
    if (btnCheckout) btnCheckout.disabled = !hay;
  };

  window.updateTotals = updateTotals;

  document.addEventListener('carrito-actualizado', async () => {
    await renderCarritoDesdeAPI();
    await updateTotals();
  });

  renderCarritoDesdeAPI();
  updateTotals();
});
