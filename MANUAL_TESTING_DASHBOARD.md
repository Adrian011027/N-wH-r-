    # 📋 PLAN COMPLETO DE TESTING - DASHBOARD ADMINISTRATIVO

**Fecha:** 8 de febrero de 2026  
**Sistema:** E-commerce con Dashboard Admin  
**Funcionalidades:** Productos, Clientes, Órdenes, Categorías, Subcategorías  

---

## 🔍 ANÁLISIS DEL DASHBOARD

### ✅ Funcionalidades Identificadas

| Módulo | Funciones | Endpoints |
|--------|-----------|-----------|
| **Productos** | CRUD Completo, Variantes, Imágenes, Filtros | `/api/productos/*`, `/dashboard/productos/*` |
| **Clientes** | CRUD Básico, Edición | `/dashboard/clientes/*`, `/api/users/*` |
| **Órdenes** | Listado, Cambio de Estado, Filtros | `/api/admin/ordenes/*`, `/dashboard/ordenes/` |
| **Categorías** | CRUD | `/api/categorias/*`, `/dashboard/categorias/` |
| **Subcategorías** | CRUD | `/api/subcategorias/*`, `/dashboard/subcategorias/` |
| **Autenticación** | Login JWT, Protección de rutas | `/dashboard/login/`, JWT Tokens |

---

## 🧪 PRUEBAS MANUALES (E2E)

### 1️⃣ AUTENTICACIÓN Y ACCESO

#### ✓ Login Correcto  ----------Listo
```
Pasos:
1. Ir a http://127.0.0.1:8000/dashboard/login/
2. Ingresar usuario: "admin"
3. Ingresar contraseña: "admin123"
4. Click en "Ingresar"

✅ Esperado: Redirige a /dashboard/productos/ con token JWT en localStorage
```

#### ✓ Login Incorrecto  ----------Listo
```
1. Ingresar contraseña incorrecta
2. Click en "Ingresar"

❌ Esperado: Mensaje de error "Credenciales inválidas"
⚠️ NO redirige al dashboard
```

#### ✓ Acceso Sin Autenticación  ----------Listo
```
1. Abrir consola del navegador
2. Limpiar localStorage: localStorage.clear()
3. Intentar acceder a /dashboard/productos/

❌ Esperado: Redirige a /dashboard/login/
```

#### ✓ Token Expirado  ----------Listo
```
1. Modificar manualmente el token en localStorage (agregar caracteres)
2. Intentar cargar una página del dashboard
3. O esperar a que expire (exp: timestamp)

❌ Esperado: Redirige a login con mensaje "Sesión expirada"
```

---
Hasta aqui 
### 2️⃣ MÓDULO PRODUCTOS

#### ✓ Cargar Lista de Productos  ----------Listo
```
1. Ir a /dashboard/productos/
2. Esperar a que cargue la lista

✅ Esperado:
   - Se muestran todos los productos
   - Se muestra contador total de productos
   - Se muestra contador de stock total
   - Se muestra número de categorías
   - Se muestra número de ofertas
```

#### ✓ Filtrar por Género  ----------Listo
```
1. En /dashboard/productos/
2. Click en dropdown "Todos los géneros"
3. Seleccionar "Hombre"

✅ Esperado:
   - Se filtran productos con genero = "Hombre"
   - Se ocultan productos de "Mujer"
   - Los badges muestran "Hombre"
```

#### ✓ Filtrar por Categoría  ----------Listo
```
1. Click en dropdown "Todas las categorías"
2. Seleccionar una categoría disponible

✅ Esperado: Solo muestra productos de esa categoría
```

#### ✓ Filtrar por Stock  ----------Listo
```
1. Click en dropdown "Todo el stock"
2. Seleccionar "Con stock"

✅ Esperado: Filtra solo productos con stock > 0
```

#### ✓ Búsqueda por Texto  ----------Listo
```
1. Escribir en campo "Buscar producto..."
2. Ej: "Nike"

✅ Esperado: Filtra productos cuyo nombre o descripción coincidan
```
---------------
#### ✓ Crear Producto .------necesito actuaizar el form de variantes
```
1. Click en botón "Nuevo Producto"
2. Diligenciar formulario:
   - Nombre: "Test Product 2025"
   - Descripción: "Descripción de prueba"
   - Categoría: Seleccionar una
   - Género: "Hombre"
   - Precio: 999.99
   - Precio Mayorista: 599.99
   - Stock: 50
3. Click en "Guardar"

✅ Esperado:
   - Mensaje: "Producto creado exitosamente"
   - Producto aparece en la lista
   - ID generado correctamente
```

