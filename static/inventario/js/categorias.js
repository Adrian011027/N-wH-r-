/**
 * categorias.js - Lógica para gestión de categorías y subcategorías
 * Reutiliza los endpoints existentes:
 * - POST /api/categorias/crear/
 * - DELETE /api/categorias/eliminar/<id>/
 * - POST /api/subcategorias/crear/
 * - DELETE /api/subcategorias/eliminar/<id>/
 */

document.addEventListener('DOMContentLoaded', () => {
  const formCat = document.getElementById('formCategoria');
  const formSubcat = document.getElementById('formSubcategoria');

  if (formCat) {
    formCat.addEventListener('submit', async (e) => {
      e.preventDefault();
      await crearCategoria();
    });
  }

  if (formSubcat) {
    formSubcat.addEventListener('submit', async (e) => {
      e.preventDefault();
      await crearSubcategoria();
    });
  }
});

async function crearCategoria() {
  const nombre = document.getElementById('catNombre').value.trim();
  const imagenInput = document.getElementById('catImagen');

  if (!nombre) { showToast('El nombre es obligatorio', 'error'); return; }

  const formData = new FormData();
  formData.append('nombre', nombre);
  if (imagenInput.files.length > 0) {
    formData.append('imagen', imagenInput.files[0]);
  }

  try {
    const res = await fetch('/api/categorias/crear/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      },
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al crear categoría');

    showToast('Categoría creada');
    setTimeout(() => location.reload(), 800);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function crearSubcategoria() {
  const categoriaId = document.getElementById('subCatCategoria').value;
  const nombre = document.getElementById('subCatNombre').value.trim();
  const descripcion = document.getElementById('subCatDescripcion').value.trim();

  if (!categoriaId || !nombre) {
    showToast('Categoría padre y nombre son obligatorios', 'error');
    return;
  }

  try {
    const res = await fetch('/api/subcategorias/crear/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      },
      body: JSON.stringify({
        categoria_id: parseInt(categoriaId),
        nombre,
        descripcion
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al crear subcategoría');

    showToast('Subcategoría creada');
    setTimeout(() => location.reload(), 800);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function eliminarCategoria(id, nombre) {
  if (!confirm(`¿Eliminar la categoría "${nombre}"? Esto eliminará también sus subcategorías y productos asociados.`)) return;

  try {
    const res = await fetch(`/api/categorias/eliminar/${id}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al eliminar');

    showToast('Categoría eliminada');
    const card = document.querySelector(`[data-cat-id="${id}"]`);
    if (card) {
      card.style.transition = 'opacity 0.3s';
      card.style.opacity = '0';
      setTimeout(() => card.remove(), 300);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function eliminarSubcategoria(id, nombre) {
  if (!confirm(`¿Eliminar la subcategoría "${nombre}"?`)) return;

  try {
    const res = await fetch(`/api/subcategorias/eliminar/${id}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Authorization': `Bearer ${localStorage.getItem('inv_access')}`
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error al eliminar');

    showToast('Subcategoría eliminada');
    setTimeout(() => location.reload(), 800);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Utilidades
function showToast(message, type = 'success') {
  const existing = document.querySelector('.inv-toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = `inv-toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function getCsrf() {
  let v = null;
  if (document.cookie) {
    document.cookie.split(';').forEach(c => {
      c = c.trim();
      if (c.startsWith('csrftoken=')) {
        v = decodeURIComponent(c.substring(10));
      }
    });
  }
  return v || '';
}
