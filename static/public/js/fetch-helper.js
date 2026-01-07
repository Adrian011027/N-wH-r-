// ========================================
// Helper para agregar JWT a todas las peticiones
// ========================================

/**
 * Obtener el token de acceso desde localStorage
 */
function getAccessToken() {
    return localStorage.getItem('access');
}

/**
 * Obtener el refresh token desde localStorage
 */
function getRefreshToken() {
    return localStorage.getItem('refresh');
}

/**
 * Verificar si el usuario está autenticado
 */
function isAuthenticated() {
    return !!getAccessToken();
}

/**
 * Renovar el access token usando el refresh token
 */
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    
    if (!refreshToken) {
        console.error('❌ No hay refresh token disponible');
        return null;
    }

    try {
        console.log('🔄 Intentando renovar token...');
        const response = await fetch('/api/auth/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Error al renovar token. Status:', response.status);
            console.error('   Respuesta:', errorText);
            throw new Error(`Error ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log('✅ Token renovado exitosamente');
        localStorage.setItem('access', data.access);
        return data.access;
    } catch (error) {
        console.error('❌ Error crítico al renovar token:', error);
        // Si falla, limpiar tokens y redirigir
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        localStorage.removeItem('user_id');
        localStorage.removeItem('username');
        console.log('🔓 Sesión terminada. Por favor, inicia sesión nuevamente.');
        // Opcional: redirigir al login
        // window.location.href = '/login/';
        return null;
    }
}

/**
 * Fetch mejorado que agrega automáticamente el token JWT
 * y renueva el token si expira
 */
async function fetchWithAuth(url, options = {}) {
    let token = getAccessToken();

    // Preparar headers
    options.headers = {
        ...options.headers,
        'Content-Type': 'application/json',
    };

    // Agregar token si existe
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    // Realizar petición
    let response = await fetch(url, options);

    // Si el token expiró (401), intentar renovarlo
    if (response.status === 401 && token) {
        console.log('⏰ Token expirado (401), intentando renovar...');
        
        token = await refreshAccessToken();
        
        if (token) {
            console.log('✅ Reintentando petición con nuevo token...');
            // Reintentar con el nuevo token
            options.headers['Authorization'] = `Bearer ${token}`;
            response = await fetch(url, options);
        } else {
            console.error('❌ No se pudo obtener un nuevo token. Acceso denegado.');
        }
    }

    return response;
}

/**
 * Wrapper para GET con autenticación
 */
async function fetchGet(url) {
    return fetchWithAuth(url, { method: 'GET' });
}

/**
 * Wrapper para POST con autenticación
 */
async function fetchPost(url, data) {
    return fetchWithAuth(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * Wrapper para PUT con autenticación
 */
async function fetchPut(url, data) {
    return fetchWithAuth(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * Wrapper para PATCH con autenticación
 */
async function fetchPatch(url, data) {
    return fetchWithAuth(url, {
        method: 'PATCH',
        body: JSON.stringify(data)
    });
}

/**
 * Wrapper para DELETE con autenticación
 */
async function fetchDelete(url) {
    return fetchWithAuth(url, { method: 'DELETE' });
}

// Exportar funciones para uso global
window.fetchWithAuth = fetchWithAuth;
window.fetchGet = fetchGet;
window.fetchPost = fetchPost;
window.fetchPut = fetchPut;
window.fetchPatch = fetchPatch;
window.fetchDelete = fetchDelete;
window.isAuthenticated = isAuthenticated;
window.getAccessToken = getAccessToken;
