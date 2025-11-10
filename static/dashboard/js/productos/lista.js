/* lista.js – dashboard de productos (con JWT) */
document.addEventListener('DOMContentLoaded', cargarProductos);

/* ---------- Helpers JWT ---------- */
function getAccessToken() {
  return localStorage.getItem("access");
}

/* ---------- CARGA Y RENDER ---------- */
async function cargarProductos() {
  try {
    const res = await fetch('/api/productos/', {
      headers: {
        "Authorization": `Bearer ${getAccessToken()}`,
        "Content-Type": "application/json",
      }
    });
    if (!res.ok) throw new Error('Error al obtener productos');
    const productos = await res.json();

    const container = document.getElementById('productos-container');
    container.innerHTML = '';

    if (!productos.length) {
      container.innerHTML = '<p>No hay productos registrados.</p>';
      return;
    }

    productos.forEach(p => container.appendChild(crearCard(p)));
  } catch (err) {
    document.getElementById('productos-container').innerHTML =
      `<p>Error: ${err.message}</p>`;
  }
}

function crearCard(p) {
  const card = document.createElement('div');
  card.className = 'producto-card';

  /* variantes detalladas */
  const variantesHTML = p.variantes?.length
    ? '<ul>' + p.variantes.map(v => {
        const talla = v.atributos?.Talla ?? '—';
        return `<li><strong>Talla:</strong> ${talla} |
                     <strong>Precio:</strong> $${v.precio} |
                     <strong>Precio Mayorista:</strong> $${v.precio_mayorista} |
                     <strong>Stock:</strong> ${v.stock}</li>`;
      }).join('') + '</ul>'
    : '<p>No hay variantes registradas.</p>';

  card.innerHTML = `
    <img src="${p.imagen}" alt="Imagen de ${p.nombre}" height="120">
    <h3>${p.nombre}</h3>
    <p><strong>Descripción:</strong> ${p.descripcion}</p>
    <p><strong>Categoría:</strong> ${p.categoria}</p>
    <p><strong>Género:</strong> ${p.genero}</p>
    <p><strong>Precio Mayorista:</strong> $${p.precio_mayorista ?? '—'}</p>
    <p><strong>Oferta:</strong> ${p.en_oferta ? 'Sí' : 'No'}</p>
    <p><strong>Stock total:</strong> ${p.stock_total}</p>
    <p><strong>Variantes:</strong></p>
    ${variantesHTML}
    <button class="btn-editar">✏️ Editar</button>
    <button class="btn-eliminar">🗑️ Eliminar</button>
    <hr>
  `;

  /* listeners */
  card.querySelector('.btn-editar')
      .addEventListener('click', () => editarProducto(p.id));
  card.querySelector('.btn-eliminar')
      .addEventListener('click', () => eliminarProducto(p.id, card));

  return card;
}

/* ---------- ACCIONES ---------- */
function editarProducto(id) {
  window.location.href = `/dashboard/productos/editar/${id}/`;
}

async function eliminarProducto(id, cardEl) {
  if (!confirm('¿Seguro que deseas eliminar este producto?')) return;

  try {
    const res = await fetch(`/api/productos/delete/${id}/`, {
      method: 'DELETE',
      headers: {
        "Authorization": `Bearer ${getAccessToken()}`,
        "Content-Type": "application/json",
      }
    });

    if (!res.ok) {
      const msg = await res.text();
      throw new Error(`Error ${res.status}: ${msg}`);
    }

    const data = await res.json();
    toast(data.mensaje || 'Producto eliminado ✔️');
    cardEl.remove();
  } catch (err) {
    toast('No se pudo eliminar: ' + err.message, true);
  }
}

/* ---------- NOTIFICACIÓN PEQUEÑA ---------- */
function toast(msg, err = false) {
  const t = document.createElement('div');
  t.textContent = msg;
  t.style.cssText =
    `position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
     padding:10px 20px;border-radius:4px;font-size:14px;
     background:${err ? '#c0392b' : '#27ae60'};color:#fff;
     z-index:9999;opacity:0;transition:opacity .3s`;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.style.opacity = 1);
  setTimeout(() => {
    t.style.opacity = 0;
    setTimeout(() => t.remove(), 300);
  }, 2500);
}
