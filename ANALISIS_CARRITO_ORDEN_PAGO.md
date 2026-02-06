# Análisis Completo: Carrito, Orden y Pago

## 📦 MÓDULO CARRITO

### Endpoints Disponibles

#### 1. Agregar Producto al Carrito
```
POST /api/carrito/create/<cliente_id>/
```
**Body JSON:**
```json
{
  "producto_id": 22,
  "talla": "26",
  "cantidad": 1
}
```
**Respuesta:**
```json
{
  "mensaje": "Producto agregado al carrito",
  "carrito_id": 5,
  "status": "activo",
  "producto": "Nike Air",
  "variante": {
    "sku": null,
    "talla": "26",
    "color": "Azul",
    "otros": {}
  },
  "cantidad": 1,
  "subtotal": 600.0
}
```

#### 2. Obtener Detalle del Carrito
```
GET /api/carrito/<cliente_id>/
Authorization: Bearer <access_token>
```
**Respuesta:**
```json
{
  "carrito_id": 5,
  "status": "activo",
  "mayoreo": false,
  "items": [
    {
      "producto_id": 22,
      "producto": "Nike Air",
      "precio_unitario": 600.0,
      "precio_menudeo": 600.0,
      "precio_mayorista": 300.0,
      "cantidad": 1,
      "talla": "26",
      "color": "Azul",
      "otros": {},
      "subtotal": 600.0,
      "variante_id": 30,
      "imagen": "/media/productos/prod-22-nike-air/imagen-1.png",
      "imagenes_galeria": ["/media/productos/prod-22-nike-air/imagen-1.png"]
    }
  ]
}
```

**Lógica de Mayoreo:**
- Si total de piezas >= 6 → aplica precio mayorista
- Si total de piezas < 6 → aplica precio normal

#### 3. Actualizar Cantidad de Producto
```
PATCH /api/carrito/<cliente_id>/item/<variante_id>/
Authorization: Bearer <access_token>
```
**Body JSON:**
```json
{
  "cantidad": 3
}
```

#### 4. Eliminar Producto del Carrito
```
DELETE /api/carrito/<cliente_id>/item/<variante_id>/
Authorization: Bearer <access_token>
```

#### 5. Vaciar Carrito Completo
```
DELETE /api/carrito/<cliente_id>/empty/
Authorization: Bearer <access_token>
```

---

## 📋 MÓDULO ORDEN

### Endpoints Disponibles

#### 1. Crear Orden desde Carrito
```
POST /ordenar/<carrito_id>/enviar/
```
**Proceso:**
1. Obtiene el carrito activo
2. Crea una Orden con status "pendiente"
3. Crea OrdenDetalle por cada item del carrito
4. Actualiza el carrito a status "procesando"
5. Retorna orden_id

**Respuesta:**
```json
{
  "orden_id": 15,
  "mensaje": "Orden creada exitosamente"
}
```

#### 2. Obtener Detalle de Orden
```
GET /orden/<orden_id>/
Authorization: Bearer <access_token>
```
**Respuesta:**
```json
{
  "id": 15,
  "cliente": {
    "username": "zem1r",
    "nombre": "Jonathan Reyes",
    "correo": "jona.emir@hotmail.com",
    "telefono": null
  },
  "carrito_id": 5,
  "total_piezas": 3,
  "total_amount": 1800.0,
  "status": "pendiente",
  "payment_method": "sin_especificar",
  "created_at": "2026-02-05T18:30:00Z",
  "items": [
    {
      "producto": "Nike Air",
      "variante_id": 30,
      "talla": "26",
      "color": "Azul",
      "cantidad": 3,
      "precio_unitario": 600.0,
      "subtotal": 1800.0
    }
  ]
}
```

#### 3. Obtener Órdenes del Cliente
```
GET /mis-pedidos/
Authorization: Bearer <access_token>
```
**Respuesta:**
```json
{
  "success": true,
  "ordenes": [
    {
      "id": 15,
      "status": "pendiente",
      "total_amount": 1800.0,
      "payment_method": "sin_especificar",
      "created_at": "05/02/2026 18:30",
      "created_at_iso": "2026-02-05T18:30:00Z",
      "items": [...],
      "total_items": 3
    }
  ]
}
```

#### 4. Actualizar Estado de Orden (Admin)
```
POST /orden/procesando/<orden_id>/
Authorization: Bearer <admin_token>
```

---

## 💳 MÓDULO PAGO (CONEKTA)

### Endpoints Disponibles

#### 1. Mostrar Formulario de Pago
```
GET /pago/formulario/<carrito_id>/
```
**Proceso:**
1. Obtiene el carrito y cliente
2. Crea orden en Conekta (o usa orden de prueba si falla)
3. Renderiza template con contexto de pago

