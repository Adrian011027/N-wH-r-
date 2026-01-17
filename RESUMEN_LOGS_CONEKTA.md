# 🎯 Resumen - Sistema de Logs para Debugging de Pagos Conekta

## 📋 Cambios realizados

### 1. **Mejorado archivo `store/views/payment.py`**

✅ **Agregados logs profesionales con `logging` de Django:**
- Importación de módulo `logging` en lugar de solo `print()`
- Configurador de logger para guardar logs en archivos
- Logs estructurados en 4 funciones principales:
  1. `crear_orden_conekta()` - Crear orden en Conekta
  2. `mostrar_formulario_pago_conekta()` - Mostrar formulario
  3. `procesar_pago_conekta()` - **Procesar pago (la función más importante)**
  4. `webhook_conekta()` - Recibir eventos de Conekta

✅ **Niveles de logging:**
- `logger.info()` - Información importante del flujo
- `logger.debug()` - Detalles técnicos (items, payloads)
- `logger.warning()` - Advertencias (órdenes de prueba)
- `logger.error()` - Errores significativos
- `logger.exception()` - Errores con stack trace

---

### 2. **Configurado logging en `ecommerce/settings.py`**

✅ **Nueva sección `LOGGING`:**
- 3 archivo de logs creados automáticamente:
  - `logs/conekta_payments.log` - Log completo de Conekta
  - `logs/payments_debug.log` - Log detallado de depuración
  - `logs/payment_errors.log` - Errores solamente

✅ **Características:**
- Logs rotatorios (máx 10 MB cada uno)
- Guarda hasta 5-10 copias antiguas
- Formatos personalizados con timestamps
- Se crea carpeta `logs/` automáticamente

---

### 3. **Creado script `analyze_logs.py`**

✅ **Herramienta para analizar logs fácilmente:**

```bash
# Ver estadísticas
python analyze_logs.py

# Solo errores
python analyze_logs.py --errors

# Últimas N líneas
python analyze_logs.py --last 100

# Buscar palabra clave
python analyze_logs.py --search "token"

# Estadísticas detalladas
python analyze_logs.py --stats
```

---

### 4. **Documentos de referencia**

#### `CONEKTA_DEBUG_GUIDE.md`
- 📖 Guía completa para debuggear pagos
- 🔍 Cómo leer y entender los logs
- 🐛 Problemas comunes y soluciones
- 📊 Ejemplo de log exitoso
- 🛠️ Troubleshooting paso a paso

#### `CONEKTA_VALIDATION_CHECKLIST.md`
- ✅ Checklist de configuración previa
- 📋 Validación de cada paso del flujo
- 🚨 Errores comunes y cómo detectarlos
- 🎫 Tarjetas de prueba de Conekta
- 💻 Comandos útiles para debugging

---

## 🔍 Qué log cada paso del pago

### **[PROCESAR_PAGO_CONEKTA]** ← LA FUNCIÓN MÁS IMPORTANTE

```
┌─────────────────────────────────────────────┐
│ 1. Parseo de JSON                           │
│    - Extrae: carrito_id, token, method      │
├─────────────────────────────────────────────┤
│ 2. Validación de datos                      │
│    - Carrito existe                         │
│    - Cliente existe                         │
├─────────────────────────────────────────────┤
│ 3. Cálculo de total                         │
│    - Suma cada item (qty × precio)          │
│    - Total en centavos                      │
├─────────────────────────────────────────────┤
│ 4. Envío a Conekta API                      │
│    - POST /orders/{id}/charges              │
│    - Headers con API Key                    │
├─────────────────────────────────────────────┤
│ 5. Respuesta de Conekta                     │
│    - HTTP Status (201=éxito, 400=error)     │
│    - Charge ID y status                     │
├─────────────────────────────────────────────┤
│ 6. Crear Orden en BD                        │
│    - Tabla Orden + detalles                 │
│    - Copiar datos de Conekta                │
├─────────────────────────────────────────────┤
│ 7. Vaciar carrito                           │
│    - Marcar como vacio                      │
├─────────────────────────────────────────────┤
│ 8. Respuesta al cliente                     │
│    - JSON con orden_id                      │
└─────────────────────────────────────────────┘
```

