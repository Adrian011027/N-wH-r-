/**
 * auth-helper.js
 * Sistema centralizado de autenticación JWT con auto-refresh
 */

// Obtener tokens del localStorage
function getTokens() {
  return {
    access: localStorage.getItem('access'),
    refresh: localStorage.getItem('refresh')
  };
}

// Guardar tokens en localStorage
function saveTokens(access, refresh) {
  if (access) localStorage.setItem('access', access);
  if (refresh) localStorage.setItem('refresh', refresh);
}

// Limpiar tokens y redirigir a login
function logout(redirect = true) {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
  localStorage.removeItem('username');
  sessionStorage.clear();
  
  if (redirect) {
    window.location.href = '/dashboard/login/';
  }
}

// Verificar si el usuario está autenticado
function isAuthenticated() {
  const { access, refresh } = getTokens();
  return !!(access && refresh);
}

// Refrescar el access token usando el refresh token
async function refreshAccessToken() {
  const { refresh } = getTokens();
  
  if (!refresh) {
    throw new Error('No hay refresh token disponible');
  }
  
  try {
    const res = await fetch('/api/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    });
    
    if (!res.ok) {
      throw new Error('Refresh token inválido o expirado');
    }
    
    const data = await res.json();
    saveTokens(data.access, null); // Solo actualizar access token
    return data.access;
  } catch (err) {
    console.error('Error al refrescar token:', err);
    logout();
    throw err;
  }
}

/**
 * Fetch wrapper con autenticación JWT y auto-refresh
 * 
 * @param {string} url - URL del endpoint
 * @param {object} options - Opciones de fetch (method, body, headers, etc.)
 * @returns {Promise<Response>}
 */
async function authFetch(url, options = {}) {
  // Verificar autenticación
  if (!isAuthenticated()) {
    logout();
    throw new Error('No autenticado');
  }
  
  // Obtener token CSRF de la cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  
  // Preparar headers con Authorization JWT y CSRF
  const { access } = getTokens();
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${access}`,
    'X-CSRFToken': getCookie('csrftoken') || ''  // Agregar CSRF token
  };
  
  // Si no es FormData, agregar Content-Type
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  
  // Primera petición
  let response = await fetch(url, {
    ...options,
    headers
  });
  
  // Si es 401, intentar refresh y reintentar
  if (response.status === 401) {
    try {
      const newAccessToken = await refreshAccessToken();
      
      // Reintentar con nuevo token
      headers['Authorization'] = `Bearer ${newAccessToken}`;
      response = await fetch(url, {
        ...options,
        headers
      });
    } catch (refreshError) {
      // Si el refresh falla, hacer logout
      logout();
      throw new Error('Sesión expirada. Por favor inicia sesión nuevamente.');
    }
  }
  
  return response;
}

/**
 * authFetch que retorna JSON directamente
 * Lanza error si la respuesta no es OK
 */
async function authFetchJSON(url, options = {}) {
  const response = await authFetch(url, options);
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.error || data.message || 'Error en la petición');
  }
  
  return data;
}

// Verificar autenticación al cargar la página
document.addEventListener('DOMContentLoaded', () => {
  // Solo verificar en páginas del dashboard (no en login)
  if (!window.location.pathname.includes('/login/') && !isAuthenticated()) {
    logout();
  }
});

// Exportar funciones para uso global
window.authHelper = {
  getTokens,
  saveTokens,
  logout,
  isAuthenticated,
  refreshAccessToken,
  authFetch,
  authFetchJSON
};
