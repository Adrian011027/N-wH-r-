# 🔍 Guía de Debugging - Pagos con Conekta

## Resumen de cambios

Se han agregado **logs detallados** al sistema de pagos de Conekta para ayudarte a identificar dónde está el problema cuando un carrito se convierte en orden pero falla el pago.

---

## 📝 Dónde se guardan los logs

Los logs se guardan en la carpeta `logs/` en la raíz del proyecto:

```
your-project/
├── logs/
│   ├── conekta_payments.log         ← Log completo de pagos con Conekta
│   ├── payments_debug.log           ← Log detallado de todos los pagos
│   └── payment_errors.log           ← Errores de pagos
```

---

## 🔧 Niveles de logs agregados

Los logs ahora capturan:

### 1. **[CREAR_ORDEN_CONEKTA]**
- ✓ ID del carrito y cliente
- ✓ Cada item del carrito (producto, talla, color, cantidad, precio)
- ✓ Total calculado en pesos y centavos
- ✓ Payload enviado a Conekta
- ✓ Respuesta HTTP de Conekta (status code y body)
- ✓ Errores de conexión o validación

### 2. **[MOSTRAR_FORMULARIO_PAGO]**
- ✓ Búsqueda del carrito
- ✓ Verificación del cliente
- ✓ Creación de orden en Conekta
- ✓ Procesamiento de items para el template
- ✓ Renderización de la página

### 3. **[PROCESAR_PAGO_CONEKTA]** ⭐ MÁS IMPORTANTE
- ✓ Parseo del JSON del request
- ✓ Extracción de: carrito_id, token, payment_method
- ✓ **Validación de datos completos**
- ✓ Búsqueda del carrito en BD
- ✓ Cálculo del total (cada item desglosado)
- ✓ Payload para crear charge
- ✓ **Petición POST a `/orders/{carrito_id}/charges`**
- ✓ **Status HTTP de respuesta**
- ✓ **Estado del charge (paid, pending_payment, etc.)**
- ✓ **Creación de Orden en BD con sus detalles**
- ✓ **Errores específicos de Conekta**

### 4. **[WEBHOOK_CONEKTA]**
- ✓ Firma del webhook (validación)
- ✓ Tipo de evento (charge.paid, charge.under_review, etc.)
- ✓ Actualización de estado de orden

---

## 🚀 Cómo leer los logs

### Opción 1: En tiempo real (Windows PowerShell)
```powershell
# Ver log en tiempo real (últimas líneas)
Get-Content -Path logs/conekta_payments.log -Tail 50 -Wait

# Ver solo los errores
Get-Content -Path logs/payment_errors.log
```

### Opción 2: En el terminal (Linux/Mac/Git Bash)
```bash
# Ver log en tiempo real
tail -f logs/conekta_payments.log

# Ver solo errores
cat logs/payment_errors.log

# Ver últimas N líneas
tail -50 logs/conekta_payments.log
```

### Opción 3: En VS Code
1. Abre la carpeta `logs/`
2. Haz click derecho en `conekta_payments.log`
3. Selecciona "Open with Default Application"
4. O simplemente ábrelo en el editor

---

## 🐛 Problemas comunes y cómo identificarlos

### Problema 1: "La orden se crea pero falla el pago"

**Busca en `conekta_payments.log`:**

```
[PROCESAR_PAGO_CONEKTA] INICIANDO PROCESAMIENTO DE PAGO
...
📤 Enviando carga (charge) a Conekta API...
  - Endpoint: https://api.conekta.io/orders/XXXX/charges
  - Monto: 1000 centavos
  - Método de pago: card
...
📥 Respuesta Conekta - Status HTTP: [AQUÍ ESTÁ EL PROBLEMA]
```

**Códigos HTTP esperados:**
- `201` o `200`: ✅ Pago exitoso
- `400`: ❌ Datos inválidos (revisa el payload)
- `401`: ❌ API Key incorrecta
- `402`: ❌ Fondos insuficientes (cliente)
- `500`: ❌ Error del servidor de Conekta

---

### Problema 2: "El token es inválido"

**Busca en los logs:**

```
ERROR AL PARSEAR JSON:
  - Tipo: JSONDecodeError
```

O busca:

```
❌ Error en respuesta de Conekta:
  - HTTP Status: 400
  - Mensaje: "Invalid token"
```

**Solución:** Verifica que el token del cliente se está generando correctamente desde el formulario HTML/JS.

---

### Problema 3: "No encuentro la orden creada en BD"

**Busca en `conekta_payments.log`:**

```
Creando registro de Orden en base de datos...
✓ Orden creada en BD: #XXXX | Status: procesando
```

Si no ves esto, significa que la respuesta de Conekta no fue exitosa.

**Revisa el status del charge:**

```
✓ Respuesta exitosa de Conekta
  - Charge ID: chr_XXXXX
  - Status: [BUSCA AQUÍ]
```

Los estados válidos para crear orden son:
- `paid` ✅
- `pending_payment` ✅
- `under_review` ✅

Si ves otro estado, la orden no se crea.

---

### Problema 4: "Error de conexión con Conekta"

**Busca:**

