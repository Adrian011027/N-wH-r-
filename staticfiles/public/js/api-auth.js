// ========================================
// API de Autenticación JWT
// ========================================

const API_URL = 'http://localhost:8000/api';

// ========================================
// Gestión de Tokens
// ========================================

/**
 * Guardar tokens en localStorage
 */
export const saveTokens = (accessToken, refreshToken) => {
    localStorage.setItem('access', accessToken);
    localStorage.setItem('refresh', refreshToken);
};

/**
 * Obtener access token
 */
export const getAccessToken = () => {
    return localStorage.getItem('access');
};

/**
 * Obtener refresh token
 */
export const getRefreshToken = () => {
    return localStorage.getItem('refresh');
};

/**
 * Guardar información del usuario
 */
export const saveUser = (user) => {
    localStorage.setItem('user', JSON.stringify(user));
};

/**
 * Obtener información del usuario
 */
export const getUser = () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
};

/**
 * Eliminar todos los datos de autenticación
 */
export const clearAuth = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
};

// ========================================
// Funciones de Autenticación
// ========================================

/**
 * Login de usuario
 * @param {string} username - Nombre de usuario
 * @param {string} password - Contraseña
 * @returns {Promise<Object>} - Datos del usuario y tokens
 */
export const login = async (username, password) => {
    try {
        const response = await fetch(`/auth/login_client/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error al iniciar sesión');
        }

        // Guardar tokens
        saveTokens(data.access, data.refresh);
        
        // Guardar info de usuario si viene en la respuesta
        if (data.username) {
            localStorage.setItem('username', data.username);
        }

        return data;
    } catch (error) {
        console.error('Error en login:', error);
        throw error;
    }
};

/**
 * Renovar access token usando refresh token
 * @returns {Promise<string>} - Nuevo access token
 */
export const refreshAccessToken = async () => {
    try {
        const refreshToken = getRefreshToken();

        if (!refreshToken) {
            throw new Error('No hay refresh token disponible');
        }

        const response = await fetch(`/api/auth/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error al renovar token');
        }

        // Guardar nuevo access token
        localStorage.setItem('access', data.access);
        return data.access;
    } catch (error) {
        console.error('Error al renovar token:', error);
        // Si falla el refresh, limpiar todo y redirigir al login
        clearAuth();
        window.location.href = '/';
        throw error;
    }
};

/**
 * Verificar si el token es válido
 * @returns {Promise<Object>} - Información del usuario si el token es válido
 */
export const verifyToken = async () => {
    try {
        const token = getAccessToken();

        if (!token) {
            throw new Error('No hay token disponible');
        }

        const response = await fetch(`/api/auth/verify/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Token inválido');
        }

        return data;
    } catch (error) {
        console.error('Error al verificar token:', error);
        throw error;
    }
};

/**
 * Cerrar sesión
 */
export const logout = async () => {
    try {
        const refreshToken = getRefreshToken();

        if (refreshToken) {
            await fetch(`/api/auth/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
            });
        }
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
    } finally {
        // Siempre limpiar los datos locales
        clearAuth();
        window.location.href = '/';
    }
};

// ========================================
// Interceptor para peticiones con JWT
// ========================================

/**
 * Realizar petición con autenticación JWT
 * Incluye renovación automática de token si expira
 * 
 * @param {string} url - URL de la petición
 * @param {Object} options - Opciones de fetch
 * @returns {Promise<Response>} - Respuesta de la petición
 */
export const fetchWithAuth = async (url, options = {}) => {
    let token = getAccessToken();

    // Si no hay token, redirigir al login
    if (!token) {
        window.location.href = '/login';
        throw new Error('No autenticado');
    }

    // Agregar headers de autenticación
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    // Realizar petición
    let response = await fetch(url, options);

    // Si el token expiró (401), intentar renovarlo
    if (response.status === 401) {
        try {
            // Intentar renovar el token
            token = await refreshAccessToken();

            // Reintentar la petición con el nuevo token
            options.headers['Authorization'] = `Bearer ${token}`;
            response = await fetch(url, options);
        } catch (error) {
            // Si falla la renovación, redirigir al login
            clearAuth();
            window.location.href = '/login';
            throw error;
        }
    }

    return response;
};

// ========================================
// Funciones de API con autenticación
// ========================================

/**
 * Obtener lista de usuarios (solo admin)
 */
export const getUsers = async () => {
    const response = await fetchWithAuth(`${API_URL}/users/`);
    
    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Error al obtener usuarios');
    }
    
    return response.json();
};

/**
 * Crear nuevo usuario (solo admin)
 */
export const createUser = async (userData) => {
    const response = await fetchWithAuth(`${API_URL}/users/create/`, {
        method: 'POST',
        body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Error al crear usuario');
    }
    
    return response.json();
};

/**
 * Actualizar usuario (solo admin)
 */
export const updateUser = async (id, userData) => {
    const response = await fetchWithAuth(`${API_URL}/users/update/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Error al actualizar usuario');
    }
    
    return response.json();
};

/**
 * Eliminar usuario (solo admin)
 */
export const deleteUser = async (id) => {
    const response = await fetchWithAuth(`${API_URL}/users/delete/${id}/`, {
        method: 'DELETE',
    });
    
    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Error al eliminar usuario');
    }
    
    return response.json();
};

// ========================================
// Helpers
// ========================================

/**
 * Verificar si el usuario está autenticado
 */
export const isAuthenticated = () => {
    return !!getAccessToken();
};

/**
 * Verificar si el usuario es admin
 */
export const isAdmin = () => {
    const user = getUser();
    return user && user.role === 'admin';
};

/**
 * Obtener el rol del usuario actual
 */
export const getUserRole = () => {
    const user = getUser();
    return user ? user.role : null;
};

// ========================================
// Exportación por defecto
// ========================================
export default {
    login,
    logout,
    refreshAccessToken,
    verifyToken,
    fetchWithAuth,
    getUsers,
    createUser,
    updateUser,
    deleteUser,
    isAuthenticated,
    isAdmin,
    getUserRole,
    getUser,
    saveTokens,
    clearAuth,
};
