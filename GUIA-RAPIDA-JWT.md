# 🚀 Guía Rápida - Sistema JWT Dashboard

## ✅ ¿Qué se implementó?

Sistema de autenticación JWT completo con **auto-refresh automático** para el dashboard de administración.

---

## 🔑 Credenciales de Prueba

```
Usuario Dashboard (Admin):
- Username: admin
- Password: admin123
- URL: http://127.0.0.1:8000/dashboard/login/

Clientes (Frontend):
- jona / 123456
- angel / 123456
```

---

## 🎯 Problema Resuelto

**ANTES**: Error 401 Unauthorized al crear productos en dashboard

**AHORA**: ✅ Sistema funciona perfectamente con auto-refresh

---

## 💡 Cómo Usar

### Para Desarrolladores Frontend

Ya no necesitas preocuparte por los tokens JWT. Solo usa:

```javascript
// Simple GET
const productos = await authFetchJSON('/api/productos/');

// POST con JSON
const categoria = await authFetchJSON('/api/categorias/crear/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre: 'Nueva Categoría' })
});

// POST con FormData (archivos)
const formData = new FormData();
formData.append('nombre', 'Producto');
formData.append('imagen', file);

const response = await authFetch('/api/productos/crear/', {
    method: 'POST',
    body: formData
});

// DELETE
await authFetch(`/api/productos/delete/${id}/`, {
    method: 'DELETE'
});
```

**¡Eso es todo!** El sistema se encarga de:
- ✅ Agregar el header `Authorization`
- ✅ Renovar el token cuando expire (cada 30 min)
- ✅ Hacer logout si el refresh falla
- ✅ Manejar errores automáticamente

---

## ⏱️ Duración de Tokens

- **Access Token**: 30 minutos
- **Refresh Token**: 7 días

El sistema renueva automáticamente el access token cada vez que expira.

---

## 🧪 Probar el Sistema

### Opción 1: Interfaz Web (Recomendado)
```bash
# 1. Iniciar servidor
python manage.py runserver

# 2. Abrir navegador
http://127.0.0.1:8000/dashboard/login/

# 3. Login con admin/admin123

# 4. Crear un producto
# Debería funcionar sin errores
```

### Opción 2: Script de Pruebas
```bash
# Asegúrate de tener el servidor corriendo primero
python manage.py runserver

# En otra terminal:
python test_jwt_system.py
```

Verás:
```
🧪 SUITE DE PRUEBAS - SISTEMA JWT
====================================
🔐 Test 1: Login de usuario admin
✅ Login exitoso
   Access Token: eyJ0eXAiOiJKV1QiLCJhbGc...
   User ID: 1
   Username: admin

🔒 Test 2: Acceso a endpoint protegido
✅ Acceso exitoso
   Total productos: 5

🔄 Test 3: Renovar access token
✅ Token renovado exitosamente

⚠️  Test 4: Acceso con token inválido
✅ Token inválido correctamente rechazado (401)

🚫 Test 5: Acceso sin token
✅ Acceso sin token correctamente rechazado (401)

✅ PRUEBAS COMPLETADAS
```

---

## 📁 Archivos Importantes

```
NöwHėrē/
├── static/dashboard/js/
│   ├── auth-helper.js          ← 🆕 Helper centralizado JWT
│   ├── productos/
│   │   ├── registro.js         ← ✅ Actualizado
│   │   ├── lista.js            ← ✅ Actualizado
│   │   └── editar.js           ← ✅ Actualizado
│   ├── categorias/
│   │   └── categorias.js       ← ✅ Actualizado
│   └── ordenes/
│       └── lista.js            ← ✅ Actualizado
│
├── store/utils/
│   └── jwt_helpers.py          ← Backend JWT (30min/7días)
│
├── templates/dashboard/
│   └── base.html               ← ✅ Incluye auth-helper.js
│
├── SISTEMA-JWT-COMPLETO.md     ← 📚 Documentación completa
├── RESUMEN-IMPLEMENTACION-JWT.md ← 📊 Resumen de cambios
├── test_jwt_system.py          ← 🧪 Script de pruebas
└── GUIA-RAPIDA-JWT.md          ← 📖 Este archivo
```

---

## 🔧 Solución de Problemas

### Error: "No autenticado" al abrir dashboard

**Solución**: Asegúrate de hacer login primero en `/dashboard/login/`

---

### Error: Token expirado después de 30 minutos

**Esto es normal y esperado**. El sistema automáticamente:
1. Detecta que expiró
2. Usa el refresh token para obtener uno nuevo
3. Reintenta la operación

**No necesitas hacer nada** ✨

---

### Error: "Sesión expirada" después de 7 días

**Esto es normal**. El refresh token expiró. Simplemente:
1. Haz login nuevamente
2. Obtendrás nuevos tokens access + refresh

---

### Error 401 al crear productos

Si esto ocurre, verifica:

1. **¿Hiciste login?**
   ```
   URL: /dashboard/login/
   Usuario: admin
   Password: admin123
   ```

2. **¿Está incluido auth-helper.js?**
   Verifica en `templates/dashboard/base.html`:
   ```html
   <script src="{% static 'dashboard/js/auth-helper.js' %}"></script>
   ```

3. **¿Hay tokens en localStorage?**
   Abre DevTools → Console:
   ```javascript
   localStorage.getItem('access')  // Debería retornar un token largo
   localStorage.getItem('refresh') // Debería retornar un token largo
   ```

4. **¿El backend está corriendo?**
   ```bash
   python manage.py runserver
   ```

---

## 📞 Soporte

Si encuentras algún problema:

1. Lee `SISTEMA-JWT-COMPLETO.md` (documentación detallada)
2. Ejecuta `test_jwt_system.py` para diagnóstico
3. Verifica logs en DevTools → Console
4. Verifica logs en terminal de Django

---

## 🎉 ¡Listo!

El sistema está **100% funcional** y listo para usar.

Ahora puedes:
- ✅ Crear productos sin errores 401
- ✅ Gestionar categorías
- ✅ Ver y actualizar órdenes
- ✅ Trabajar sin preocuparte por tokens
- ✅ El auto-refresh funciona automáticamente

**¡A desarrollar!** 🚀
