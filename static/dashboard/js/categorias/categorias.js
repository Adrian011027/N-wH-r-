document.addEventListener("DOMContentLoaded", () => {
  const tabla       = document.querySelector("#tabla-categorias tbody");
  const form        = document.getElementById("form-categoria");
  const inputNombre = document.getElementById("nombre-categoria");

  /* ─────────── Helpers JWT ─────────── */
  function getAccessToken() {
    return localStorage.getItem("access");
  }

  function getAuthHeaders() {
    const token = getAccessToken();
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    };
  }

  /* ─────────── Render tabla ─────────── */
  function cargarCategorias() {
    const token = getAccessToken();
    if (!token) {
      console.error("No hay token de acceso. Redirigiendo al login...");
      window.location.href = "/dashboard/login/";
      return;
    }

    fetch("/api/categorias/", {
      headers: getAuthHeaders()
    })
      .then((res) => {
        if (res.status === 401 || res.status === 403) {
          console.error("Token inválido o expirado. Redirigiendo al login...");
          localStorage.clear();
          window.location.href = "/dashboard/login/";
          return;
        }
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((categorias) => {
        if (!categorias) return; // Si redirigió, no continuar
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
      .catch((err) => {
        console.error("Error cargando categorías:", err);
        alert("Error al cargar categorías. Por favor, recarga la página.");
      });
  }

  /* ─────────── Crear ────────────── */
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const nombre = inputNombre.value.trim();
    if (!nombre) return;
    fetch("/api/categorias/crear/", {
      method: "POST",
      headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
    })
      .then((res) => res.ok && cargarCategorias())
      .catch((err) => console.error("Error eliminando categoría:", err));
  };

  /* ─────────── Inicial ──────────── */
  cargarCategorias();
});
