# ✅ Checklist de Validación - Sistema de Pagos Conekta

## Configuración previa

- [ ] **API Key de Conekta configurado en `.env`**
  ```
  CONEKTA_API_KEY=key_XXXXXXX
  ```
  - Obtén en: https://panel.conekta.com/developers/api-keys

- [ ] **Public Key de Conekta configurado**
  ```
  CONEKTA_PUBLIC_KEY=key_XXXXXXX
  ```
  - Diferente a la API Key privada

- [ ] **Modo correcto en `.env`**
  ```
  CONEKTA_MODE=sandbox  # Para pruebas
  # o
  CONEKTA_MODE=production  # Para producción
  ```

- [ ] **URLs de redirección configuradas (opcional)**
  ```
  CONEKTA_SUCCESS_URL=http://localhost:8000/pago/exitoso/
  CONEKTA_CANCEL_URL=http://localhost:8000/pago/cancelado/
  ```

---

## Carpetas y archivos

- [ ] **Carpeta `logs/` creada automáticamente**
  - Se crea en: `your-project/logs/`
  - Archivo: `conekta_payments.log`
  - Archivo: `payments_debug.log`
  - Archivo: `payment_errors.log`

- [ ] **Script de análisis de logs**
  - Archivo: `analyze_logs.py` (en la raíz del proyecto)
  - Uso: `python analyze_logs.py --stats`

- [ ] **Documentación de debugging**
  - Archivo: `CONEKTA_DEBUG_GUIDE.md` (en la raíz del proyecto)

---

## Flujo de pago - Validación paso a paso

### 1️⃣ Carrito con productos

- [ ] El cliente ha agregado productos al carrito
- [ ] Cada producto tiene: nombre, precio, talla, color, cantidad
- [ ] El carrito está asociado a un cliente
- [ ] El estado del carrito es: `activo`

**Log esperado:**
```
[CREAR_ORDEN_CONEKTA] INICIANDO
Item 1: [Producto] | Cantidad: 1 | Precio: 999.99 MXN
Total calculado: 99999 centavos = 999.99 MXN
```

---

### 2️⃣ Mostrar formulario de pago

- [ ] Se accede a: `/pago/formulario/{carrito_id}/`
- [ ] El carrito existe en BD
- [ ] El cliente existe y tiene correo
- [ ] Se renderiza el template `formulario_conekta.html`

**Log esperado:**
```
[MOSTRAR_FORMULARIO_PAGO] INICIANDO
Carrito encontrado | Cliente: username
✓ Total calculado: 999.99 MXN | 1 items
✓ Renderizando template
```

---

### 3️⃣ Generar token (Cliente - JavaScript)

- [ ] Se ejecuta el JavaScript de Conekta en el formulario
- [ ] El formulario tiene un botón "Pagar"
- [ ] Al hacer clic, se genera un token con Conekta.js
- [ ] El token se envía al servidor

**Validar:**
```javascript
// Debe haber algo como:
const token = await Conekta.Token.create({...});
```

---

### 4️⃣ Procesar pago (POST a Django)

- [ ] Endpoint: `POST /pago/procesar-conekta/`
- [ ] Body JSON contiene:
  ```json
  {
    "carrito_id": 42,
    "token": "tok_XXXXXX",
    "payment_method": "card"
  }
  ```

**Log esperado:**
```
[PROCESAR_PAGO_CONEKTA] INICIANDO PROCESAMIENTO DE PAGO
Parseando JSON del body...
✓ JSON parseado correctamente
Datos extraídos:
  - carrito_id: 42
  - token: tok_XXXXX...
  - payment_method: card
Buscando carrito #42...
✓ Carrito encontrado | Cliente: angel123
```

---

### 5️⃣ Validación de datos

- [ ] `carrito_id` es un número
- [ ] `token` no es vacío (comienza con `tok_`)
- [ ] `payment_method` es válido (`card`, `oxxo`, `bank_transfer`)
- [ ] El carrito existe en BD
- [ ] El cliente existe y tiene datos completos

**Log esperado:**
```
✓ Datos extraídos:
  - carrito_id: 42
  - payment_method: card
✓ Carrito encontrado
✓ Cliente: angel123 (correo@email.com)
```

