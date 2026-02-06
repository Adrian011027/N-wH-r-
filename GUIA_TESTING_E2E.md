# 🧪 GUÍA DE TESTING END-TO-END - CLIENTE

## 📋 Descripción General

El script `test_cliente_e2e.py` realiza un testing automatizado completo del flujo de un cliente desde el registro hasta el pago. Este documento describe:

1. ✅ Qué funcionalidades cubre el script
2. ⚙️ Cómo ejecutarlo
3. 🔍 Qué más deberías considerar para testing completo
4. 📊 Métricas y reportes

---

## ✅ Funcionalidades Cubiertas

### 1. **Registro de Cliente** (`test_registro_cliente`)
- **Endpoint**: `POST /create-client/`
- **Validaciones**:
  - ✓ Registro exitoso (status 200/201)
  - ✓ Respuesta contiene mensaje de confirmación
  - ✓ Datos guardados correctamente en BD

### 2. **Login y JWT** (`test_login_cliente`)
- **Endpoint**: `POST /auth/login_client/`
- **Validaciones**:
  - ✓ Credenciales correctas
  - ✓ Recepción de `access_token` y `refresh_token`
  - ✓ Recepción de `cliente_id`
  - ✓ Tokens válidos y decodificables

### 3. **Navegación de Productos** (`test_obtener_productos`)
- **Endpoint**: `GET /api/productos/`
- **Validaciones**:
  - ✓ Listado de productos disponible
  - ✓ Respuesta incluye IDs de productos
  - ✓ Datos de productos completos (nombre, precio, imagen)

### 4. **Wishlist (Lista de Deseos)** (`test_wishlist`)
- **Endpoints**:
  - `POST /wishlist/<cliente_id>/` - Agregar producto
  - `GET /wishlist/<cliente_id>/` - Obtener wishlist
  - `DELETE /wishlist/<cliente_id>/` - Eliminar producto
  - `DELETE /wishlist/all/<cliente_id>/` - Vaciar wishlist
- **Validaciones**:
  - ✓ Agregar productos a wishlist (autenticado)
  - ✓ Obtener lista completa de productos
  - ✓ Eliminar productos individualmente
  - ✓ Autenticación JWT funciona correctamente

### 5. **Carrito de Compras** (`test_carrito`)
- **Endpoints**:
  - `POST /api/carrito/create/<cliente_id>/` - Agregar item
  - `GET /api/carrito/<cliente_id>/` - Obtener carrito
  - `PATCH /api/carrito/<cliente_id>/item/<variante_id>/actualizar/` - Actualizar cantidad
  - `DELETE /api/carrito/<cliente_id>/item/<variante_id>/eliminar/` - Eliminar item
  - `DELETE /api/carrito/<cliente_id>/empty/` - Vaciar carrito
- **Validaciones**:
  - ✓ Agregar productos con talla/variante
  - ✓ Actualizar cantidades
  - ✓ Eliminar items del carrito
  - ✓ Cálculo correcto del total
  - ✓ Persistencia entre sesiones

### 6. **Creación de Orden** (`test_crear_orden`)
- **Endpoint**: `POST /ordenar/<carrito_id>/enviar/`
- **Validaciones**:
  - ✓ Orden creada con datos de envío
  - ✓ Orden vinculada correctamente al carrito
  - ✓ Generación de `orden_id`
  - ✓ Status inicial correcto (`pendiente`)

### 7. **Pago Simulado** (`test_pago_simulado`)
- **Endpoint**: `POST /orden/procesando/<orden_id>/`
- **Validaciones**:
  - ✓ Actualización de status a `pagado`
  - ✓ Simulación de webhook Conekta
  - ✓ Procesamiento de pago (sandbox)

### 8. **Verificación de Orden** (`test_verificar_orden`)
- **Endpoint**: `GET /orden/<orden_id>/`
- **Validaciones**:
  - ✓ Orden existe
  - ✓ Status actualizado correctamente
  - ✓ Total calculado correctamente
  - ✓ Fecha de creación registrada

### 9. **Mis Pedidos** (`test_mis_pedidos`)
- **Endpoint**: `GET /mis-pedidos/`
- **Validaciones**:
  - ✓ Acceso autenticado
  - ✓ Listado de pedidos del cliente
  - ✓ Información completa de cada pedido

---

## ⚙️ Cómo Ejecutar el Script

### **Requisitos**
```bash
pip install requests
```

### **Ejecución Básica**
```bash
# Servidor local (Django en :8000)
python test_cliente_e2e.py

# Servidor específico
python test_cliente_e2e.py --base-url http://production.nowhere.com

# Con ambiente virtual
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
python test_cliente_e2e.py
```