Cada paso produce logs que puedes ver en `logs/conekta_payments.log`

---

## 📊 Ejemplo de uso

### Situación actual (el problema)
**"Se crea la orden pero falla el pago"**

### Solución para debuggear

```bash
# 1. Abre un terminal para ver logs en tiempo real
tail -f logs/conekta_payments.log

# 2. En otro terminal, ejecuta servidor
python manage.py runserver

# 3. Intenta hacer un pago desde navegador

# 4. En el primer terminal verás todos los pasos:
[PROCESAR_PAGO_CONEKTA] INICIANDO
...
✓ Total calculado: 1000 centavos
...
Respuesta Conekta - Status HTTP: 400  ← AQUÍ VES EL ERROR
Response: {"message": "Invalid token"}
```

**Resultado:** Ahora sabes que el problema es el token, no otra cosa.

---

## 🎯 Información capturada por cada función

### `crear_orden_conekta(carrito, cliente)`
- ✅ ID del carrito
- ✅ Datos del cliente
- ✅ Items (producto, talla, color, cantidad, precio)
- ✅ Total calculado
- ✅ Respuesta de Conekta (status, order_id)
- ✅ Errores de conexión

### `mostrar_formulario_pago_conekta(carrito_id)`
- ✅ Búsqueda del carrito
- ✅ Verificación del cliente
- ✅ Items para mostrar
- ✅ Total para el template
- ✅ Conekta order_id

### `procesar_pago_conekta(request)` ⭐
- ✅ **Validación de request JSON**
- ✅ **Extracción de carrito_id, token, payment_method**
- ✅ **Búsqueda de carrito en BD**
- ✅ **Cálculo detallado del total (cada item)**
- ✅ **Payload enviado a Conekta**
- ✅ **HTTP Status de respuesta**
- ✅ **Charge ID y status**
- ✅ **Creación de Orden en BD**
- ✅ **Errores específicos de Conekta**
- ✅ **Stack traces en caso de error**

### `webhook_conekta(request)`
- ✅ Firma del webhook (validación)
- ✅ Tipo de evento
- ✅ Order ID y Charge ID
- ✅ Actualización de estado

---

## 🚀 Próximos pasos

### 1. **Prueba el sistema**
```bash
# Ejecutar servidor
python manage.py runserver

# En otra terminal, ver logs
python analyze_logs.py
```

### 2. **Intenta un pago de prueba**
- Usa tarjeta: `4242 4242 4242 4242`
- CVV: `123`, Fecha: `12/99`
- Observa los logs

### 3. **Revisa los logs**
```bash
# Ver el flujo completo
tail -100 logs/conekta_payments.log

# Solo errores
cat logs/payment_errors.log

# Estadísticas
python analyze_logs.py --stats
```

### 4. **Si hay problema, identifica dónde**
Usa el checklist en `CONEKTA_VALIDATION_CHECKLIST.md`

---

## 📁 Estructura de archivos nuevos/modificados

```
your-project/
│
├── logs/                              ← NUEVA (auto-creada)
│   ├── conekta_payments.log           ← Todos los pagos
│   ├── payments_debug.log             ← Detalles técnicos
│   └── payment_errors.log             ← Solo errores
│
├── analyze_logs.py                    ← NUEVO (herramienta)
├── CONEKTA_DEBUG_GUIDE.md             ← NUEVO (guía)
├── CONEKTA_VALIDATION_CHECKLIST.md    ← NUEVO (checklist)
│
├── ecommerce/
│   └── settings.py                    ← MODIFICADO (logging config)
│
└── store/views/
    └── payment.py                     ← MODIFICADO (logging en funciones)
```

---

## ✨ Beneficios