```
ERROR DE CONEXIÓN CON CONEKTA:
  - Tipo: ConnectionError / Timeout / etc.
  - Detalle: [Lee aquí para más info]
```

**Posibles causas:**
- API Key incorrecta o expirada
- Firewall bloqueando conexión a Conekta
- Problema temporal en Conekta

---

## 📊 Ejemplo de log exitoso

```
================================================================================
[PROCESAR_PAGO_CONEKTA] INICIANDO PROCESAMIENTO DE PAGO
================================================================================
Parseando JSON del body...
✓ JSON parseado correctamente

Datos extraídos del request:
  - carrito_id: 42
  - token: tok_XXXXXXXXXXXXXX...
  - payment_method: card

Buscando carrito #42...
✓ Carrito encontrado | Cliente: angel123

Calculando total del carrito...
  Item 1: Nike Air Max | Negro-M | 999.99 MXN x 1 = 99999 centavos
  Item 2: Adidas Ultraboost | Blanco-L | 1299.99 MXN x 1 = 129999 centavos
✓ Total calculado: 229998 centavos = 2299.98 MXN | 2 items

Preparando payload para crear charge en Conekta...
Enviando carga (charge) a Conekta API...
  - Endpoint: https://api.conekta.io/orders/42/charges
  - Monto: 229998 centavos
  - Método de pago: card

Respuesta Conekta - Status HTTP: 201

✓ Respuesta exitosa de Conekta
  - Charge ID: chr_ABCD1234
  - Status: paid

Creando registro de Orden en base de datos...
✓ Orden creada en BD: #15 | Status: procesando

Creando detalles de orden...
  - Detalle 1: Nike Air Max x1
  - Detalle 2: Adidas Ultraboost x1

✓ Detalles de orden creados exitosamente

Marcando carrito como vacío...
✓ Carrito vaciado correctamente

✅ PAGO PROCESADO EXITOSAMENTE:
  - Orden ID: 15
  - Charge ID: chr_ABCD1234
  - Status: procesando
  - Monto total: 2299.98 MXN
================================================================================
```

---

## 🔒 Información sensible en logs

Los logs contienen:
- ❌ Token de pago (primeros 30 caracteres para identificar)
- ✅ ID de orden y cliente (necesarios para debugging)
- ✅ Amounts y detalles de pago (para auditoría)

**Seguridad:** Los logs no incluyen:
- Números de tarjeta completos
- CVV
- Claves privadas de API

---

## 📱 Webhook - Logs adicionales

Si configuraste el webhook (opcional), verás en `conekta_payments.log`:

```
[WEBHOOK_CONEKTA] EVENTO RECIBIDO
================================================================================
Signature recibida: abc123def456...
✓ Firma válida
✓ JSON parseado correctamente
  - Tipo de evento: charge.paid
  
📍 EVENTO: PAGO REALIZADO
  - Order ID: ord_ABC123
  - Charge ID: chr_XYZ789

✓ Orden actualizada: #15 → Status: pagado
```

---

## 🛠️ Troubleshooting paso a paso

### Paso 1: ¿Se crea la orden?
Busca en `conekta_payments.log`:
```
✓ Orden creada en BD: #XX
```
- **Sí**: Ve al Paso 2
- **No**: El pago falló en Conekta, revisa el status HTTP

### Paso 2: ¿Cuál es el status de pago?
Busca:
```
✓ Respuesta exitosa de Conekta
  - Status: [BUSCA AQUÍ]
```
- **paid**: ✅ Todo bien
- **pending_payment**: ⏳ Espera confirmación
- **Otro**: ❌ Verifica qué significa

### Paso 3: ¿Hay errores de BD?
Busca:
```
Error al crear orden en BD
```
- **Sí**: Lee el mensaje de error (constraints, etc.)
- **No**: Ve al Paso 4

### Paso 4: ¿El carrito se vacía?
Busca:
```
✓ Carrito vaciado correctamente
```
- **Sí**: Todo el proceso completó
- **No**: Hay un error antes

---

## 💡 Consejos para debugging

1. **Abre dos terminales:**
   - Una para `tail -f logs/conekta_payments.log`
   - Otra para ejecutar `python manage.py runserver`

2. **Intenta un pago de prueba** mientras ves los logs en tiempo real

3. **Copia los logs** y compártelos si necesitas ayuda

4. **Revisa primero `payment_errors.log`** para ver solo problemas

5. **Usa `grep` o `findstr` para buscar errores específicos:**
   ```powershell
   # Windows
   findstr "ERROR" logs/conekta_payments.log
   
   # Linux/Mac
   grep "ERROR" logs/conekta_payments.log
   ```

---

## 📞 Información de Conekta

- **Panel:** https://panel.conekta.com
- **API Docs:** https://developers.conekta.com/
- **Status:** https://status.conekta.com
- **Sandbox:** https://api.conekta.io (es la misma para dev y prod)

---

## ✅ Verificación final

Después de hacer estos cambios, verifica que:

1. ✅ La carpeta `logs/` se crea automáticamente
2. ✅ Los archivos de log aparecen cuando intentas un pago
3. ✅ Puedes leer los logs en tiempo real
4. ✅ Los errores son claros y actionables

¡Ahora tienes visibilidad completa del proceso de pago! 🚀
