/* main.js – ES module (smooth expand / collapse) */
document.addEventListener('DOMContentLoaded', async () => {

  /* ====== elementos base ====== */
  const selInicial  = document.getElementById('select-talla-inicial');
  const contLineas  = document.getElementById('lineas-tallas');
  const selExtra    = document.getElementById('select-talla-extra');
  const wrapExtra   = document.getElementById('wrapper-select-extra');
  const btnAddCart  = document.getElementById('btn-agregar-carrito');
  const msg         = document.getElementById('mensaje-carrito');
  const stockInfo   = document.getElementById('info-stock');
  const variantes   = JSON.parse(document.getElementById('variantes-data').textContent);

  const datos = document.getElementById('detalles-datos');
  const cliId = datos?.dataset.clienteId;
  const prodId = +datos?.dataset.productoId;

  const elegidas = new Set();

  /* ====== helpers ====== */
  const getCSRF = () =>
    decodeURIComponent(document.cookie.split(';').map(c => c.trim())
      .find(c => c.startsWith('csrftoken='))?.split('=')[1] || '');

  const stockTxt = talla => {
    const v = variantes.find(x => x.talla === talla);
    return v ? `Talla ${talla}: Stock disponible ${v.stock}` : '';
  };

  /* ====== reintento post-login ====== */
  const prelogin = sessionStorage.getItem('prelogin_carrito');
  if (cliId && prelogin) {
    try {
      const { producto_id, items } = JSON.parse(prelogin);
      if (producto_id === prodId && Array.isArray(items)) {
        let total = 0;
        for (const item of items) {
          // 🔐 JWT: fetchPost agrega token automáticamente
          const res = await fetchPost(`/api/carrito/create/${cliId}/`, {
            producto_id,
            talla: item.talla,
            cantidad: item.cantidad
          });
          if (res.ok) total += item.cantidad;
        }
        if (total > 0) {
          msg.style.color = 'green';
          msg.textContent = `✔️ Se agregaron ${total} unidades al carrito tras iniciar sesión.`;
        }
      }
    } catch (err) {
      console.error('Error al procesar prelogin_carrito:', err);
    }
    sessionStorage.removeItem('prelogin_carrito');
  }

  /* ====== crear línea ====== */
  function crearLinea(selectEl) {
    const talla = selectEl.value;
    if (!talla || elegidas.has(talla)) return;

    elegidas.add(talla);
    if (stockInfo) stockInfo.textContent = stockTxt(talla);

    const fila = document.createElement('div');
    fila.className = 'linea-talla';
    fila.dataset.talla = talla;
    fila.style.maxHeight = '0';
    fila.style.opacity = '0';
    fila.style.transform = 'translateX(40px)';

    const qtyWrap = document.createElement('div');
    qtyWrap.className = 'qty-wrap';
    qtyWrap.innerHTML = `
      <button class="btn-minus">−</button>
      <input type="number" min="1" value="1" class="qty">
      <button class="btn-plus">+</button>`;
    
    const qty = qtyWrap.querySelector('.qty');
    const btnMinus = qtyWrap.querySelector('.btn-minus');
    const btnPlus  = qtyWrap.querySelector('.btn-plus');

    btnMinus.onclick = () => {
      if (+qty.value > 1) {
        qty.value--;
        actualizarBtnMinus();
      } else {
        eliminarFila();
      }
    };

    btnPlus.onclick = () => {
      qty.value++;
      actualizarBtnMinus();
    };

    function actualizarBtnMinus() {
      const cantidad = +qty.value;
      if (cantidad === 1) {
        btnMinus.innerHTML = '<i class="fas fa-trash"></i>';
        btnMinus.classList.add('trash');
      } else {
        btnMinus.textContent = '−';
        btnMinus.classList.remove('trash');
      }
    }

    function eliminarFila() {
      fila.style.maxHeight = '0';
      fila.style.opacity = '0';
      fila.style.transform = 'translateX(40px)';
      fila.addEventListener('transitionend', () => {
        fila.remove();
        elegidas.delete(selectEl.value);
        if (!elegidas.size && stockInfo) stockInfo.textContent = '';
      }, { once: true });
    }

    actualizarBtnMinus();function actualizarBtnMinus() {
   const cantidad = +qty.value;
  if (cantidad === 1) {
    btnMinus.innerHTML = '<i class="fas fa-trash"></i>';
    btnMinus.classList.add('trash');
  } else {
    // Si era un ícono, primero aplica fade-out
    if (btnMinus.classList.contains('trash')) {
      btnMinus.classList.add('fade-out');

      // Espera la animación antes de cambiar
      setTimeout(() => {
        btnMinus.textContent = '−';
        btnMinus.classList.remove('trash', 'fade-out');
      }, 200); // debe coincidir con el duration de fadeOutIcon
    } else {
      btnMinus.textContent = '−';
      btnMinus.classList.remove('trash');
    }
  }
}



    selectEl.className = 'talla-select';
    selectEl.dataset.old = talla;
    selectEl.onchange = () => cambioTalla(selectEl);

    fila.append(selectEl, qtyWrap);

    contLineas.appendChild(fila);

    requestAnimationFrame(() => {
      fila.style.maxHeight = fila.scrollHeight + 'px';
      fila.style.opacity = '1';
      fila.style.transform = 'translateX(0)';
    });
  }

  function cambioTalla(sel) {
    const antes = sel.dataset.old;
    const ahora = sel.value;
    if (!ahora) { sel.value = antes; return; }

    if (elegidas.has(ahora) && ahora !== antes) {
      alert('Esa talla ya está añadida.');
      sel.value = antes;
      return;
    }
    elegidas.delete(antes); elegidas.add(ahora);
    sel.closest('.linea-talla').dataset.talla = ahora;
    sel.dataset.old = ahora;
    if (stockInfo) stockInfo.textContent = stockTxt(ahora);
  }

  selInicial.addEventListener('change', function onSelInicialChange() {
    crearLinea(selInicial);
    wrapExtra.style.display = 'block';
    selInicial.removeEventListener('change', onSelInicialChange);
  });

  selExtra.addEventListener('change', () => {
    if (selExtra.value && !elegidas.has(selExtra.value)) {
      const nuevo = selExtra.cloneNode(true);
      nuevo.value = selExtra.value;
      crearLinea(nuevo);
      selExtra.value = '';
    }
  });

btnAddCart.addEventListener('click', async () => {
  const seleccion = [];
  contLineas.querySelectorAll('.linea-talla').forEach(fila => {
    seleccion.push({
      talla: fila.dataset.talla,
      cantidad: +fila.querySelector('.qty').value
    });
  });

  if (!seleccion.length) {
    msg.style.color = 'orange';
    msg.textContent = '⚠️ No has añadido tallas.';
    return;
  }

  msg.textContent = '';
  let total = 0;

  for (const item of seleccion) {
    try {
      let endpoint = '';
      if (cliId) {
        endpoint = `/api/carrito/create/${cliId}/`;
      } else {
        endpoint = `/api/carrito/create/0/`;  // ✅ ESTA es la ruta correcta
      }

      // 🔐 JWT: fetchPost agrega token automáticamente si el usuario está logueado
      const res = await fetchPost(endpoint, {
        producto_id: prodId,
        talla: item.talla,
        cantidad: item.cantidad
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al agregar producto');

      total += item.cantidad;

    } catch (e) {
      msg.style.color = 'red';
      msg.textContent = '❌ ' + e.message;
      return;
    }
  }


  msg.style.color = 'green';
  msg.textContent = `✔️ Se agregaron ${total} unidades al carrito.`;
});


  document.querySelectorAll('.detalle-section')
          .forEach(sec => sec.classList.add('fade-in'));
});
