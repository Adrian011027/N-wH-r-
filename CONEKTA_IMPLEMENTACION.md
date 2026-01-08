# Integración de Conekta como Pasarela de Pago

## 📋 Requisitos

1. **Cuenta en Conekta**: Crear en https://conekta.com
2. **Claves API**: Obtener en https://admin.conekta.com/settings/api
3. **Librería Conekta**: Ya instalada (`pip install conekta`)

---

## 🔑 Pasos de Configuración

### 1. Agregar Claves de Conekta al .env

```bash
# .env
CONEKTA_PRIVATE_KEY=sk_test_XXXXXXXXXXXXX
CONEKTA_PUBLIC_KEY=pk_test_XXXXXXXXXXXXXXX
CONEKTA_SUCCESS_URL=http://127.0.0.1:8000/pago/exitoso/
CONEKTA_CANCEL_URL=http://127.0.0.1:8000/pago/cancelado/
```

### 2. Agregar Webhook en Conekta Admin

1. Ir a: https://admin.conekta.com/webhooks
2. Crear nuevo webhook con URL: `https://tudominio.com/pago/webhook/conekta/`
3. Seleccionar eventos:
   - `charge.paid` (pago completado)
   - `charge.under_review` (revisión de fraude)
   - `charge.refunded` (reembolso)

### 3. Flujo de Compra Actualizado

**Antes (sin Conekta):**
```
Carrito → Finalizar Compra → Confirmación
```

**Ahora (con Conekta):**
```
Carrito → Seleccionar Método de Pago → Formulario Conekta → 
Pagar → Confirmación → Webhook actualiza estado
```

---

## 🔌 Endpoints Disponibles

### GET `/pago/formulario/<carrito_id>/`
Muestra el formulario de pago integrado con Conekta.

**Ejemplo:**
```html
<a href="/pago/formulario/1/" class="btn">Proceder a Pagar</a>
```

### POST `/api/pago/procesar/`
Procesa el pago mediante token de Conekta.

**Body (JSON):**
```json
{
  "carrito_id": 1,
  "token": "tok_xxx_yyy_zzz",
  "payment_method": "card"
}
```

**Response (exitoso):**
```json
{
  "success": true,
  "mensaje": "Pago procesado exitosamente",
  "orden_id": 42,
  "redirect": "/ordenar/1/exito/"
}
```

### POST `/pago/webhook/conekta/`
Recibe eventos de Conekta para confirmar pagos.

(Se configura automáticamente en el dashboard de Conekta)

---

## 💳 Métodos de Pago Soportados

### 1. Tarjeta de Crédito/Débito
- Visa, Mastercard, American Express, Discover
- Validación automática de CVV
- 3D Secure (opcional)

### 2. OXXO
- Pago en efectivo en tiendas OXXO
- Generar referencia de pago
- Validar pagos en webhook

### 3. SPEI
- Transferencia bancaria instantánea
- Para transferencias B2C
- Confirmación automática

---

## 📝 Modelos Afectados

### Orden (actualizado)
```python
class Orden(models.Model):
    carrito = models.OneToOneField(Carrito, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)  # 'procesando', 'pagado', 'enviado', etc.
    payment_method = models.CharField(max_length=50)  # 'conekta', 'transferencia', etc.
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 🧪 Pruebas con Tarjetas de Conekta

En **ambiente de pruebas**:

### Tarjeta Exitosa
```
Número:  4242 4242 4242 4242
Mes:     12
Año:     2025
CVV:     123
```

### Tarjeta con Fraude (revisión)
```
Número:  4100 0000 0000 0019
Mes:     12
Año:     2025
CVV:     123
```

### Tarjeta Rechazada
```
Número:  4000 0000 0000 0002
Mes:     12
Año:     2025
CVV:     123
```

---

## 🛠️ Integración en el Carrito

### 1. Actualizar botón de "Finalizar Compra"

**Antes:**
```html
<button onclick="finalizarCompra()">Finalizar Compra</button>
```

**Ahora:**
```html
<a href="/pago/formulario/{{ carrito.id }}/" class="btn btn-primary">
  Proceder al Pago
</a>
```

### 2. En carrito.js (si usas AJAX)

```javascript
async function finalizarCompra() {
  const carritoId = getCarritoId();
  
  // Redirigir al formulario de pago
  window.location.href = `/pago/formulario/${carritoId}/`;
}
```

---

## 📊 Estados de Pago

| Estado | Significado | Acción |
|--------|-----------|--------|
| `procesando` | Pago en proceso | Esperar confirmación |
| `pagado` | Pago completado | Preparar envío |
| `revisión` | Revisión de fraude | Comunicar al cliente |
| `reembolsado` | Dinero devuelto | Marcar como cancelado |

---

## 🔒 Seguridad

1. ✅ **HTTPS obligatorio** en producción
2. ✅ **Claves privadas** en variables de entorno (NO en código)
3. ✅ **CSRF protection** en formularios Django
4. ✅ **Validación de webhook** con firma de Conekta
5. ✅ **PCI DSS compliance** (sin guardar datos de tarjeta)

---

## 📞 Soporte

- **Documentación Conekta**: https://developers.conekta.com
- **API Reference**: https://api.conekta.com/docs
- **Status Page**: https://status.conekta.com

---

## ✅ Checklist de Implementación

- [ ] Cuenta creada en Conekta
- [ ] Claves API generadas
- [ ] Variables de entorno configuradas (.env)
- [ ] Librería conekta instalada
- [ ] Vistas de pago creadas (payment.py)
- [ ] URLs registradas
- [ ] Templates HTML creados
- [ ] Webhook configurado en Conekta Admin
- [ ] Pruebas con tarjetas de prueba
- [ ] Flujo de carrito actualizado
- [ ] Estado de órdenes actualizado
- [ ] Emails de confirmación configurados
- [ ] Documentación de usuario lista
- [ ] Pasar a producción (cambiar claves)

