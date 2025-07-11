document.addEventListener("DOMContentLoaded", () => {
  const tabla       = document.querySelector("#tabla-categorias tbody");
  const form        = document.getElementById("form-categoria");
  const inputNombre = document.getElementById("nombre-categoria");

  /* ─────────── Helpers ─────────── */
  const getCookie = (name) => {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : null;
  };
  const CSRF = { "X-CSRFToken": getCookie("csrftoken") };

  /* ─────────── Render tabla ─────── */
  function cargarCategorias() {
    fetch("/api/categorias/")
      .then((res) => res.json())
      .then((categorias) => {
        tabla.innerHTML = "";
        categorias.forEach((cat) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${cat.id}</td>
            <td>${cat.nombre}</td>
            <td>
              <button onclick="editarCategoria(${cat.id}, '${cat.nombre.replace(/'/g, "\\'")}')">Editar</button>
              <button onclick="eliminarCategoria(${cat.id})">Eliminar</button>
            </td>`;
          tabla.appendChild(tr);
        });
      })
      .catch((err) => console.error("Error cargando categorías:", err));
  }

  /* ─────────── Crear ────────────── */
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const nombre = inputNombre.value.trim();
    if (!nombre) return;
    fetch("/api/categorias/crear/", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...CSRF },
      body: JSON.stringify({ nombre }),
    })
      .then((res) => res.ok && cargarCategorias())
      .then(() => (inputNombre.value = ""))
      .catch((err) => console.error("Error creando categoría:", err));
  });

  /* ─────────── Editar ───────────── */
  window.editarCategoria = (id, actual) => {
    const nuevo = prompt("Nuevo nombre:", actual);
    if (!nuevo || nuevo.trim() === "" || nuevo === actual) return;
    fetch(`/api/categorias/actualizar/${id}/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...CSRF },
      body: JSON.stringify({ nombre: nuevo.trim() }),
    })
      .then((res) => res.ok && cargarCategorias())
      .catch((err) => console.error("Error actualizando categoría:", err));
  };

  /* ─────────── Eliminar ─────────── */
  window.eliminarCategoria = (id) => {
    if (!confirm("¿Eliminar la categoría?")) return;
    fetch(`/api/categorias/eliminar/${id}/`, {
      method: "DELETE",
      headers: CSRF,
    })
      .then((res) => res.ok && cargarCategorias())
      .catch((err) => console.error("Error eliminando categoría:", err));
  };

  /* ─────────── Inicial ──────────── */
  cargarCategorias();
});