**Si hay error:**
```
❌ Error: Carrito sin cliente asociado
```

---

### 6️⃣ Cálculo del total

- [ ] Se recorren todos los items del carrito
- [ ] Se obtiene el precio de cada variante
- [ ] Se multiplica cantidad × precio
- [ ] Se suma todo en centavos

**Log esperado:**
```
Calculando total del carrito...
Item 1: Nike Air Max | Negro-M | 999.99 MXN x 1 = 99999 centavos
Item 2: Adidas Ultra | Blanco-L | 1299.99 MXN x 2 = 259998 centavos
✓ Total calculado: 359997 centavos = 3599.97 MXN | 2 items
```

---

### 7️⃣ Envío a Conekta API

- [ ] Headers incluyen: `Authorization: Bearer {API_KEY}`
- [ ] Headers incluyen: `Accept: application/vnd.conekta-v2.0.0+json`
- [ ] Endpoint: `POST https://api.conekta.io/orders/{carrito_id}/charges`
- [ ] Payload contiene: `amount`, `payment_method`, `token_id`

**Log esperado:**
```
Enviando carga (charge) a Conekta API...
  - Endpoint: https://api.conekta.io/orders/42/charges
  - Monto: 359997 centavos
  - Método: card
```

---

### 8️⃣ Respuesta de Conekta

- [ ] Status HTTP: `200` o `201` (éxito)
- [ ] Response contiene: `id` (charge_id), `status`, `amount`

**Estados válidos del charge:**
- ✅ `paid` - Pago completado
- ✅ `pending_payment` - Pago pendiente
- ✅ `under_review` - En revisión
- ❌ `declined` - Pago rechazado
- ❌ `error` - Error en pago

**Log esperado (éxito):**
```
Respuesta Conekta - Status HTTP: 201
✓ Respuesta exitosa de Conekta
  - Charge ID: chr_ABCD1234
  - Status: paid
```

**Log esperado (error):**
```
Respuesta Conekta - Status HTTP: 400
ERROR AL CREAR ORDEN EN CONEKTA:
  - HTTP Status: 400
  - Response: {"message": "Invalid token"}
```

---

### 9️⃣ Crear Orden en Base de Datos

- [ ] Se crea registro en tabla `Orden`
- [ ] Se incluye: `carrito_id`, `cliente_id`, `total_amount`, `status`, `conekta_charge_id`
- [ ] Se crea `OrdenDetalle` para cada item del carrito
- [ ] El estado inicial es: `procesando` (si paid) o `pendiente_pago`

**Log esperado:**
```
Creando registro de Orden en base de datos...
✓ Orden creada en BD: #15 | Status: procesando
Creando detalles de orden...
  - Detalle 1: Nike Air Max x1
  - Detalle 2: Adidas Ultra x2
✓ Detalles de orden creados exitosamente
```

---

### 🔟 Vaciar carrito

- [ ] El carrito se marca como: `vacio`
- [ ] Los items del carrito se eliminan (opcional)

**Log esperado:**
```
Marcando carrito como vacío...
✓ Carrito vaciado correctamente
```

---

### 1️⃣1️⃣ Respuesta al cliente

- [ ] Se retorna JSON con `success: true`
- [ ] Se incluye: `orden_id`, `redirect` (URL de éxito)
- [ ] El cliente se redirige a: `/pago/exitoso/`

**Log esperado:**
```
✅ PAGO PROCESADO EXITOSAMENTE:
  - Orden ID: 15
  - Charge ID: chr_ABCD1234
  - Status: procesando
  - Monto total: 3599.97 MXN
```

---

## Errores comunes y cómo detectarlos

### Error 1: "JSON inválido"
**Busca en logs:**
```
ERROR AL PARSEAR JSON:
  - JSONDecodeError: ...
```
**Causa:** El body del request no es JSON válido
**Solución:** Verifica el JavaScript que envía el request

---

### Error 2: "Carrito no encontrado"
**Busca en logs:**
```
Buscando carrito #42...
[Error message]
```
**Causa:** El `carrito_id` no existe en BD
**Solución:** Verifica que el carrito_id sea correcto

---

