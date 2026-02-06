document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("categorias-grid");
  const form = document.getElementById("form-categoria");
  const inputNombre = document.getElementById("nombre-categoria");
  const editForm = document.getElementById("edit-form");

  /* ─────────── Estados de vista ─────────── */
  function mostrarEstado(estado) {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('categorias-grid').style.display = 'none';
    document.getElementById('empty-state').style.display = 'none';

    switch (estado) {
      case 'loading':
        document.getElementById('loading-state').style.display = 'flex';
        break;
      case 'grid':
        document.getElementById('categorias-grid').style.display = 'grid';
        break;
      case 'empty':
        document.getElementById('empty-state').style.display = 'block';
        break;
    }
  }

  /* ─────────── Render grid ─────────── */
  function cargarCategorias() {
    mostrarEstado('loading');

    authFetch("/api/categorias/")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((categorias) => {
        if (!categorias) return;
        
        // Actualizar estadística
        document.getElementById('stat-total').textContent = categorias.length;

        if (categorias.length === 0) {
          mostrarEstado('empty');
          return;
        }

        grid.innerHTML = "";
        categorias.forEach((cat) => {
          const card = document.createElement("div");
          card.className = "categoria-card";
          card.innerHTML = `
            <div class="categoria-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div class="categoria-info">
              <span class="categoria-id">ID #${cat.id}</span>
              <h3 class="categoria-nombre">${cat.nombre}</h3>
            </div>
            <div class="categoria-actions">
              <button class="btn-icon edit" onclick="abrirModalEditar(${cat.id}, '${cat.nombre.replace(/'/g, "\\'")}')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button class="btn-icon delete" onclick="eliminarCategoria(${cat.id}, '${cat.nombre.replace(/'/g, "\\'")}')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          `;
          grid.appendChild(card);
        });
        mostrarEstado('grid');
      })
      .catch((err) => {
        console.error("Error cargando categorías:", err);
        showToast("Error al cargar categorías", "error");
      });
  }

  /* ─────────── Crear ────────────── */
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const nombre = inputNombre.value.trim();
    if (!nombre) return;

    const btn = form.querySelector('.btn-primary');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner-small"></div>';
    btn.disabled = true;

    authFetch("/api/categorias/crear/", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al crear');
        return res.json();
      })
      .then(() => {
        inputNombre.value = "";
        showToast("✅ Categoría creada correctamente", "success");
        cargarCategorias();
      })
      .catch((err) => {
        console.error("Error creando categoría:", err);
        showToast("Error al crear categoría", "error");
      })
      .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
  });

  /* ─────────── Modal de edición ─────────── */
  window.abrirModalEditar = (id, nombre) => {
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-nombre').value = nombre;
    document.getElementById('edit-modal').classList.add('open');
    document.body.style.overflow = 'hidden';
    
    setTimeout(() => {
      document.getElementById('edit-nombre').focus();
    }, 100);
  };

  window.cerrarModal = () => {
    document.getElementById('edit-modal').classList.remove('open');
    document.body.style.overflow = '';
  };

  // Cerrar con ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') cerrarModal();
  });

  // Cerrar al hacer clic fuera
  document.getElementById('edit-modal').addEventListener('click', (e) => {
    if (e.target.id === 'edit-modal') cerrarModal();
  });

  /* ─────────── Guardar edición ─────────── */
  editForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const id = document.getElementById('edit-id').value;
    const nombre = document.getElementById('edit-nombre').value.trim();
    
    if (!nombre) return;

    const btn = editForm.querySelector('.btn-submit');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner-small"></div> Guardando...';
    btn.disabled = true;

    authFetch(`/api/categorias/actualizar/${id}/`, {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al actualizar');
        return res.json();
      })
      .then(() => {
        cerrarModal();
        showToast("✅ Categoría actualizada correctamente", "success");
        cargarCategorias();
      })
      .catch((err) => {
        console.error("Error actualizando categoría:", err);
        showToast("Error al actualizar categoría", "error");
      })
      .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
  });

  /* ─────────── Eliminar ─────────── */
  window.eliminarCategoria = (id, nombre) => {
    if (!confirm(`¿Estás seguro de eliminar la categoría "${nombre}"?`)) return;
    
    authFetch(`/api/categorias/eliminar/${id}/`, {
      method: "DELETE",
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al eliminar');
        showToast("✅ Categoría eliminada correctamente", "success");
        cargarCategorias();
      })
      .catch((err) => {
        console.error("Error eliminando categoría:", err);
        showToast("Error al eliminar categoría", "error");
      });
  };

  /* ─────────── Toast ─────────── */
  function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3000);
  }

  /* ─────────── Inicial ──────────── */
  cargarCategorias();
});
