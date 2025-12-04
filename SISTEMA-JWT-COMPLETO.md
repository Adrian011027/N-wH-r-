# 🔐 Sistema JWT Completo - NöwHėrē Dashboard

## ✅ Sistema Implementado

### 1. Backend (Django)

#### Configuración JWT
- **Access Token**: 30 minutos de duración
- **Refresh Token**: 7 días de duración
- **Algoritmo**: HS256
- **Secret Key**: Configurado en `settings.SECRET_KEY`

#### Endpoints de Autenticación

```python
# Login (Usuarios Dashboard)
POST /auth/login_user/
Body: { "username": "admin", "password": "admin123" }
Response: {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_id": 1,
    "username": "admin",
    "role": "admin"
}

# Refresh Token (Renovar Access)
POST /api/auth/refresh/
Body: { "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..." }
Response: {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Decoradores de Protección

```python
# store/views/decorators.py

@admin_required()  # Solo usuarios de dashboard (Usuario model)
@cliente_required()  # Solo clientes (Cliente model)
```

#### Archivos Clave Backend

- `store/utils/jwt_helpers.py`: Generación y validación de tokens
- `store/views/decorators.py`: Decoradores de autenticación
- `store/views/views.py`: Endpoints de login y refresh

---

### 2. Frontend (JavaScript)

#### Helper Centralizado: `auth-helper.js`

Ubicación: `static/dashboard/js/auth-helper.js`

Este archivo proporciona:

```javascript
// 1. Funciones de gestión de tokens
window.authHelper = {
    getTokens(),        // Obtiene access y refresh del localStorage
    saveTokens(access, refresh),  // Guarda tokens
    logout(redirect),   // Limpia tokens y redirige
    isAuthenticated(),  // Verifica si hay sesión activa
    
    // 2. Fetch con auto-refresh
    authFetch(url, options),     // fetch() con JWT automático
    authFetchJSON(url, options), // authFetch + retorna JSON
    
    // 3. Refresh automático
    refreshAccessToken()  // Renueva el access token
};
```

#### Flujo de Autenticación Automática

```javascript
// 1. El usuario hace una petición
const response = await authFetch('/api/productos/', {
    method: 'POST',
    body: formData
});

// 2. authFetch automáticamente:
//    - Agrega header: Authorization: Bearer <access_token>
//    - Si recibe 401:
//      a) Llama a /api/auth/refresh/ con refresh token
//      b) Guarda nuevo access token
//      c) Reintenta la petición original
//    - Si refresh falla:
//      a) Hace logout
//      b) Redirige a /dashboard/login/

// 3. Sin más configuración necesaria ✨
```

#### Uso en Archivos JavaScript

**Antes (Manual):**
```javascript
const token = localStorage.getItem('access');
if (!token) {
    window.location.href = '/dashboard/login/';
    return;
}

const response = await fetch('/api/productos/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

if (response.status === 401) {
    // Manejar token expirado manualmente...
    window.location.href = '/dashboard/login/';
}
```

**Ahora (Automático):**
```javascript
// ¡Eso es todo! authFetch maneja todo automáticamente
const response = await authFetch('/api/productos/');
const data = await response.json();

// O más simple:
const data = await authFetchJSON('/api/productos/');
```

---

### 3. Archivos Actualizados

#### Plantilla Base
- `templates/dashboard/base.html`: Incluye `auth-helper.js` globalmente

#### JavaScript Dashboard
Todos usan `authFetch()` y `authFetchJSON()`:

✅ `static/dashboard/js/productos/registro.js`
✅ `static/dashboard/js/productos/lista.js`
✅ `static/dashboard/js/productos/editar.js`
✅ `static/dashboard/js/categorias/categorias.js`
✅ `static/dashboard/js/ordenes/lista.js`

---

## 🔧 Cómo Funciona

### Flujo Completo

```
1. Usuario inicia sesión
   └─> POST /auth/login_user/
       └─> Backend retorna: { access, refresh }
           └─> Frontend guarda en localStorage

2. Usuario crea un producto
   └─> authFetch('/api/productos/crear/', { method: 'POST', body: formData })
       └─> authFetch agrega: Authorization: Bearer <access>
           └─> Backend valida con @admin_required()
               ├─> ✅ Token válido: Crea producto
               └─> ❌ Token expirado: 401 Unauthorized
                   └─> authFetch detecta 401
                       └─> POST /api/auth/refresh/ { refresh }
                           ├─> ✅ Refresh válido: Nuevo access
                           │   └─> Reintenta crear producto
                           └─> ❌ Refresh expirado: Logout
```

---

## 🐛 Problema Resuelto

### Antes
- **Error**: 401 Unauthorized al crear productos
- **Causa**: Frontend no enviaba header `Authorization`
- **Síntoma**: Categorías funcionaban, productos no

### Después
- **Solución**: `authFetch()` agrega automáticamente el header
- **Extra**: Auto-refresh cuando token expira (cada 30 minutos)
- **Resultado**: Sistema totalmente funcional con refresh automático

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Cargar datos (GET)
```javascript
// Simple
const productos = await authFetchJSON('/api/productos/');

// Con manejo de errores
try {
    const productos = await authFetchJSON('/api/productos/');
    console.log(productos);
} catch (error) {
    console.error('Error:', error.message);
}
```

### Ejemplo 2: Crear datos (POST JSON)
```javascript
const nuevaCategoria = await authFetchJSON('/api/categorias/crear/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre: 'Ropa de Invierno' })
});
```

### Ejemplo 3: Subir archivo (POST FormData)
```javascript
const formData = new FormData();
formData.append('nombre', 'Zapatilla Nike');
formData.append('imagen', fileInput.files[0]);