### **Salida Esperada**
```
======================================================================
STEP 1: Registro de Cliente
======================================================================

ℹ️  POST /create-client/
✅ Cliente registrado exitosamente
ℹ️  Mensaje: Cliente registrado correctamente

======================================================================
STEP 2: Login y Obtención de JWT
======================================================================

ℹ️  POST /auth/login_client/
✅ Login exitoso
ℹ️  Cliente ID: 42
ℹ️  Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

[... más output ...]

======================================================================
📊 RESUMEN DE RESULTADOS
======================================================================

✅ Tests pasados: 9/9
ℹ️  Tiempo total: 12.35s
```

---

## 🔍 Qué Más Deberías Considerar

### **1. Testing de Edge Cases (Casos Límite)**

#### **Registro de Cliente**
- ❌ Username duplicado (debe fallar)
- ❌ Email duplicado (debe fallar)
- ❌ Password débil (debe fallar)
- ❌ Campos obligatorios vacíos
- ❌ Email inválido
- ❌ Teléfono con formato incorrecto

#### **Login**
- ❌ Credenciales incorrectas
- ❌ Usuario no verificado
- ❌ Usuario bloqueado/inactivo
- ❌ Password expirado
- ✓ Refresh token después de expiración

#### **Wishlist**
- ❌ Agregar producto que no existe
- ❌ Agregar producto duplicado (debe ignorar)
- ✓ Sincronización entre invitado y autenticado
- ✓ Persistencia después de logout/login

#### **Carrito**
- ❌ Agregar producto sin stock
- ❌ Agregar cantidad mayor al stock disponible
- ❌ Agregar talla que no existe
- ✓ Carrito invitado (sin login)
- ✓ Migración de carrito invitado al autenticarse
- ✓ Carrito con múltiples variantes del mismo producto

#### **Orden y Pago**
- ❌ Crear orden con carrito vacío
- ❌ Pago rechazado por Conekta
- ❌ Datos de envío incompletos
- ✓ Webhook de Conekta con diferentes status
- ✓ Timeout en procesamiento de pago
- ✓ Orden duplicada (doble clic)

---

### **2. Testing de Seguridad**

```python
def test_seguridad():
    """
    Validaciones de seguridad que debes agregar
    """
    
    # JWT Expiration
    def test_jwt_expiracion():
        # Esperar a que expire el token
        time.sleep(7200)  # 2 horas
        # Intentar hacer request con token expirado
        # Debe fallar con 401
        pass
    
    # CSRF Protection
    def test_csrf_protection():
        # Hacer POST sin CSRF token
        # Debe fallar con 403
        pass
    
    # Acceso a recursos de otros usuarios
    def test_no_acceso_otros_usuarios():
        # Cliente A intenta acceder a carrito de Cliente B
        # Debe fallar con 403
        pass
    
    # SQL Injection
    def test_sql_injection():
        # Intentar inyección SQL en campos de búsqueda
        # Debe sanitizar y no ejecutar
        pass
    
    # XSS (Cross-Site Scripting)
    def test_xss_protection():
        # Intentar agregar <script> en nombre de producto
        # Debe escapar y no ejecutar
        pass
```

---

### **3. Testing de Performance**

```python
def test_performance():
    """
    Validaciones de rendimiento
    """
    
    # Carga concurrente
    def test_carga_concurrente():
        # 100 usuarios simultáneos agregando al carrito
        # Medir tiempo de respuesta
        # No debe haber deadlocks ni errores de concurrencia
        pass
    
    # Tiempo de respuesta
    def test_tiempo_respuesta():
        # Endpoints deben responder en < 500ms
        assert response_time < 0.5
    
    # Paginación de productos
    def test_paginacion():
        # Productos con 1000+ items
        # Debe paginar correctamente
        pass
```

---

### **4. Testing de Integración**

```python
def test_integracion():
    """
    Validaciones de integración con servicios externos
    """
    
    # Conekta (Sandbox)
    def test_conekta_sandbox():
        # Usar tokens de prueba de Conekta
        # Validar respuesta de API Conekta
        pass
    
    # Email (SMTP)
    def test_envio_email():
        # Verificar que emails se envían
        # Orden confirmada, recuperación de password, etc.
        pass
    
    # WhatsApp (Twilio)
    def test_envio_whatsapp():
        # Validar notificaciones por WhatsApp
        pass
    
    # AWS S3 (si aplica)
    def test_carga_imagenes():
        # Validar carga de imágenes a S3
        pass
```

---

### **5. Testing de UI/UX (Selenium)**

