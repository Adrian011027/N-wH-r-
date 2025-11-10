# 🔐 Guía de Migración JWT - Frontend

## ✅ Estado Actual del Proyecto

### Backend (100% Completado)
- ✅ JWT implementado en `/api/auth/` (login, refresh, logout, verify)
- ✅ Decoradores `@jwt_role_required()` y `@admin_required()` aplicados
- ✅ Todos los endpoints protegidos correctamente
- ✅ CORS configurado para frontend

### Frontend (En Progreso)
- ✅ Helper `fetch-helper.js` creado con auto-refresh de tokens
- ✅ Base template actualizado para incluir helper
- ⚠️ Archivos JS individuales requieren migración

---

## 📋 Archivos que Necesitan Actualización

### 🔴 ALTA PRIORIDAD (Operaciones protegidas)

#### 1. **carrito.js** (5 fetch calls)
**Endpoints afectados:**
- `PATCH /api/carrito/${ID}/item/${varId}/actualizar/` - Actualizar cantidad
- `GET /api/carrito/${ID}/` - Obtener carrito
- `DELETE /api/carrito/${ID}/item/${varId}/eliminar/` - Eliminar item
- `POST /api/carrito/${ID}/empty/` - Vaciar carrito

**Cambios requeridos:**
```javascript
// ❌ ANTES
const res = await fetch(`${API_BASE}/item/${varId}/actualizar/`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ cantidad: cant })
});

// ✅ DESPUÉS
const res = await fetchWithAuth(`${API_BASE}/item/${varId}/actualizar/`, {
    method: 'PATCH',
    body: JSON.stringify({ cantidad: cant })
});
```

#### 2. **wishlist.js** (11 fetch calls)
**Endpoints afectados:**
- `GET /api/wishlist/${clienteId}/` - Obtener wishlist
- `POST /api/wishlist/${clienteId}/` - Agregar producto
- `DELETE /api/wishlist/${clienteId}/` - Eliminar producto
- `GET /api/carrito/${clienteId}/` - Ver carrito
- `POST /api/carrito/create/${clienteId}/` - Crear carrito

**Cambios requeridos:**
```javascript
// ❌ ANTES
const r = await fetch(`${backendURL}${clienteId}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify({ producto_id: prodId })
});

// ✅ DESPUÉS
const r = await fetchPost(`${backendURL}${clienteId}/`, {
    producto_id: prodId
});
```

#### 3. **login.js** (2 fetch calls)
**REEMPLAZAR COMPLETAMENTE** con `api-auth.js`

```javascript
// ❌ ANTES (login.js completo)
const res = await fetch("/login-client/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
    body: JSON.stringify({ username, password })
});

// ✅ DESPUÉS (usando api-auth.js)
import { login } from '/static/public/js/api-auth.js';

const result = await login(username, password);
if (result.success) {
    window.location.href = "/";
} else {
    alert(result.message);
}
```

#### 4. **finalizar_compra.js**
**Endpoint:** `POST /api/orden/create/${clienteId}/`

```javascript
// ❌ ANTES
const res = await fetch(`/api/orden/create/${clienteId}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify(ordenData)
});

// ✅ DESPUÉS
const res = await fetchPost(`/api/orden/create/${clienteId}/`, ordenData);
```

#### 5. **detalles_producto/main.js** (2 fetch calls)
**Endpoints:**
- `POST /api/carrito/create/${cliId}/` - Agregar al carrito
- `POST /api/wishlist/${cliId}/` - Agregar a wishlist

```javascript
// ❌ ANTES
const res = await fetch(`/api/carrito/create/${cliId}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify({ variante_id: varId, cantidad: cant })
});

// ✅ DESPUÉS
const res = await fetchPost(`/api/carrito/create/${cliId}/`, {
    variante_id: varId,
    cantidad: cant
});
```

---

### 🟡 PRIORIDAD MEDIA (Algunos endpoints protegidos)

#### 6. **usuario.js**
- Endpoints de perfil de cliente (si existen)

#### 7. **productos_genero/main.js**
- Solo lectura, probablemente público

---

### 🟢 BAJA PRIORIDAD (Endpoints públicos)

#### 8. **registro_usuario/main.js**
- `POST /create-client/` - **Público**, no requiere token

#### 9. **inicio/main.js**
- Acciones generales, verificar si requieren autenticación

---

## 🛠️ Pasos de Migración

### **Paso 1: Verificar que fetch-helper.js esté cargado**
Confirmar que `base.html` incluya:
```html
<script src="{% static 'public/js/fetch-helper.js' %}"></script>
```

### **Paso 2: Reemplazar fetch() por fetchWithAuth()**

**Patrón GET:**
```javascript
// Antes
const res = await fetch('/api/endpoint/');

