/**
 * auth-helper.js (Inventario)
 * Sistema de autenticación JWT para el módulo de inventario.
 * Usa prefijo 'inv_' en localStorage para no colisionar con el dashboard admin.
 */

function getInvTokens() {
  return {
    access: localStorage.getItem('inv_access'),
    refresh: localStorage.getItem('inv_refresh')
  };
}

function saveInvTokens(access, refresh) {
  if (access) localStorage.setItem('inv_access', access);
  if (refresh) localStorage.setItem('inv_refresh', refresh);
}

function invLogout(redirect = true) {
  localStorage.removeItem('inv_access');
  localStorage.removeItem('inv_refresh');
  localStorage.removeItem('inv_username');
  localStorage.removeItem('inv_user_id');
  localStorage.removeItem('inv_role');
  if (redirect) {
    window.location.href = '/inventario/login/';
  }
}

function isInvAuthenticated() {
  const { access, refresh } = getInvTokens();
  return !!(access && refresh);
}

async function refreshInvToken() {
  const { refresh } = getInvTokens();
  if (!refresh) throw new Error('No hay refresh token');

  try {
    const res = await fetch('/api/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    });
    if (!res.ok) throw new Error('Refresh inválido');
    const data = await res.json();
    saveInvTokens(data.access, null);
    return data.access;
  } catch (err) {
    invLogout();
    throw err;
  }
}

function getCookie(name) {
  let v = null;
  if (document.cookie) {
    document.cookie.split(';').forEach(c => {
      c = c.trim();
      if (c.startsWith(name + '=')) {
        v = decodeURIComponent(c.substring(name.length + 1));
      }
    });
  }
  return v;
}

async function invFetch(url, options = {}) {
  if (!isInvAuthenticated()) { invLogout(); throw new Error('No autenticado'); }

  const { access } = getInvTokens();
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${access}`,
    'X-CSRFToken': getCookie('csrftoken') || ''
  };
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    try {
      const newToken = await refreshInvToken();
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, { ...options, headers });
    } catch (e) {
      invLogout();
      throw new Error('Sesión expirada');
    }
  }
  return response;
}

async function invFetchJSON(url, options = {}) {
  const response = await invFetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || data.message || 'Error');
  return data;
}

// Verificar auth al cargar (no en login)
document.addEventListener('DOMContentLoaded', () => {
  if (!window.location.pathname.includes('/login/') && !isInvAuthenticated()) {
    invLogout();
  }
});

window.invAuth = { getInvTokens, saveInvTokens, invLogout, isInvAuthenticated, invFetch, invFetchJSON };