### Error 3: "API Key incorrecta"
**Busca en logs:**
```
Respuesta Conekta - Status HTTP: 401
```
**Causa:** `CONEKTA_API_KEY` no es válida
**Solución:** Revisa la API Key en `.env`

---

### Error 4: "Token inválido"
**Busca en logs:**
```
Respuesta Conekta - Status HTTP: 400
Response: {"message": "Invalid token"}
```
**Causa:** El token de pago es inválido o expiró
**Solución:** Verifica que Conekta.js esté correctamente implementado

---

### Error 5: "Fondos insuficientes"
**Busca en logs:**
```
Respuesta Conekta - Status HTTP: 402
Response: {"message": "Insufficient funds"}
```
**Causa:** La tarjeta de prueba no tiene suficientes fondos
**Solución:** Usa tarjetas de prueba correctas

---

### Error 6: "No se conecta a Conekta"
**Busca en logs:**
```
ERROR DE CONEXIÓN CON CONEKTA:
  - Tipo: ConnectionError / TimeoutError
```
**Causa:** 
- Sin conexión a internet
- Firewall bloqueando
- Problemas en servidor Conekta

**Solución:** 
- Verifica tu conexión
- Revisa firewall/antivirus
- Intenta más tarde

---

## Pruebas con tarjetas de Conekta

### Tarjetas de prueba (Sandbox)

| Resultado | Número | CVV | Fecha |
|-----------|--------|-----|-------|
| ✅ Aprobado | 4242 4242 4242 4242 | 123 | 12/99 |
| ❌ Rechazado | 4000 0000 0000 0002 | 123 | 12/99 |
| ⏳ Revisión | 4000 1400 0000 0008 | 123 | 12/99 |
| ⚠️ Fondos insuficientes | 5555 5555 5555 4444 | 123 | 12/99 |

### Prueba paso a paso

```
1. Abre la aplicación
2. Agrega un producto al carrito
3. Procede al checkout
4. Usa tarjeta: 4242 4242 4242 4242
5. CVV: 123, Fecha: 12/99
6. Abre el log: tail -f logs/conekta_payments.log
7. Verifica que aparezcan todos los logs esperados
```

---

## Comandos útiles para debugging

### Ver logs en tiempo real
```powershell
# Windows PowerShell
Get-Content -Path logs/conekta_payments.log -Tail 50 -Wait
```

```bash
# Linux/Mac
tail -f logs/conekta_payments.log
```

### Ver solo errores
```powershell
# Windows
findstr "ERROR" logs/conekta_payments.log
```

```bash
# Linux/Mac
grep "ERROR" logs/conekta_payments.log
```

### Usar script de análisis
```bash
python analyze_logs.py --stats       # Estadísticas
python analyze_logs.py --errors      # Solo errores
python analyze_logs.py --last 100    # Últimas 100 líneas
python analyze_logs.py --search "token"  # Buscar palabra
```

---

## Verificación final

Antes de pasar a producción:

- [ ] Cambiar `CONEKTA_MODE` a `production`
- [ ] Cambiar `CONEKTA_API_KEY` a la clave de producción
- [ ] Cambiar `CONEKTA_PUBLIC_KEY` a la clave pública de producción
- [ ] Configurar webhook en panel de Conekta
- [ ] Probar con transacciones reales (pequeños montos)
- [ ] Verificar que `DEBUG=False` en settings.py
- [ ] Habilitar HTTPS para conexiones a Conekta

---

## 📊 Dashboard de logs

Puedes ver resumen de pagos ejecutando:

```bash
python analyze_logs.py
```

Esto mostrará:
- ✅ Resumen de archivos de log
- 📈 Estadísticas de pagos (exitosos, errores, pendientes)
- 💳 Últimos 3 pagos procesados

---

## 🆘 Soporte

Si tienes problemas:

1. 📝 **Revisa los logs** (comienza con `payment_errors.log`)
2. 🔍 **Usa el script de análisis**: `python analyze_logs.py --errors`
3. 🔗 **Consulta API de Conekta**: https://developers.conekta.com/
4. 📞 **Contacta Conekta**: support@conekta.com

---

**¡Ahora tienes visibilidad total del sistema de pagos! 🎉**