// Después
const res = await fetchGet('/api/endpoint/');
```

**Patrón POST:**
```javascript
// Antes
const res = await fetch('/api/endpoint/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});

// Después
const res = await fetchPost('/api/endpoint/', data);
```

**Patrón DELETE:**
```javascript
// Antes
const res = await fetch('/api/endpoint/', { method: 'DELETE' });

// Después
const res = await fetchDelete('/api/endpoint/');
```

**Patrón PATCH:**
```javascript
// Antes
const res = await fetch('/api/endpoint/', {
    method: 'PATCH',
    body: JSON.stringify(data)
});

// Después
const res = await fetchPatch('/api/endpoint/', data);
```

### **Paso 3: Eliminar headers manuales**
Ya no necesitas agregar:
- `Content-Type` (se agrega automáticamente)
- `Authorization` (se agrega automáticamente)
- `X-CSRFToken` (ya no se usa, JWT lo reemplaza)

### **Paso 4: Manejar respuestas 401**
El helper ya renueva tokens automáticamente. Si falla:
```javascript
const res = await fetchGet('/api/protected-endpoint/');

if (res.status === 401) {
    // Token inválido o expirado definitivamente
    alert('Sesión expirada, por favor inicia sesión nuevamente');
    window.location.href = '/login/';
}
```

---

## 🔍 Verificación Post-Migración

### **Checklist por archivo:**
- [ ] **carrito.js**: 5 fetch → fetchWithAuth
- [ ] **wishlist.js**: 11 fetch → fetchWithAuth
- [ ] **login.js**: Migrado a api-auth.js
- [ ] **finalizar_compra.js**: fetch → fetchPost
- [ ] **detalles_producto/main.js**: 2 fetch → fetchPost
- [ ] **usuario.js**: Verificar endpoints protegidos
- [ ] **registro_usuario/main.js**: Mantener sin token (público)

### **Pruebas funcionales:**
1. ✅ Login guarda tokens en localStorage
2. ✅ Peticiones incluyen `Authorization: Bearer <token>`
3. ✅ Token se renueva automáticamente al expirar
4. ✅ Logout limpia tokens y redirige
5. ✅ Endpoints protegidos rechazan sin token (401)
6. ✅ Endpoints admin rechazan usuarios normales (403)

---

## 📝 Notas Importantes

### **Endpoints Públicos (NO requieren token):**
- `POST /api/auth/login/` - Login
- `POST /create-client/` - Registro
- `GET /api/productos/` - Listado de productos
- `GET /api/productos/{id}/` - Detalle de producto
- `GET /api/categorias/` - Categorías

### **Endpoints Protegidos (Requieren JWT):**
- Todo lo relacionado con **carrito** (`/api/carrito/*`)
- Todo lo relacionado con **wishlist** (`/api/wishlist/*`)
- Todo lo relacionado con **órdenes** (`/api/orden/*`)
- **Perfil de cliente** (`/api/cliente/*`)

### **Endpoints Admin (Requieren role=admin):**
- **Gestión de usuarios** (`/api/usuarios/*`)
- **Gestión de productos** (CREATE/UPDATE/DELETE en `/api/productos/*`)
- **Gestión de órdenes** (UPDATE/DELETE en `/api/orden/*`)

---

## 🚀 Siguiente Paso

**RECOMENDACIÓN:** Migrar archivos en este orden:
1. `login.js` → Usar `api-auth.js` completo
2. `carrito.js` → Crítico para compras
3. `wishlist.js` → Alta frecuencia de uso
4. `finalizar_compra.js` → Flujo de pago
5. `detalles_producto/main.js` → Agregar al carrito desde detalle
6. Resto de archivos según prioridad

---

## ❓ Troubleshooting

### **Error: "Token expirado"**
- El helper renueva automáticamente
- Si persiste, verificar que `refresh_token` esté en localStorage

### **Error: "No autorizado (401)"**
- Usuario no ha iniciado sesión
- Tokens fueron limpiados manualmente
- Redirigir a `/login/`

### **Error: "Prohibido (403)"**
- Usuario autenticado pero sin permisos
- Endpoint requiere rol `admin`
- Mostrar mensaje de acceso denegado

### **Error: "CORS"**
- Verificar `CORS_ALLOWED_ORIGINS` en `settings.py`
- Asegurar que frontend corra en puerto permitido (3000, 5173, 8080)

---

**Última actualización:** $(Get-Date -Format "yyyy-MM-dd HH:mm")
