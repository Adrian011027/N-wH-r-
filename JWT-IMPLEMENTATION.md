# Autenticación JWT - Guía de Implementación

## 📋 Archivos Creados/Modificados

### Backend (Django)

1. **`store/views/auth.py`** - Nuevas vistas de autenticación JWT
   - `login()` - Autenticación y generación de tokens
   - `refresh_token()` - Renovación de access token
   - `logout()` - Cierre de sesión
   - `verify_token()` - Verificación de token válido

2. **`store/views/decorators.py`** - Decoradores JWT mejorados
   - `jwt_role_required()` - Protección de rutas con validación de roles
   - `admin_required()` - Acceso solo para administradores

3. **`store/views/users.py`** - Vistas protegidas con JWT
   - Todas las rutas ahora requieren autenticación JWT
   - Solo administradores pueden acceder

4. **`ecommerce/settings.py`** - Configuración
   - JWT_SECRET_KEY agregada
   - CORS configurado para permitir peticiones del frontend
   - django-cors-headers instalado

5. **`store/urls.py`** - Nuevas rutas de API
   - `/api/auth/login/` - Login
   - `/api/auth/refresh/` - Renovar token
   - `/api/auth/logout/` - Logout
   - `/api/auth/verify/` - Verificar token
   - `/api/users/*` - CRUD de usuarios (solo admin)

### Frontend (JavaScript)

6. **`static/public/js/api-auth.js`** - Cliente de API con JWT
   - Funciones de autenticación
   - Interceptor automático para renovación de tokens
   - Gestión de localStorage
   - Funciones helper (isAuthenticated, isAdmin, etc.)

7. **`ejemplo-jwt.html`** - Ejemplo de uso

## 🚀 Configuración Inicial

### 1. Variables de Entorno

Agrega a tu archivo `.env`:

```env
JWT_SECRET_KEY=tu-clave-secreta-muy-segura-cambiar-en-produccion
```

**⚠️ IMPORTANTE:** Cambia esta clave en producción por una clave única y segura.

### 2. Instalar Dependencias

Las dependencias ya están instaladas, pero si necesitas reinstalarlas:

```bash
pip install PyJWT==2.10.1 django-cors-headers==4.6.0
```

### 3. Migraciones (si es necesario)

```bash
python manage.py makemigrations
python manage.py migrate
```

## 📡 Endpoints de la API

### Autenticación

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "tu_password"
}
```

**Respuesta exitosa:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  },
  "message": "Login exitoso"
}
```

#### Renovar Token
```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Verificar Token
```http
POST /api/auth/verify/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Usuarios (Solo Admin)

#### Obtener Usuarios
```http
GET /api/users/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Crear Usuario
```http
POST /api/users/create/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "username": "nuevo_usuario",
  "password": "password123",
  "role": "user"
}
```

#### Actualizar Usuario
```http
PUT /api/users/update/1/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "username": "usuario_actualizado",
  "password": "nueva_password",
  "role": "admin"
}
```

#### Eliminar Usuario
```http
DELETE /api/users/delete/1/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 💻 Uso en el Frontend

### Importar la API

```javascript
import { login, logout, fetchWithAuth, getUsers } from './static/public/js/api-auth.js';
```

### Ejemplo de Login

```javascript
try {
  const response = await login('admin', 'password123');
  console.log('Login exitoso:', response.user);
  // Los tokens se guardan automáticamente en localStorage
} catch (error) {
  console.error('Error:', error.message);
}
```

### Hacer Peticiones Autenticadas

```javascript
// Usando fetchWithAuth (recomendado - renueva el token automáticamente)
try {
  const response = await fetchWithAuth('http://localhost:8000/api/users/');
  const data = await response.json();
  console.log('Usuarios:', data);
} catch (error) {
  console.error('Error:', error);
}

// O usando las funciones helper
try {
  const users = await getUsers();
  console.log('Usuarios:', users);
} catch (error) {
  console.error('Error:', error);
}
```

### Verificar Autenticación

```javascript
import { isAuthenticated, isAdmin, getUser } from './api-auth.js';

// Verificar si está autenticado
if (isAuthenticated()) {
  console.log('Usuario autenticado');
}

// Verificar si es admin
if (isAdmin()) {
  console.log('El usuario es administrador');
}

// Obtener datos del usuario
const user = getUser();
console.log('Usuario actual:', user);
```

### Cerrar Sesión

```javascript
await logout();
// Redirige automáticamente a /login
```

## 🔐 Seguridad

### Access Token
- **Duración:** 1 hora
- **Tipo:** Bearer Token
- **Uso:** Todas las peticiones a la API

### Refresh Token
- **Duración:** 7 días
- **Uso:** Solo para renovar el access token

### Headers Requeridos

Todas las peticiones protegidas deben incluir:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## 🛠️ Troubleshooting

### Error: "Token expirado"
- Solución: El interceptor `fetchWithAuth` renueva automáticamente el token
- Si el refresh token también expiró, el usuario debe iniciar sesión nuevamente

### Error: "Permisos insuficientes"
- El usuario no tiene el rol requerido para acceder al endpoint
- Verificar que el usuario tenga role='admin' para endpoints administrativos

### Error: "CORS policy"
- Verificar que el frontend esté en la lista de `CORS_ALLOWED_ORIGINS` en `settings.py`
- Por defecto permite: localhost:3000, localhost:5173, localhost:8080

### Error: "Token inválido"
- El token puede estar corrupto o haber sido modificado
- Intentar cerrar sesión y volver a iniciar sesión

## 📝 Notas Importantes

1. **En Producción:**
   - Cambia `JWT_SECRET_KEY` por una clave única y segura
   - Usa HTTPS en todas las comunicaciones
   - Actualiza `CORS_ALLOWED_ORIGINS` con tu dominio real

2. **Tokens en localStorage:**
   - Son vulnerables a ataques XSS
   - Considera usar cookies httpOnly para mayor seguridad en producción

3. **Renovación Automática:**
   - `fetchWithAuth` renueva automáticamente el token si expira
   - No necesitas manejar la renovación manualmente

4. **Compatibilidad:**
   - Las rutas antiguas (`/auth/login_user/`, etc.) siguen funcionando
   - Se recomienda migrar a las nuevas rutas `/api/auth/*`

## 🎯 Próximos Pasos

1. Proteger todas las rutas de tu API con `@jwt_role_required()`
2. Implementar la UI de login en tu frontend
3. Agregar manejo de errores más robusto
4. Considerar implementar blacklist de tokens para logout real
5. Agregar rate limiting para prevenir fuerza bruta

## 📚 Recursos

- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [JWT.io](https://jwt.io/) - Para debuggear tokens

---

¿Necesitas ayuda? Revisa el archivo `ejemplo-jwt.html` para ver una implementación completa funcionando.