#### ✓ Editar Producto  ---- Error en las imagenes de variantes y producto
```
1. En listado de productos, click botón "Editar"
2. Cambiar valor: Stock de 50 a 75
3. Click en "Guardar cambios"

✅ Esperado:
   - Mensaje: "Producto actualizado"
   - El stock se actualiza en tiempo real
   - Cambios persisten al recargar
```

#### ✓ Ver Variantes   ----------Listo
```
1. Click en botón "Variantes" de un producto
2. Se abre modal con lista de variantes

✅ Esperado:
   - Modal muestra tabla de variantes
   - Muestra: Talla, Color, Precio, Stock
   - Permite editar variantes
```

#### ✓ Crear Variante Erroooooooooor en imagenes
```
1. En modal de variantes, click "Agregar Variante"
2. Diligenciar:
   - Talla: "30"
   - Color: "Rojo"
   - Precio: 1200
   - Stock: 15
3. Click "Guardar"

✅ Esperado:
   - Nueva variante aparece en tabla
   - Stock total del producto aumenta
```

#### ✓ Eliminar Producto  ----------Listoxx    
```
1. Click en botón "🗑️" de un producto
2. Confirmar eliminación en alert

✅ Esperado:
   - Producto desaparece de lista
   - Variantes asociadas se eliminan
   - Stock total se actualiza
```

---

### 3️⃣ MÓDULO CLIENTES

#### ✓ Cargar Lista de Clientes   ----------Listo
```
1. Ir a /dashboard/clientes/
2. Esperar carga

✅ Esperado:
   - Se muestran todos los clientes
   - Muestra: ID, Username, Email, Nombre
   - Contador de clientes totales
```

#### ✓ Buscar/Filtrar Clientes   ----------Listo
```
1. Escribir en campo de búsqueda
2. Ej: "jona"

✅ Esperado: Filtra clientes por nombre/email/username
```

#### ✓ Editar Cliente ----------Listo
```
1. Click en botón "Editar" de un cliente
2. Ir a /dashboard/clientes/editar/{id}/
3. Cambiar nombre o email
4. Guardar

✅ Esperado:
   - Datos se actualizan
   - Cambios persisten
   - Mensaje de éxito
```

#### ✓ Eliminar Cliente  ----------Listo
```
1. Click en botón "Eliminar" de un cliente
2. Confirmar

❌ Esperado:
   - Cliente se elimina de BD
   - Sus órdenes se marcan como "huérfanas" (si existe lógica)
   - Aparece en lista de eliminados o desaparece
```

---

### 4️⃣ MÓDULO ÓRDENES

#### ✓ Cargar Lista de Órdenes  ----------Listo
```
1. Ir a /dashboard/ordenes/
2. Esperar carga

✅ Esperado:
   - Se muestran todas las órdenes
   - Muestra: ID, Cliente, Total, Status, Fecha
   - Estadísticas: Total órdenes, Pendientes, Procesando, Pagadas
```

#### ✓ Filtrar por Status   ----------Listo
```
1. Click en dropdown "Status"
2. Seleccionar "Pagada"

✅ Esperado: Solo muestra órdenes con status = "pagada"
```

#### ✓ Filtrar por Rango de Fechas   ----------Listo
```
1. Ingresar fechas en "Desde" y "Hasta"
2. Presionar Enter o Tab

✅ Esperado: Filtra órdenes en ese rango
```

#### ✓ Buscar por Cliente  ----------Listo
```
1. Escribir nombre/email del cliente
2. Wait 400ms (debounce)

✅ Esperado: Filtra órdenes de ese cliente
```

#### ✓ Cambiar Status de Orden  ----------Listo
```
1. En listado de órdenes, cambiar status
2. Ej: De "activo" a "procesando"
3. Guardar

✅ Esperado:
   - Status se actualiza
   - Se guarda en BD
   - Refleja cambio en estadísticas
```

---

### 5️⃣ MÓDULO CATEGORÍAS

#### ✓ Cargar Categorías  ----------Listo  
```
1. Ir a /dashboard/categorias/
2. Esperar carga

✅ Esperado: Muestra tabla de categorías con opciones CRUD
```

#### ✓ Crear Categoría  ----------Listo
```
1. Click "Agregar Categoría"
2. Nombre: "Accesorios 2025"
3. Guardar

✅ Esperado:
   - Nueva categoría aparece en tabla
   - Se puede usar en productos
```

