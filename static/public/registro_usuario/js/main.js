function getCSRFToken() {
  const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return el ? el.value : '';
}

document.addEventListener("DOMContentLoaded", () => {
  /* ----------  A. MOSTRAR / OCULTAR CONTRASEÑA  ---------- */
  const pwdInput  = document.getElementById('pwd');
  const toggleBtn = pwdInput?.nextElementSibling;      // tu <button>
  if (toggleBtn) {
    const icon = toggleBtn.querySelector('i');

    toggleBtn.addEventListener('click', () => {
      const oculto = pwdInput.type === 'password';
      pwdInput.type = oculto ? 'text' : 'password';

      // alterna SOLO estas dos clases, sin duplicar <i>
      icon.classList.toggle('fa-eye');
      icon.classList.toggle('fa-eye-slash');

      toggleBtn.setAttribute(
        'aria-label',
        oculto ? 'Ocultar contraseña' : 'Mostrar contraseña'
      );
    });
  }

  /* ----------  B. ENVÍO DEL FORMULARIO  ---------- */
  const form = document.getElementById('registroForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email     = form.email.value.trim().toLowerCase();
    const email2    = form.email2.value.trim().toLowerCase();
    const pwd       = form.pwd.value;
    const nombre    = form.nombre.value.trim();
    const telefono  = form.telefono.value.trim();
    const direccion = form.direccion.value.trim();

    if (!email || !email2 || !pwd) {
      alert('❌ Los campos de correo, confirmación y contraseña son obligatorios.');
      return;
    }
    if (email !== email2) {
      alert('❌ Los correos no coinciden.');
      return;
    }

    const datos = {
      username: email,
      password: pwd,
      correo  : email,
    };
    if (nombre)    datos.nombre    = nombre;
    if (telefono)  datos.telefono  = telefono;
    if (direccion) datos.direccion = direccion;

    try {
      const res = await fetch('/create-client/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken' : getCSRFToken(),
        },
        body: JSON.stringify(datos),
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        window.location.href = '/';
      } else {
        alert('❌ Error: ' + (data.error || res.status));
      }
    } catch (err) {
      alert('❌ Error inesperado: ' + err);
    }
  });
});
