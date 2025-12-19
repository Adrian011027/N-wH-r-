/**
 * 🔐 Logout con JWT
 * Limpia tokens y cierra sesión en el backend
 */

async function logout() {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (refreshToken) {
      // Llamar al endpoint de logout para blacklistear el token
      await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(console.error);
    }
  } finally {
    // Limpiar tokens del localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('clienteId');
    
    // Limpiar wishlist si existe
    Object.keys(localStorage)
      .filter(key => key.startsWith('wishlist_'))
      .forEach(key => localStorage.removeItem(key));
    
    // Redirigir al inicio
    window.location.href = '/';
  }
}

// Exponer función globalmente
window.logout = logout;

// Agregar listener a botones de logout
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-logout]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (confirm('¿Cerrar sesión?')) {
        logout();
      }
    });
  });
});
