document.addEventListener("DOMContentLoaded", () => {
    const tabla = document.querySelector("#tabla-categorias tbody");
    const form = document.getElementById("form-categoria");
    const inputNombre = document.getElementById("nombre-categoria");

    function cargarCategorias() {
        fetch("/get_categorias/")
            .then(res => res.json())
            .then(categorias => {
                tabla.innerHTML = "";
                categorias.forEach(cat => {
                    const fila = document.createElement("tr");
                    fila.innerHTML = `
                        <td>${cat.id}</td>
                        <td>${cat.nombre}</td>
                        <td>
                            <button onclick="eliminarCategoria(${cat.id})">Eliminar</button>
                        </td>`;
                    tabla.appendChild(fila);
                });
            });
    }

    form.addEventListener("submit", e => {
        e.preventDefault();
        fetch("/create_categoria/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre: inputNombre.value })
        }).then(res => {
            if (res.ok) {
                inputNombre.value = "";
                cargarCategorias();
            }
        });
    });

    window.eliminarCategoria = (id) => {
        fetch(`/delete_categoria/${id}/`, {
            method: "DELETE"
        }).then(res => {
            if (res.ok) cargarCategorias();
        });
    };

    cargarCategorias();
});