| Antes | Después |
|-------|---------|
| ❌ Solo `print()` en consola | ✅ Logs profesionales en archivos |
| ❌ Logs desaparecen al reiniciar | ✅ Logs persistentes |
| ❌ Difícil identificar errores | ✅ Errores claramente identificados |
| ❌ No hay contexto de debugging | ✅ Contexto completo de cada operación |
| ❌ Imposible auditar pagos | ✅ Auditoría completa de transacciones |

---

## 💡 Tips para debugging efectivo

1. **Abre dos terminales:**
   - Terminal 1: `tail -f logs/conekta_payments.log`
   - Terminal 2: `python manage.py runserver`

2. **Intenta un pago mientras ves los logs en vivo**

3. **Busca palabras clave en los logs:**
   - "Error" → Problemas
   - "Status HTTP: 40X" → Errores de cliente
   - "Status HTTP: 50X" → Errores de servidor
   - "paid" → Pago exitoso

4. **Usa el script `analyze_logs.py`:**
   ```bash
   python analyze_logs.py --errors  # Solo errores
   ```

5. **Comparte los logs si necesitas ayuda:**
   ```bash
   # Pero primero, elimina datos sensibles
   tail -100 logs/conekta_payments.log > logs_to_share.txt
   ```

---

## 🎓 Entendiendo el flujo completo

```
USUARIO                    SERVIDOR DJANGO              CONEKTA
───────────────────────────────────────────────────────────────
  │                            │                           │
  │ 1. Click "Pagar"           │                           │
  ├───────────────────────────>│                           │
  │                            │ 2. Genera token (JS)      │
  │ 3. Envía token             │                           │
  ├───────────────────────────>│                           │
  │                            │ 4. POST /procesar-pago    │
  │                            │ [LOG: JSON parseado]      │
  │                            │                           │
  │                            │ 5. Busca carrito          │
  │                            │ [LOG: Carrito encontrado] │
  │                            │                           │
  │                            │ 6. Calcula total          │
  │                            │ [LOG: Total calculado]    │
  │                            │                           │
  │                            │ 7. POST /orders/ID/charges│
  │                            ├──────────────────────────>│
  │                            │                           │
  │                            │ 8. Conekta procesa        │
  │                            │ [LOG: Status HTTP]        │
  │                            │<──────────────────────────┤
  │                            │                           │
  │                            │ 9. Crea Orden en BD       │
  │                            │ [LOG: Orden creada]       │
  │                            │                           │
  │ 10. Redirige a éxito       │                           │
  │<───────────────────────────┤                           │
  │                            │                           │
```

Cada paso genera logs en `conekta_payments.log`

---

## 🔒 Información sensible

Los logs **incluyen:**
- Carrito ID ✅
- Cliente info (username, email) ✅
- Montos ✅
- Charge ID ✅
- Errores detallados ✅

Los logs **NO incluyen:**
- Número de tarjeta completo ❌
- CVV ❌
- API Key privada completa ❌
- Tokens de pago completos (solo primeros 30 chars) ❌

---

## 📞 Soporte

Si aún tienes problemas después de revisar los logs:

1. **Documenta el error:**
   ```bash
   tail -50 logs/payment_errors.log > error_report.txt
   ```

2. **Revisa Conekta:**
   - Panel: https://panel.conekta.com
   - API Docs: https://developers.conekta.com
   - Status: https://status.conekta.com

3. **Contacta Conekta:**
   - Email: support@conekta.com
   - Incluye logs y error_report.txt

---

## ✅ Verificación final

Después de estos cambios, verifica:

- [ ] La carpeta `logs/` se crea al ejecutar servidor
- [ ] Los archivos .log aparecen después de intentar un pago
- [ ] Puedes leer los logs con `tail -f` o `analyze_logs.py`
- [ ] Los errores son claros y actionables
- [ ] El flujo de pago está completamente documentado

**¡Listo! Ahora tienes visibilidad completa del sistema de pagos! 🎉**

---

*Generado: 16 de enero de 2026*
*Sistema: Django + Conekta v2.0.0*
