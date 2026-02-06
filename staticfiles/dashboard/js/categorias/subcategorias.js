document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("subcategorias-grid");
  const form = document.getElementById("form-subcategoria");
  const inputNombre = document.getElementById("nombre-subcategoria");
  const selectCategoria = document.getElementById("categoria-select");
  const inputImagen = document.getElementById("imagen-subcategoria");
  const editForm = document.getElementById("edit-form");
  const editImagen = document.getElementById("edit-imagen");

  /* ─────────── Preview de imágenes ─────────── */
  if (inputImagen) {
    inputImagen.addEventListener("change", (e) => {
      const file = e.target.files[0];
      const previewContainer = document.getElementById("preview-subcategoria");
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          document.getElementById("preview-img-subcategoria").src = event.target.result;
          previewContainer.style.display = "flex";
        };
        reader.readAsDataURL(file);
      }
    });
  }

  if (editImagen) {
    editImagen.addEventListener("change", (e) => {
      const file = e.target.files[0];
      const previewContainer = document.getElementById("preview-edit-sub");
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          document.getElementById("preview-img-edit-sub").src = event.target.result;
          previewContainer.style.display = "flex";
        };
        reader.readAsDataURL(file);
      }
    });
  }

  /* ─────────── Cargar Categorías ─────────── */
  function cargarCategorias() {
    authFetch("/api/categorias/")
      .then((res) => res.json())
      .then((categorias) => {
        // Llenar select de crear
        selectCategoria.innerHTML = '<option value="">Seleccionar categoría...</option>';
        categorias.forEach((cat) => {
          const option = document.createElement("option");
          option.value = cat.id;
          option.textContent = cat.nombre;
          selectCategoria.appendChild(option);
        });

        // Llenar select de editar
        const editSelect = document.getElementById('edit-categoria');
        editSelect.innerHTML = '<option value="">Seleccionar categoría...</option>';
        categorias.forEach((cat) => {
          const option = document.createElement("option");
          option.value = cat.id;
          option.textContent = cat.nombre;
          editSelect.appendChild(option);
        });

        cargarSubcategorias();
      })
      .catch((err) => {
        console.error("Error cargando categorías:", err);
        showToast("Error al cargar categorías", "error");
      });
  }

  /* ─────────── Estados de vista ─────────── */
  function mostrarEstado(estado) {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('subcategorias-grid').style.display = 'none';
    document.getElementById('empty-state').style.display = 'none';

    switch (estado) {
      case 'loading':
        document.getElementById('loading-state').style.display = 'flex';
        break;
      case 'grid':
        document.getElementById('subcategorias-grid').style.display = 'grid';
        break;
      case 'empty':
        document.getElementById('empty-state').style.display = 'block';
        break;
    }
  }

  /* ─────────── Render grid ─────────── */
  function cargarSubcategorias() {
    mostrarEstado('loading');

    authFetch("/api/subcategorias/")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((subcategorias) => {
        if (!subcategorias) return;
        
        // Actualizar estadística
        document.getElementById('stat-total').textContent = subcategorias.length;

        if (subcategorias.length === 0) {
          mostrarEstado('empty');
          return;
        }

        grid.innerHTML = "";
        subcategorias.forEach((subcat) => {
          const card = document.createElement("div");
          card.className = "categoria-card";
          card.innerHTML = `
            <div class="categoria-icon">
              ${subcat.imagen ? `<img src="${subcat.imagen}" alt="${subcat.nombre}" style="width: 100%; height: 100%; object-fit: cover;">` : `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                </svg>
              `}
            </div>
            <div class="categoria-info">
              <span class="categoria-id">${subcat.categoria_nombre}</span>
              <h3 class="categoria-nombre">${subcat.nombre}</h3>
            </div>
            <div class="categoria-actions">
              <button class="btn-icon edit" onclick="abrirModalEditar(${subcat.id}, '${subcat.nombre.replace(/'/g, "\\'")}', ${subcat.categoria_id}, '${subcat.imagen ? subcat.imagen : ''}')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button class="btn-icon delete" onclick="eliminarSubcategoria(${subcat.id}, '${subcat.nombre.replace(/'/g, "\\'")}')">
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
        console.error("Error cargando subcategorías:", err);
        showToast("Error al cargar subcategorías", "error");
      });
  }

  /* ─────────── Crear ────────────── */
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const categoriaId = selectCategoria.value;
    const nombre = inputNombre.value.trim();
    
    if (!categoriaId) {
      showToast("Selecciona una categoría", "error");
      return;
    }
    if (!nombre) return;

    const btn = form.querySelector('.btn-primary');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner-small"></div>';
    btn.disabled = true;

    // Usar FormData para enviar archivo
    const formData = new FormData();
    formData.append('nombre', nombre);
    formData.append('categoria_id', categoriaId);
    
    const imagenInput = document.getElementById('imagen-subcategoria');
    if (imagenInput && imagenInput.files.length > 0) {
      formData.append('imagen', imagenInput.files[0]);
    }

    authFetch("/api/subcategorias/crear/", {
      method: "POST",
      body: formData,
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al crear');
        return res.json();
      })
      .then(() => {
        selectCategoria.value = "";
        inputNombre.value = "";
        document.getElementById('imagen-subcategoria').value = "";
        showToast("✅ Subcategoría creada correctamente", "success");
        cargarSubcategorias();
      })
      .catch((err) => {
        console.error("Error creando subcategoría:", err);
        showToast("Error al crear subcategoría", "error");
      })
      .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
  });

  /* ─────────── Modal de edición ─────────── */
  window.abrirModalEditar = (id, nombre, categoriaId, imagen) => {
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-nombre').value = nombre;
    document.getElementById('edit-categoria').value = categoriaId;
    
    const infoEl = document.getElementById('edit-imagen-info');
    const previewContainer = document.getElementById("preview-edit-sub");
    
    if (imagen) {
      infoEl.style.display = 'block';
      // Mostrar imagen actual
      document.getElementById("preview-img-edit-sub").src = imagen;
      previewContainer.style.display = "flex";
    } else {
      infoEl.style.display = 'none';
      previewContainer.style.display = "none";
    }
    
    // Limpiar el input de archivo
    document.getElementById('edit-imagen').value = '';
    
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

    // Usar FormData para enviar archivo
    const formData = new FormData();
    formData.append('nombre', nombre);
    
    const imagenInput = document.getElementById('edit-imagen');
    if (imagenInput && imagenInput.files.length > 0) {
      formData.append('imagen', imagenInput.files[0]);
    }

    authFetch(`/api/subcategorias/actualizar/${id}/`, {
      method: "PATCH",
      body: formData,
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al actualizar');
        return res.json();
      })
      .then(() => {
        cerrarModal();
        showToast("✅ Subcategoría actualizada correctamente", "success");
        cargarSubcategorias();
      })
      .catch((err) => {
        console.error("Error actualizando subcategoría:", err);
        showToast("Error al actualizar subcategoría", "error");
      })
      .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
  });

  /* ─────────── Eliminar ─────────── */
  window.eliminarSubcategoria = (id, nombre) => {
    if (!confirm(`¿Estás seguro de eliminar la subcategoría "${nombre}"?`)) return;
    
    authFetch(`/api/subcategorias/eliminar/${id}/`, {
      method: "DELETE",
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al eliminar');
        showToast("✅ Subcategoría eliminada correctamente", "success");
        cargarSubcategorias();
      })
      .catch((err) => {
        console.error("Error eliminando subcategoría:", err);
        showToast("Error al eliminar subcategoría", "error");
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