#### ✓ Editar Categoría  ----------Listo
```
1. Click "Editar" en una categoría
2. Cambiar nombre
3. Guardar

✅ Esperado: Cambios se persisten
```

#### ✓ Eliminar Categoría  ----------Listo
```
1. Click "Eliminar" en una categoría

⚠️ Esperado:
   - Si tiene productos: Error o aviso
   - Si no tiene productos: Se elimina
```

---

### 6️⃣ VALIDACIONES Y SEGURIDAD

#### ✓ Validación de Campo Requerido  ----------Listo
```
1. Intentar crear producto sin nombre
2. Click "Guardar"

❌ Esperado: Error "Campo requerido"
```

#### ✓ Validación de Precio  ----------Listo
```
1. Intentar ingresar precio negativo: -100
2. Guardar

❌ Esperado: Error "Precio debe ser positivo"
```

#### ✓ Validación de Stock  ----------Listo
```
1. Intentar ingresar stock negativo: -5
2. Guardar

❌ Esperado: Error "Stock debe ser >= 0"
```

#### ✓ Protección CSRF ----------Listo
```
1. Ver código fuente del formulario
2. Buscar token CSRF en HTML

✅ Esperado: 
   - Campo csrf_token presente en input
   - Meta tag csrf-token presente
   - Token en cookie csrftoken
   - Peticiones fetch incluyen header X-CSRFToken
   - Django valida token CSRF en POST/PUT/DELETE
```

#### ✓ Inyección SQL  ----------Listo
```
1. En búsqueda de clientes, escribir:   
2. Buscar

❌ Esperado:
   - No resulta en error SQL
   - Se busca como texto literal
   - ORM previene inyección
```

---

## 🤖 PRUEBAS AUTOMATIZADAS (Unit & Integration)

### Crear archivo: `test_dashboard_automation.py`

```python
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from store.models import Producto, Categoria, Usuario
import json

class DashboardAuthTest(TestCase):
    """Tests de autenticación del dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
    
    def test_login_correcto(self):
        """Test: Login exitoso redirige a dashboard"""
        response = self.client.post('/auth/login_user/', {
            'username': 'admin',
            'password': 'admin123'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())
    
    def test_login_incorrecto(self):
        """Test: Login fallido devuelve error"""
        response = self.client.post('/auth/login_user/', {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 401)
    
    def test_acceso_sin_token(self):
        """Test: No se puede acceder sin JWT"""
        response = self.client.get('/api/productos/')
        
        # Debería fallar o requerir token
        self.assertNotEqual(response.status_code, 200)


class ProductoAPITest(TestCase):
    """Tests de API de productos"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.categoria = Categoria.objects.create(nombre='Test')
        self.login()
    
    def login(self):
        response = self.client.post('/auth/login_user/', {
            'username': 'admin',
            'password': 'admin123'
        })
        self.token = response.json().get('token')
    
    def test_crear_producto(self):
        """Test: Crear producto vía API"""
        data = {
            'nombre': 'Test Product',
            'descripcion': 'Desc',
            'precio': 100,
            'categoria_id': self.categoria.id,
            'genero': 'Hombre',
            'stock': 50
        }
        
        response = self.client.post(
            '/api/productos/crear/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Producto.objects.filter(nombre='Test Product').exists())
    
    def test_actualizar_producto(self):
        """Test: Actualizar producto vía API"""
        producto = Producto.objects.create(
            nombre='Original',
            descripcion='Desc',
            precio=100,
            categoria=self.categoria,
            genero='Hombre'
        )
        
        data = {'nombre': 'Actualizado', 'stock': 75}
        
        response = self.client.post(
            f'/api/productos/update/{producto.id}/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Actualizado')
    
    def test_eliminar_producto(self):
        """Test: Eliminar producto vía API"""
        producto = Producto.objects.create(
            nombre='Para Eliminar',
            descripcion='Desc',
            precio=100,
            categoria=self.categoria,
            genero='Hombre'
        )
        
        response = self.client.delete(
            f'/api/productos/delete/{producto.id}/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producto.objects.filter(id=producto.id).exists())
    
    def test_filtro_genero(self):
        """Test: Filtro por género funciona correctamente"""
        p1 = Producto.objects.create(
            nombre='Hombre', descripcion='D', precio=100,
            categoria=self.categoria, genero='Hombre'
        )
        p2 = Producto.objects.create(
            nombre='Mujer', descripcion='D', precio=100,
            categoria=self.categoria, genero='Mujer'
        )
        
        response = self.client.get(
            '/api/productos/?genero=Hombre',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        data = response.json()
        self.assertEqual(len([p for p in data if p['genero'] == 'Hombre']), 1)


class ClienteAPITest(TestCase):
    """Tests de API de clientes"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.login()
    
    def login(self):
        response = self.client.post('/auth/login_user/', {
            'username': 'admin',
            'password': 'admin123'
        })
        self.token = response.json().get('token')
    
    def test_listar_usuarios(self):
        """Test: Obtener lista de usuarios"""
        response = self.client.get(
            '/api/users/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('usuarios', data)


class OrdenesDashboardTest(TestCase):
    """Tests de dashboard de órdenes"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.login()
    
    def login(self):
        response = self.client.post('/auth/login_user/', {
            'username': 'admin',
            'password': 'admin123'
        })
        self.token = response.json().get('token')
    
    def test_cargar_ordenes(self):
        """Test: Cargar lista de órdenes"""
        response = self.client.get(
            '/api/admin/ordenes/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('ordenes', data)
```

