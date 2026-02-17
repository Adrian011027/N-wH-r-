/* main.js – ES module (smooth expand / collapse + JWT) */
/* Actualizado para modelo: 1 variante = 1 color con tallas_stock JSONField */

// Las funciones fetchPost, fetchWithAuth, etc. están disponibles globalmente desde fetch-helper.js

document.addEventListener('DOMContentLoaded', async () => {

  // Verificar que fetch-helper.js esté cargado
  if (typeof window.fetchPost === 'undefined') {
    console.error('Error: fetch-helper.js no está cargado. Las funciones fetchPost no están disponibles.');
    return;
  }

  /* ====== elementos base ====== */
  const selInicial  = document.getElementById('select-talla-inicial');
  const selColor    = document.getElementById('select-color');
  const contLineas  = document.getElementById('lineas-tallas');
  const selExtra    = document.getElementById('select-talla-extra');
  const wrapExtra   = document.getElementById('wrapper-select-extra');
  const btnAddCart   = document.getElementById('btn-agregar-carrito');
  const stockInfo   = document.getElementById('info-stock');
  const variantes   = JSON.parse(document.getElementById('variantes-data').textContent);

  const datos = document.getElementById('detalles-datos');
  const prodId = +datos?.dataset.productoId;

  const elegidas = new Set();

  /* ====== auth: JWT ====== */
  const TOKEN      = localStorage.getItem("access");
  const CLIENTE_ID = Number(localStorage.getItem("user_id") || 0);
  const IS_LOGGED  = !!TOKEN;

  /* ====== helpers para nuevo modelo ====== */

  // Obtener variante seleccionada por color
  function getVarianteActiva() {
    if (!selColor) return variantes[0] || null;
    const colorVal = selColor.value;
    if (!colorVal) return variantes[0] || null;
    return variantes.find(v => v.color === colorVal) || variantes[0] || null;
  }

  // Obtener stock de una talla en la variante activa
  function getStockTalla(talla) {
    const v = getVarianteActiva();
    if (!v || !v.tallas_stock) return 0;
    return v.tallas_stock[talla] || 0;
  }

  // Obtener tallas disponibles para color actual (con stock > 0)
  function getTallasDisponibles() {
    const v = getVarianteActiva();
    if (!v || !v.tallas_stock) return [];
    return Object.entries(v.tallas_stock)
      .filter(([_, stock]) => stock > 0)
      .map(([talla]) => talla);
  }

  // Actualizar opciones del selector de tallas según color activo
  function actualizarSelectorTallas(selectEl) {
    const tallasDisp = getTallasDisponibles();
    const currentVal = selectEl.value;

    // Guardar la primera opción (placeholder)
    const placeholder = selectEl.options[0];
    selectEl.innerHTML = '';
    selectEl.appendChild(placeholder);

    tallasDisp.forEach(t => {
      if (elegidas.has(t)) return; // no mostrar tallas ya elegidas
      const opt = document.createElement('option');
      opt.value = t;
      opt.textContent = t;
      if (t === currentVal) opt.selected = true;
      selectEl.appendChild(opt);
    });
  }

  const stockTxt = talla => {
    const stock = getStockTalla(talla);
    return stock > 0 ? `Talla ${talla}: Stock disponible ${stock}` : '';
  };

  /* ====== actualizar carrusel con imágenes de variante ====== */
  function actualizarCarruselVariante() {
    const variante = getVarianteActiva();
    if (variante && variante.imagenes && variante.imagenes.length > 0 && window.productoCarrusel) {
      window.productoCarrusel.changeImages(variante.imagenes);
    }
  }

  /* ====== listener de color ====== */
  if (selColor) {
    const isSelect = selColor.tagName === 'SELECT';
    const onColorChange = () => {
      // Limpiar líneas existentes al cambiar color
      elegidas.clear();
      contLineas.innerHTML = '';
      wrapExtra.style.display = 'none';

      // Re-crear selector inicial
      actualizarSelectorTallas(selInicial);
      selInicial.value = '';
      selInicial.addEventListener('change', function onSelInicialChange() {
        crearLinea(selInicial);
        wrapExtra.style.display = 'block';
        selInicial.removeEventListener('change', onSelInicialChange);
      });

      if (selExtra) actualizarSelectorTallas(selExtra);
      actualizarCarruselVariante();

      // Actualizar precio
      const v = getVarianteActiva();
      if (v) {
        const precioEl = document.getElementById('precio-actual');
        if (precioEl) precioEl.textContent = `$${Number(v.precio).toFixed(2)}`;
      }
      if (stockInfo) stockInfo.textContent = '';
    };

    if (isSelect) {
      selColor.addEventListener('change', onColorChange);
    }
    // Inicializar tallas al cargar (para select o hidden input)
    actualizarSelectorTallas(selInicial);
  }

  /* ====== reintento post-login ====== */
  const prelogin = sessionStorage.getItem('prelogin_carrito');
  if (CLIENTE_ID && prelogin) {
    try {
      const { producto_id, items } = JSON.parse(prelogin);
      if (producto_id === prodId && Array.isArray(items)) {
        let total = 0;
        for (const item of items) {
          const res = await window.fetchPost(`/api/carrito/create/${CLIENTE_ID}/`, {
            producto_id,
            talla: item.talla,
            variante_id: item.variante_id,
            cantidad: item.cantidad
          });
          if (res.ok) total += item.cantidad;
        }
        if (total > 0) {
          mostrarToast(`${total} ${total === 1 ? 'artículo agregado' : 'artículos agregados'}`, 'success');
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

    // Actualizar carrusel con imágenes de la variante activa
    actualizarCarruselVariante();

    const fila = document.createElement('div');
    fila.className = 'linea-talla';
    fila.dataset.talla = talla;
    // Guardar variante_id para enviar al carrito
    const varActiva = getVarianteActiva();
    fila.dataset.varianteId = varActiva ? varActiva.id : '';
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
        if (btnMinus.classList.contains('trash')) {
          btnMinus.classList.add('fade-out');
          setTimeout(() => {
            btnMinus.textContent = '−';
            btnMinus.classList.remove('trash', 'fade-out');
          }, 200);
        } else {
          btnMinus.textContent = '−';
          btnMinus.classList.remove('trash');
        }
      }
    }

    function eliminarFila() {
      fila.style.maxHeight = '0';
      fila.style.opacity = '0';
      fila.style.transform = 'translateX(40px)';
      fila.addEventListener('transitionend', () => {
        fila.remove();
        elegidas.delete(talla);
        if (!elegidas.size && stockInfo) stockInfo.textContent = '';
        // Restaurar talla eliminada en los selectores
        if (selExtra) actualizarSelectorTallas(selExtra);
      }, { once: true });
    }

    actualizarBtnMinus();

    selectEl.className = 'talla-select';
    selectEl.dataset.old = talla;
    selectEl.onchange = () => cambioTalla(selectEl);

    fila.append(selectEl, qtyWrap);
    contLineas.appendChild(fila);

    // Actualizar selector extra para quitar talla elegida
    if (selExtra) actualizarSelectorTallas(selExtra);

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

    actualizarCarruselVariante();
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

  /* ====== botón agregar al carrito ====== */
  btnAddCart.addEventListener('click', async () => {
    const seleccion = [];
    const varActiva = getVarianteActiva();
    
    contLineas.querySelectorAll('.linea-talla').forEach(fila => {
      const talla = fila.dataset.talla;
      const cantidad = +fila.querySelector('.qty').value;
      
      seleccion.push({
        talla: talla,
        variante_id: varActiva ? varActiva.id : null,
        cantidad: cantidad
      });
    });

    if (seleccion.length === 0) {
      mostrarToast('Selecciona al menos una talla', 'error');
      return;
    }

    let total = 0;
    let errores = [];

    console.log('Procesando selección:', seleccion);

    for (const item of seleccion) {
      try {
        // Validar stock antes de enviar
        const stockDisp = getStockTalla(item.talla);
        if (stockDisp < item.cantidad) {
          errores.push(`Talla ${item.talla}: solo hay ${stockDisp} unidades disponibles`);
          continue;
        }

        let endpoint = '';
        if (CLIENTE_ID) {
          endpoint = `/api/carrito/create/${CLIENTE_ID}/`;
        } else {
          endpoint = `/api/carrito/create/0/`;
        }

        const body = {
          producto_id: prodId,
          talla: item.talla,
          cantidad: item.cantidad
        };
        if (item.variante_id) body.variante_id = item.variante_id;

        console.log('Enviando al carrito:', body);
        const res = await window.fetchPost(endpoint, body);
        const data = await res.json();
        console.log('Respuesta del servidor:', res.status, data);
        
        if (!res.ok) {
          errores.push(data.error || 'Error al agregar producto');
          continue;
        }

        total += item.cantidad;

      } catch (e) {
        console.error('Error al procesar item:', e);
        errores.push(e.message);
      }
    }

    console.log('Total agregado:', total, 'Errores:', errores);

    // Mostrar resultados
    if (errores.length > 0 && total === 0) {
      mostrarToast(errores[0], 'error');
    } else if (errores.length > 0 && total > 0) {
      mostrarToast(`${total} ${total === 1 ? 'artículo agregado' : 'artículos agregados'}`, 'success');
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    } else if (total > 0) {
      mostrarToast(`${total} ${total === 1 ? 'artículo agregado' : 'artículos agregados'}`, 'success');
      document.dispatchEvent(new CustomEvent('carrito-actualizado'));
    }
  });

  /* ====== toast overlay ====== */
  const toastOverlay = document.getElementById('toast-overlay');
  const toastText    = document.getElementById('toast-text');
  let toastTimer     = null;

  function mostrarToast(texto, tipo = 'success') {
    if (!toastOverlay || !toastText) return;

    clearTimeout(toastTimer);
    toastText.textContent = texto;
    toastOverlay.className = 'toast-overlay';
    if (tipo === 'error') toastOverlay.classList.add('toast-error');

    // Forzar reflow para reiniciar animación
    void toastOverlay.offsetWidth;
    toastOverlay.classList.add('visible');

    toastTimer = setTimeout(() => {
      toastOverlay.classList.remove('visible');
    }, 1800);
  }

  /* animación de secciones */
  document.querySelectorAll('.detalle-section')
          .forEach(sec => sec.classList.add('fade-in'));
});