const response = await authFetch('/api/productos/crear/', {
    method: 'POST',
    body: formData
    // NO agregar Content-Type, FormData lo maneja automáticamente
});

const producto = await response.json();
```

### Ejemplo 4: Actualizar (PUT)
```javascript
await authFetch(`/api/ordenes/${ordenId}/estado/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'enviado' })
});
```

### Ejemplo 5: Eliminar (DELETE)
```javascript
const response = await authFetch(`/api/productos/delete/${id}/`, {
    method: 'DELETE'
});

if (response.ok) {
    console.log('Producto eliminado');
}
```

---

## 🔐 Seguridad

### Tokens Almacenados
```javascript
localStorage.setItem('access', '...')   // 30 minutos
localStorage.setItem('refresh', '...')  // 7 días
```

### Protección Backend
Todos los endpoints del dashboard requieren:
```python
@csrf_exempt
@admin_required()
def create_product(request):
    # Solo accesible con JWT válido de Usuario (admin)
    ...
```

### Auto-logout
- Si el refresh token expira (7 días), se hace logout automático
- Si el usuario cierra sesión, se limpian todos los tokens
- Protección contra tokens inválidos o manipulados

---

## 🚀 Próximos Pasos Opcionales

### 1. Indicador Visual de Sesión
```javascript
// Agregar en header.html
function mostrarTiempoRestante() {
    const token = localStorage.getItem('access');
    if (!token) return;
    
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expira = new Date(payload.exp * 1000);
    const ahora = new Date();
    const minutos = Math.floor((expira - ahora) / 60000);
    
    console.log(`Sesión expira en ${minutos} minutos`);
}
```

### 2. Renovación Proactiva
```javascript
// Renovar automáticamente a los 25 minutos (antes de expirar)
setInterval(async () => {
    try {
        await authHelper.refreshAccessToken();
        console.log('Token renovado automáticamente');
    } catch (e) {
        console.log('No se pudo renovar:', e);
    }
}, 25 * 60 * 1000); // 25 minutos
```

### 3. Remember Me
```javascript
// En login.html, si checkbox "Recordarme" está marcado:
if (rememberMe) {
    // Guardar en localStorage (persistente)
    localStorage.setItem('refresh', data.refresh);
} else {
    // Guardar en sessionStorage (cierra al cerrar navegador)
    sessionStorage.setItem('refresh', data.refresh);
}
```

---

## 📊 Resumen Técnico

| Característica | Estado | Ubicación |
|---|---|---|
| Access Token (30 min) | ✅ | `jwt_helpers.py` |
| Refresh Token (7 días) | ✅ | `jwt_helpers.py` |
| Endpoint Refresh | ✅ | `/api/auth/refresh/` |
| Auto-refresh Frontend | ✅ | `auth-helper.js` |
| Protección Endpoints | ✅ | `@admin_required()` |
| Productos Dashboard | ✅ | `registro.js`, `lista.js`, `editar.js` |
| Categorías Dashboard | ✅ | `categorias.js` |
| Órdenes Dashboard | ✅ | `ordenes/lista.js` |
| Login Dashboard | ✅ | `templates/dashboard/auth/login.html` |

---

## 🎯 Estado Final

✅ **Sistema JWT 100% Funcional**
- Autenticación completa
- Auto-refresh automático
- Protección de endpoints
- Manejo de errores
- Logout automático

**Listo para producción** 🚀