---

## 🔄 PRUEBAS DE PERFORMANCE

### Load Testing (Apache JMeter)
```
1. Thread Group: 50 usuarios
2. Ramp-up: 10 segundos
3. Duración: 60 segundos
4. Endpoints a probar:
   - GET /api/productos/
   - GET /dashboard/productos/
   - GET /api/admin/ordenes/
   - POST /api/productos/crear/
```

### Métricas Objetivo:
- Response Time Promedio: < 500ms
- 95% Response Time: < 1000ms
- Error Rate: < 1%
- Throughput: > 100 req/sec

---

## 🔐 PRUEBAS DE SEGURIDAD

### ✓ Verificar JWT en cada endpoint
```bash
# Sin token
curl http://127.0.0.1:8000/api/productos/crear/ -X POST
# ❌ Debería rechazar con 401

# Con token expirado
curl -H "Authorization: Bearer EXPIRED_TOKEN" http://127.0.0.1:8000/api/productos/
# ❌ Debería rechazar con 401
```

### ✓ Validar permisos por rol
```
- Usuario con rol='cliente' intenta crear producto
- ❌ Debería rechazar: "Permiso denegado"
```

### ✓ Protección contra CSRF
```
- Enviar formulario sin {% csrf_token %}
- ❌ Debería rechazar con 403
```

---

## 📊 CHECKLIST DE TESTING FINAL

- [ ] ✅ Login correcto
- [ ] ❌ Login incorrecto
- [ ] 🔐 Token expirado
- [ ] 📋 Listar productos
- [ ] ➕ Crear producto
- [ ] ✏️ Editar producto
- [ ] 🗑️ Eliminar producto
- [ ] 🔍 Filtrar por género
- [ ] 🔍 Filtrar por categoría
- [ ] 🔍 Filtrar por stock
- [ ] 🔎 Buscar por texto
- [ ] 👥 Listar clientes
- [ ] ✏️ Editar cliente
- [ ] 🗑️ Eliminar cliente
- [ ] 📦 Listar órdenes
- [ ] 🎛️ Cambiar status orden
- [ ] 📅 Filtrar por fechas
- [ ] 💾 Crear categoría
- [ ] ✏️ Editar categoría
- [ ] 🗑️ Eliminar categoría
- [ ] ⚠️ Validaciones requeridas
- [ ] ⚠️ Validaciones numéricas
- [ ] 🔒 Protección JWT
- [ ] 🔒 Protección CSRF
- [ ] 🚀 Performance aceptable
- [ ] 💾 Datos persisten en BD
- [ ] 🔄 Paginación funciona
- [ ] 🔄 Debounce en búsquedas
- [ ] 📱 Responsive design
- [ ] ♿ Accesibilidad básica

---

## 🚀 CÓMO EJECUTAR TESTS

```bash
# Tests unitarios
python manage.py test store.tests.test_dashboard_automation -v 2

# Tests con coverage
coverage run --source='.' manage.py test
coverage report

# Tests específicos
python manage.py test store.tests.test_dashboard_automation.DashboardAuthTest.test_login_correcto
```

---

## 📝 NOTAS IMPORTANTES

1. **Datos de prueba**: Usar datos realistas pero claramente marcados como "Test"
2. **Limpiar datos**: Después de cada test automatizado, limpiar BD
3. **Logs**: Revisar logs en `logs/` para errores de servidor
4. **Performance**: Monitorear tiempo de respuesta en desarrollo
5. **Security**: Nunca exponertoken en logs o reportes

---

Generated: 2026-02-08 | Status: ✅ LISTO PARA EJECUTAR
