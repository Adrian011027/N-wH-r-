/* ==========================================================================
 * carrito.js – versión JWT + invitado funcional COMPLETA (con toggle trash/−)
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

  // ────────────────────────────────
  async function patchCantidad(varId, cant) {
    // 🔐 JWT: Usa fetchPatch que agrega automáticamente el token
    const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };
    
    const res = await fetchWithAuth(`${API_BASE}/item/${varId}/actualizar/`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ cantidad: cant })
    });
    return res.ok;
  }

  // ────────────────────────────────
  async function renderCarritoDesdeAPI() {
    // 🔐 JWT: fetchWithAuth agrega token automáticamente para usuarios logueados
    const headers = IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY };
    const res = await fetchWithAuth(`${API_BASE}/`, {
      headers
    });
    if (!res.ok) {
      console.error("[carrito] error al cargar:", res.status);
      return;
    }

    const data = await res.json();
    const contenedor = document.querySelector('.carrito-items');
    if (!contenedor || !Array.isArray(data.items)) return;

    const actuales = new Set([...contenedor.children].map(el => el.dataset.varianteId));
    const nuevos   = new Set(data.items.map(item => String(item.variante_id)));

    // quitar items que ya no están
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

      const div = document.createElement('div');
      div.className = 'carrito-item';
      div.dataset.varianteId = id;

      const minusBtn = item.cantidad === 1
        ? `<button class="btn-minus trash" title="Eliminar"><i class="fa-solid fa-trash"></i></button>`
        : `<button class="btn-minus">−</button>`;

      // Generar carrusel mini de imágenes
      const imagenes = item.imagenes_galeria || [];
      const allImages = [item.imagen, ...imagenes].filter(Boolean);
      
      let imagenesHTML = '';
      if (allImages.length > 1) {
        imagenesHTML = `
          <div class="carrusel-mini-viewport">
            <div class="carrusel-mini-track" style="transform: translateX(0%);">
              ${allImages.map(img => `<img src="${img}" alt="${item.producto}" class="carrusel-mini-slide">`).join('')}
            </div>
            <button class="carrusel-mini-prev" data-variante="${id}">‹</button>
            <button class="carrusel-mini-next" data-variante="${id}">›</button>
          </div>
        `;
      } else {
        imagenesHTML = `<img src="${item.imagen || '/static/img/no-image.jpg'}" alt="${item.producto}">`;
      }

      div.innerHTML = `
        <div class="item-imagen">
          ${imagenesHTML}
        </div>

        <div class="item-detalles">
          <h4>${item.producto}</h4>
          <span>${item.talla ? `Talla: ${item.talla}` : 'Talla única'}${item.color && item.color !== 'N/A' ? ` · Color: ${item.color}` : ''}</span>

          <div class="item-precio-cantidad">
            <div class="item-precio">
              <span class="precio-unitario-wrapper">
                <span class="precio-unitario">$${precio.toFixed(2)}</span>
              </span>
              <span class="badge ${data.mayoreo ? 'badge-mayoreo' : 'badge-menudeo'}">
                (${data.mayoreo ? 'mayoreo' : 'menudeo'})
              </span>
            </div>

            <div class="item-cantidad qty-wrap">
              ${minusBtn}
              <input type="number" class="qty" min="1" value="${item.cantidad}">
              <button class="btn-plus">＋</button>
            </div>
          </div>
        </div>
      `;

      contenedor.appendChild(div);
      requestAnimationFrame(() => div.classList.add('fade-in'));
    }

    // subtotal
    const total = data.items.reduce((acc, item) => {
      const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
      return acc + precio * item.cantidad;
    }, 0);
    document.getElementById('carrito-subtotal').textContent = `$${total.toFixed(2)}`;

    if (data.items.length > 0) {
      ensureConfirmButtonVisible(data.carrito_id);
    }

    window.alternarVistaCarrito?.(data.items.length);
  }

  // ────────────────────────────────
  async function updateTotals() {
    // 🔐 JWT: fetchWithAuth agrega token automáticamente
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
      document.getElementById('carrito-subtotal').textContent = '$0.00';
      if (alertaMay)  alertaMay.style.display  = 'none';
      if (alertaMeta) alertaMeta.style.display = 'none';
      return;
    }

    const piezas = data.items.reduce((s, x) => s + x.cantidad, 0);
    const faltan = Math.max(6 - piezas, 0);
    document.querySelectorAll('.piezas-restantes')
      .forEach(el => el.textContent = faltan);

    if (alertaMay)  alertaMay.style.display  = data.mayoreo ? 'block' : 'none';
    if (alertaMeta) alertaMeta.style.display = (!data.mayoreo && faltan > 0) ? 'block' : 'none';

    // 🔄 Actualizar precios unitarios visibles si cambia a mayoreo
    if (Array.isArray(data.items)) {
      data.items.forEach(item => {
        const itemEl = document.querySelector(`.carrito-item[data-variante-id="${item.variante_id}"]`);
        if (!itemEl) return;

        const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
        const precioEl = itemEl.querySelector('.precio-unitario');
        const badgeEl  = itemEl.querySelector('.badge');

        if (precioEl) precioEl.textContent = `$${precio.toFixed(2)}`;
        if (badgeEl) {
          badgeEl.textContent = `(${data.mayoreo ? 'mayoreo' : 'menudeo'})`;
          badgeEl.className   = `badge ${data.mayoreo ? 'badge-mayoreo' : 'badge-menudeo'}`;
        }
      });
    }

  }

  // ────────────────────────────────
  // click en + / − / eliminar
  document.body.addEventListener('click', async e => {
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
          // 🔐 JWT: fetchDelete agrega token automáticamente
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
      // 🔄 actualizar icono dinámicamente
      const btn = wrap.querySelector('.btn-minus');
      if (val === 1) {
        btn.classList.add('trash');
        btn.innerHTML = `<i class="fa-solid fa-trash"></i>`;
      } else {
        btn.classList.remove('trash');
        btn.textContent = '−';
      }
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    }
  });

  // ────────────────────────────────
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
      // 🔄 también actualizar icono dinámicamente
      const btn = wrap.querySelector('.btn-minus');
      if (val === 1) {
        btn.classList.add('trash');
        btn.innerHTML = `<i class="fa-solid fa-trash"></i>`;
      } else {
        btn.classList.remove('trash');
        btn.textContent = '−';
      }
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    }
  });

  // ────────────────────────────────
  // vaciar carrito completo
  document.querySelector('.btn-vaciar')?.addEventListener('click', async () => {
    if (!confirm('¿Vaciar todo el carrito?')) return;

    // 🔐 JWT: fetchDelete agrega token automáticamente
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

  // ────────────────────────────────
  // Mini-carrusel de imágenes en items del carrito
  document.body.addEventListener('click', e => {
    const miniPrev = e.target.closest('.carrusel-mini-prev');
    const miniNext = e.target.closest('.carrusel-mini-next');
    
    if (!miniPrev && !miniNext) return;
    
    const viewport = (miniPrev || miniNext).closest('.carrusel-mini-viewport');
    const track = viewport?.querySelector('.carrusel-mini-track');
    const slides = track?.querySelectorAll('.carrusel-mini-slide');
    
    if (!track || !slides || slides.length <= 1) return;
    
    // Obtener índice actual
    let currentIndex = 0;
    const transform = track.style.transform;
    const match = transform.match(/translateX\((-?\d+)%\)/);
    if (match) {
      currentIndex = Math.abs(parseInt(match[1]) / 100);
    }
    
    // Mover al siguiente o anterior
    if (miniNext) {
      currentIndex = (currentIndex + 1) % slides.length;
    } else {
      currentIndex = (currentIndex - 1 + slides.length) % slides.length;
    }
    
    track.style.transform = `translateX(-${currentIndex * 100}%)`;
  });

  // ────────────────────────────────
    const botonesWrapper = document.querySelector('.carrito-botones');
    if (!botonesWrapper) return;

    const existente = botonesWrapper.querySelector('.btn-finalizar');
    if (existente) existente.remove();

    const seguirBtn = botonesWrapper.querySelector('.btn-seguir');

    if (IS_LOGGED) {
      const enlace = document.createElement('a');
      enlace.className = 'btn-finalizar';
      enlace.textContent = 'Finalizar compra';
      enlace.href = `/ordenar/${carritoId}/`;
      botonesWrapper.insertBefore(enlace, seguirBtn);
    } else {
      const enlace = document.createElement('button');
      enlace.className = 'btn-finalizar';
      enlace.textContent = 'Finalizar compra';
      enlace.addEventListener('click', e => {
        e.preventDefault(); modalGuest();
      });
      botonesWrapper.insertBefore(enlace, seguirBtn);
    }
  }

  // ────────────────────────────────
  function modalGuest() {
    let m = document.getElementById('guest-checkout-modal');
    if (m) { m.classList.add('open'); return; }
    m = document.createElement('div');
    m.id = 'guest-checkout-modal';
    m.className = 'modal-overlay';
    m.innerHTML = `<div class="modal">
      <h3>¿Cómo deseas continuar?</h3>
      <button class="btn-guest-checkout">Comprar como invitado</button>
      <button class="btn-login">Iniciar sesión / Registrarse</button>
      <button class="modal-close">✕</button>
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

  // ────────────────────────────────
  window.alternarVistaCarrito = hay => {
    document.getElementById('carrito-activo').style.display = hay ? 'block' : 'none';
    document.getElementById('carrito-vacio').style.display  = hay ? 'none'  : 'block';
  };

  window.updateTotals = updateTotals;

  document.addEventListener('carrito-actualizado', async () => {
    await renderCarritoDesdeAPI();
    await updateTotals();
  });

  renderCarritoDesdeAPI();
  updateTotals();
  document.getElementById('carrito-container')?.classList.add('fade-in-carrito');
});