#### 2. Procesar Pago
```
POST /pago/procesar/
```
**Body JSON:**
```json
{
  "carrito_id": 5,
  "token": "tok_test_visa_4242",
  "payment_method": "card"
}
```
**Proceso:**
1. Valida carrito y cliente
2. Crea orden en Conekta
3. Crea cargo (charge) con el token
4. Si el pago es exitoso:
   - Crea Orden en BD local
   - Actualiza stock de productos
   - Vacía el carrito
5. Retorna resultado del pago

**Respuesta Exitosa:**
```json
{
  "success": true,
  "orden_id": 15,
  "conekta_order_id": "ord_2...",
  "charge_id": "chg_2...",
  "payment_status": "paid",
  "total": 1800.0,
  "redirect_url": "/pago/exitoso/?orden_id=15"
}
```

#### 3. Crear Checkout de Conekta
```
POST /pago/crear-checkout/
```
**Body JSON:**
```json
{
  "carrito_id": 5
}
```
**Retorna:**
- checkout_id de Conekta
- orden_id de Conekta

#### 4. Verificar Orden Creada
```
GET /pago/verificar-orden/?carrito_id=5
```
**Respuesta:**
```json
{
  "success": true,
  "orden_existe": true,
  "orden_id": 15,
  "status": "pendiente"
}
```

#### 5. Webhook de Conekta (para producción)
```
POST /pago/webhook/
```
Recibe eventos de Conekta:
- `charge.paid` - Pago completado
- `charge.under_review` - Pago en revisión
- `charge.failed` - Pago fallido

---

## 🔄 FLUJO COMPLETO DE COMPRA

```
1. Cliente agrega productos al carrito
   └─> POST /api/carrito/create/<cliente_id>/

2. Cliente revisa su carrito
   └─> GET /api/carrito/<cliente_id>/

3. Cliente actualiza cantidades (opcional)
   └─> PATCH /api/carrito/<cliente_id>/item/<variante_id>/

4. Cliente finaliza compra
   └─> POST /ordenar/<carrito_id>/enviar/
       └─> Crea Orden con status "pendiente"

5. Sistema muestra formulario de pago
   └─> GET /pago/formulario/<carrito_id>/
       └─> Crea orden en Conekta

6. Cliente ingresa datos de pago
   └─> POST /pago/procesar/
       └─> Procesa pago con Conekta
       └─> Si exitoso:
           - Actualiza Orden a "pagado"
           - Actualiza stock
           - Vacía carrito

7. Cliente ve confirmación
   └─> GET /pago/exitoso/?orden_id=15

8. Cliente puede ver su historial
   └─> GET /mis-pedidos/
```

---

## 🧪 CASOS DE PRUEBA REQUERIDOS

### Carrito
- ✅ Agregar producto al carrito
- ✅ Obtener detalle del carrito
- ✅ Actualizar cantidad de producto
- ✅ Eliminar producto del carrito
- ✅ Vaciar carrito completo
- ✅ Verificar cálculo de mayoreo (>= 6 piezas)

### Orden
- ✅ Crear orden desde carrito
- ✅ Obtener detalle de orden
- ✅ Verificar items de la orden
- ✅ Obtener historial de órdenes del cliente

### Pago
- ✅ Procesar pago con token de prueba
- ✅ Verificar orden creada después del pago
- ✅ Verificar stock actualizado
- ✅ Verificar carrito vaciado

---

## 📊 DATOS DE PRUEBA

### Cliente Existente
```json
{
  "id": 16,
  "username": "zem1r",
  "nombre": "Jonathan Reyes",
  "email": "jona.emir@hotmail.com",
  "password": "123456"
}
```

### Productos Disponibles
```json
[
  {
    "id": 22,
    "nombre": "Nike Air",
    "variantes": [
      {"id": 30, "talla": "26", "color": "Azul", "precio": 600.0, "stock": 10},
      {"id": 31, "talla": "27", "color": "Azul", "precio": 600.0, "stock": 15}
    ]
  },
  {
    "id": 23,
    "nombre": "Dolce & Gabbana New Roma",
    "variantes": [
      {"id": 32, "talla": "25", "color": "Blanco y Negro", "precio": 1200.0, "stock": 15}
    ]
  },
  {
    "id": 24,
    "nombre": "Bota Dior",
    "variantes": [
      {"id": 33, "talla": "28", "color": "Negro", "precio": 4000.0, "stock": 20}
    ]
  },
  {
    "id": 25,
    "nombre": "Alexander McQueen",
    "variantes": [
      {"id": 34, "talla": "24", "color": "negro", "precio": 1500.0, "stock": 50}
    ]
  },
  {
    "id": 26,
    "nombre": "Jimmy Choo",
    "variantes": [
      {"id": 35, "talla": "23", "color": "Negro", "precio": 14000.0, "stock": 20}
    ]
  }
]
```