Para testing de interfaz gráfica, necesitarías **Selenium**:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_ui_flow():
    """
    Testing end-to-end con Selenium (navegador real)
    """
    
    driver = webdriver.Chrome()
    
    try:
        # 1. Abrir página de inicio
        driver.get("http://127.0.0.1:8000/")
        
        # 2. Click en "Registrarse"
        btn_registro = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btn-registro"))
        )
        btn_registro.click()
        
        # 3. Llenar formulario de registro
        driver.find_element(By.ID, "username").send_keys("test_user")
        driver.find_element(By.ID, "email").send_keys("test@test.com")
        driver.find_element(By.ID, "password").send_keys("Test123!")
        
        # 4. Submit
        driver.find_element(By.ID, "btn-submit").click()
        
        # 5. Verificar redirección a login
        WebDriverWait(driver, 10).until(
            EC.url_contains("/login")
        )
        
        # ... continuar flujo completo
        
    finally:
        driver.quit()
```

---

### **6. Testing de Datos (Database)**

```python
import psycopg2

def test_database_integrity():
    """
    Validaciones de integridad de datos en PostgreSQL
    """
    
    conn = psycopg2.connect(
        dbname="nowhere-db",
        user="nowhere_root",
        password="nowhere123",
        host="nowhere-db.ctcywc28slty.us-east-2.rds.amazonaws.com"
    )
    
    cur = conn.cursor()
    
    # Validar que orden tiene items
    cur.execute("""
        SELECT COUNT(*) 
        FROM store_orden o
        LEFT JOIN store_itemorden io ON o.id = io.orden_id
        WHERE o.id = %s
    """, (orden_id,))
    
    count = cur.fetchone()[0]
    assert count > 0, "Orden no tiene items"
    
    # Validar totales correctos
    cur.execute("""
        SELECT 
            o.total,
            SUM(io.cantidad * v.precio) as calculado
        FROM store_orden o
        JOIN store_itemorden io ON o.id = io.orden_id
        JOIN store_variante v ON io.variante_id = v.id
        WHERE o.id = %s
        GROUP BY o.id, o.total
    """, (orden_id,))
    
    total, calculado = cur.fetchone()
    assert total == calculado, f"Total incorrecto: {total} != {calculado}"
    
    conn.close()
```

---

## 📊 Métricas y Reportes

### **1. Coverage (Cobertura de Código)**

Usar `coverage.py`:

```bash
pip install coverage

# Ejecutar con coverage
coverage run test_cliente_e2e.py

# Ver reporte
coverage report

# HTML detallado
coverage html
```

### **2. CI/CD Integration**

Integrar en GitHub Actions:

```yaml
# .github/workflows/test.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install requests coverage
      
      - name: Run migrations
        run: python manage.py migrate
      
      - name: Start Django server
        run: python manage.py runserver &
        
      - name: Wait for server
        run: sleep 5
      
      - name: Run E2E tests
        run: coverage run test_cliente_e2e.py
      
      - name: Generate coverage report
        run: coverage report
```

---

## 🎯 Checklist Completo de Testing

### **Funcionalidad Core**
- [x] Registro de cliente
- [x] Login/Logout
- [x] Navegación de productos
- [x] Wishlist (agregar/eliminar/vaciar)
- [x] Carrito (agregar/actualizar/eliminar/vaciar)
- [x] Creación de orden
- [x] Pago (simulado)
- [x] Mis pedidos

### **Edge Cases**
- [ ] Duplicados (username, email)
- [ ] Campos inválidos
- [ ] Productos sin stock
- [ ] Tallas inexistentes
- [ ] Carrito vacío

### **Seguridad**
- [ ] JWT expiración
- [ ] CSRF protection
- [ ] Autorización (acceso a recursos propios)
- [ ] SQL Injection
- [ ] XSS

### **Performance**
- [ ] Carga concurrente (100+ usuarios)
- [ ] Tiempo de respuesta < 500ms
- [ ] Paginación con 1000+ productos

### **Integración**
- [ ] Conekta Sandbox
- [ ] Email SMTP
- [ ] WhatsApp Twilio
- [ ] AWS S3

### **UI/UX**
- [ ] Selenium tests (navegador real)
- [ ] Responsive design
- [ ] Accesibilidad

### **Base de Datos**
- [ ] Integridad referencial
- [ ] Transacciones ACID
- [ ] Cálculos correctos (totales)

---

## 🚀 Próximos Pasos

1. **Ejecutar el script base**: `python test_cliente_e2e.py`
2. **Revisar resultados**: Ver qué tests pasan/fallan
3. **Agregar edge cases**: Implementar validaciones de casos límite
4. **Integrar Selenium**: Para testing de UI
5. **Configurar CI/CD**: GitHub Actions para testing automático
6. **Métricas**: Coverage reports y dashboards

---

## 📝 Notas Finales

- El script actual cubre el **Happy Path** (flujo exitoso)
- Debes agregar validaciones de **error handling**
- Considera usar **pytest** para mejor organización de tests
- Implementa **mocks** para servicios externos (Conekta, Email, etc.)
- Usa **fixtures** para datos de prueba consistentes

**¿Siguiente paso?**: Ejecuta el script y analiza los resultados. Luego agrega validaciones de edge cases según prioridad.
