document.addEventListener('DOMContentLoaded', () => {
  const ID = Number(window.CLIENTE_ID || 0);
  const IS_LOGGED = ID > 0;
  const SESSION_KEY = window.SESSION_KEY || '';
  const API_BASE = IS_LOGGED ? `/api/carrito/${ID}` : `/api/carrito/guest`;

  const getCookie = name => {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : null;
  };

  async function patchCantidad(varId, cant) {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (IS_LOGGED) headers['X-CSRFToken'] = getCookie('csrftoken');
    else headers['X-Session-Key'] = SESSION_KEY;

    const res = await fetch(`${API_BASE}/item/${varId}/actualizar/`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ cantidad: cant })
    });
    return res.ok;
  }

  async function renderCarritoDesdeAPI() {
    const res = await fetch(`${API_BASE}/`, {
      headers: IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY }
    });
    const data = await res.json();
    const contenedor = document.querySelector('.carrito-items');
    if (!contenedor || !Array.isArray(data.items)) return;

    const actuales = new Set([...contenedor.children].map(el => el.dataset.varianteId));
    const nuevos = new Set(data.items.map(item => String(item.variante_id)));

    [...contenedor.children].forEach(child => {
      const id = child.dataset.varianteId;
      if (!nuevos.has(id)) {
        child.classList.add('fade-out');
        child.addEventListener('animationend', () => child.remove(), { once: true });
      }
    });

    for (const item of data.items) {
      const id = String(item.variante_id);
      if (actuales.has(id)) {
        // 🟢 Actualiza precio y badge incluso si ya está en el DOM
        const itemEl = contenedor.querySelector(`[data-variante-id="${id}"]`);
        if (itemEl) {
          const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
          const precioEl = itemEl.querySelector('.precio-unitario');
          const badgeEl = itemEl.querySelector('.badge');

          if (precioEl) precioEl.textContent = `$${precio.toFixed(2)}`;
          if (badgeEl) {
            badgeEl.textContent = `(${data.mayoreo ? 'mayoreo' : 'menudeo'})`;
            badgeEl.className = `badge ${data.mayoreo ? 'badge-mayoreo' : 'badge-menudeo'}`;
          }
        }
        continue;
      }


      const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;

      const div = document.createElement('div');
      div.className = 'carrito-item';
      div.dataset.varianteId = id;

      const minusBtn = item.cantidad === 1
        ? `<button class="btn-minus trash" title="Eliminar"><i class="fa-solid fa-trash"></i></button>`
        : `<button class="btn-minus">−</button>`;

      div.innerHTML = `
        <div class="item-imagen">
          <img src="${item.imagen || '/static/img/no-image.jpg'}" alt="${item.producto}">
        </div>

        <div class="item-detalles">
          <h4>${item.producto}</h4>
          <span>${item.atributos?.join(', ') || 'Talla única'}</span>

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

    const total = data.items.reduce((acc, item) => {
      const precio = data.mayoreo ? item.precio_mayorista : item.precio_menudeo;
      return acc + precio * item.cantidad;
    }, 0);
    document.getElementById('carrito-subtotal').textContent = `$${total.toFixed(2)}`;
  }

  async function updateTotals() {
    const res = await fetch(`${API_BASE}/`, {
      headers: IS_LOGGED ? {} : { 'X-Session-Key': SESSION_KEY }
    });
    const data = await res.json();
    if (!res.ok) { console.error('[carrito]', data); return; }

    const hay = data.items?.length;
    window.alternarVistaCarrito?.(hay);

    const alertaMeta = document.getElementById('alerta-meta-mayoreo');
    const alertaMay = document.getElementById('alerta-mayoreo');

    if (!hay) {
      document.getElementById('carrito-subtotal').textContent = '$0.00';
      if (alertaMay) alertaMay.style.display = 'none';
      if (alertaMeta) alertaMeta.style.display = 'none';
      return;
    }

    const piezas = data.items.reduce((s, x) => s + x.cantidad, 0);
    const faltan = Math.max(6 - piezas, 0);
    document.querySelectorAll('.piezas-restantes')
      .forEach(el => el.textContent = faltan);

    if (alertaMay) alertaMay.style.display = data.mayoreo ? 'block' : 'none';
    if (alertaMeta) alertaMeta.style.display = (!data.mayoreo && faltan > 0) ? 'block' : 'none';
  }

  document.body.addEventListener('click', async e => {
    const plus = e.target.closest('.btn-plus');
    const minus = e.target.closest('.btn-minus');
    if (!plus && !minus) return;

    const wrap = (plus || minus).closest('.qty-wrap');
    const input = wrap.querySelector('.qty');
    const varId = wrap.closest('.carrito-item').dataset.varianteId;
    if (!varId) return;

    let val = parseInt(input.value) || 1;

    if (plus) {
      val++;
    } else {
      if (val === 1) {
        const item = wrap.closest('.carrito-item');
        item.classList.add('fade-out');

        item.addEventListener('animationend', async () => {
          const headers = IS_LOGGED
            ? { 'X-CSRFToken': getCookie('csrftoken') }
            : { 'X-Session-Key': SESSION_KEY };

          const r = await fetch(`${API_BASE}/item/${varId}/eliminar/`, {
            method: 'DELETE',
            headers
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
  const btn = wrap.querySelector('.btn-minus');

  if (val === 1) {
    if (!btn.classList.contains('trash')) {
      btn.classList.add('trash');
      btn.innerHTML = `<i class="fa-solid fa-trash fade-in-icon"></i>`;
    }
  } else {
    if (btn.classList.contains('trash')) {
      btn.classList.remove('trash');
      btn.textContent = '−';  // Asegura que siempre se vea el signo menos
    }
  }

  document.dispatchEvent(new CustomEvent('carrito-actualizado'));
}

  });

  document.body.addEventListener('change', async e => {
    if (!e.target.classList.contains('qty')) return;
    const input = e.target;
    const varId = input.closest('.carrito-item').dataset.varianteId;
    let val = parseInt(input.value) || 1;
    if (val < 1) val = 1;
    input.value = val;

    if (await patchCantidad(varId, val)) {
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    }
  });

  document.querySelector('.btn-vaciar')?.addEventListener('click', async () => {
    if (!confirm('¿Vaciar todo el carrito?')) return;

    const headers = IS_LOGGED
      ? { 'X-CSRFToken': getCookie('csrftoken') }
      : { 'X-Session-Key': SESSION_KEY };

    const r = await fetch(`${API_BASE}/empty/`, {
      method: 'DELETE',
      headers
    });

    if (r.ok) {
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    } else {
      alert('No se pudo vaciar el carrito.');
    }
  });

  document.querySelector('.btn-finalizar')?.addEventListener('click', e => {
    if (IS_LOGGED) return;
    e.preventDefault(); modalGuest();
  });

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

  window.alternarVistaCarrito = hay => {
    document.getElementById('carrito-activo').style.display = hay ? 'block' : 'none';
    document.getElementById('carrito-vacio').style.display = hay ? 'none' : 'block';
  };

  window.updateTotals = updateTotals;

  document.addEventListener('carrito-actualizado', async () => {
    await renderCarritoDesdeAPI();
    await updateTotals();

    const subtotalEl = document.getElementById('carrito-subtotal');
    if (subtotalEl) {
      subtotalEl.classList.remove('fade-in-extra');
      void subtotalEl.offsetWidth;
      subtotalEl.classList.add('fade-in-extra');
    }

    const botonesWrap = document.querySelector('.carrito-botones');
    if (botonesWrap) {
      botonesWrap.classList.remove('fade-in-extra');
      void botonesWrap.offsetWidth;
      botonesWrap.classList.add('fade-in-extra');
    }
  });

  renderCarritoDesdeAPI();
  updateTotals();

  document.getElementById('carrito-container')?.classList.add('fade-in-carrito');
});
