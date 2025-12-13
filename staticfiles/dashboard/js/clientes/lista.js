/* lista.js – Dashboard lista de clientes con JWT */
document.addEventListener('DOMContentLoaded', async () => {
  const container = document.querySelector('.clientes-container');
  
  if (!container) return;

  try {
    await cargarClientes();
  } catch (err) {
    console.error('Error al cargar clientes:', err);
    toast('Error al cargar la lista de clientes', 'error');
  }

  // Event delegation para botones de eliminar
  container.addEventListener('click', async (e) => {
    const deleteBtn = e.target.closest('.btn-delete');
    if (!deleteBtn) return;

    const clienteId = deleteBtn.dataset.clienteId;
    const clienteNombre = deleteBtn.dataset.clienteNombre;

    if (!confirm(`¿Estás seguro de eliminar al cliente "${clienteNombre}"?`)) {
      return;
    }

    try {
      const response = await authFetch(`/clientes/delete/${clienteId}/`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al eliminar cliente');
      }

      toast(data.message || 'Cliente eliminado correctamente', 'success');
      
      // Recargar lista
      await cargarClientes();

    } catch (err) {
      toast(err.message, 'error');
      console.error(err);
    }
  });
});

async function cargarClientes() {
  const container = document.querySelector('.clientes-container');
  
  try {
    const response = await authFetch('/clientes/', {
      method: 'GET'
    });

    const clientes = await response.json();

    if (!response.ok) {
      throw new Error(clientes.error || 'Error al cargar clientes');
    }

    // Si no hay clientes
    if (!clientes || clientes.length === 0) {
      container.innerHTML = `
        <div class="no-data">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <p>No hay clientes registrados</p>
        </div>
      `;
      return;
    }

    // Renderizar tabla de clientes
    container.innerHTML = `
      <div class="table-container">
        <table class="clientes-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Usuario</th>
              <th>Nombre</th>
              <th>Correo</th>
              <th>Teléfono</th>
              <th>Dirección</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${clientes.map(c => `
              <tr>
                <td>#${c.id}</td>
                <td><strong>@${c.username}</strong></td>
                <td>${c.nombre || '—'}</td>
                <td>${c.correo || '—'}</td>
                <td>${c.telefono || '—'}</td>
                <td>${c.direccion || '—'}</td>
                <td>
                  <div class="action-buttons">
                    <a href="/dashboard/clientes/editar/${c.id}/" class="btn-edit" title="Editar">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </a>
                    <button class="btn-delete" 
                            data-cliente-id="${c.id}" 
                            data-cliente-nombre="${c.nombre || c.username}"
                            title="Eliminar">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    // Actualizar estadísticas si existen
    const totalElement = document.querySelector('.stat-number');
    if (totalElement) {
      totalElement.textContent = clientes.length;
    }

  } catch (err) {
    console.error('Error:', err);
    container.innerHTML = `
      <div class="error-state">
        <p>Error al cargar clientes: ${err.message}</p>
        <button onclick="location.reload()" class="btn-retry">Reintentar</button>
      </div>
    `;
  }
}

// Toast notification
function toast(msg, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  
  requestAnimationFrame(() => t.classList.add('show'));
  
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 400);
  }, 3000);
}
