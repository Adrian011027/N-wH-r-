# ⚡ Quick Start - Debugging de Pagos Conekta

## 🎯 Objetivo
Identificar por qué se crea la orden pero falla el pago en Conekta.

## ✨ Cambios realizados (automáticos)

✅ Logs profesionales agregados a `/store/views/payment.py`  
✅ Configuración de logging en `ecommerce/settings.py`  
✅ Carpeta `logs/` se crea automáticamente  
✅ Script de análisis `analyze_logs.py` creado  

---

## 🚀 Comienza aquí (3 pasos)

### Paso 1: Reinicia el servidor
```bash
# Terminal 1
python manage.py runserver
```

### Paso 2: Mira los logs en tiempo real
```bash
# Terminal 2
tail -f logs/conekta_payments.log
```

### Paso 3: Intenta hacer un pago
- Abre tu app en navegador
- Agrega un producto al carrito
- Ve al checkout
- Usa tarjeta de prueba: **4242 4242 4242 4242**
- Mira qué pasa en Terminal 2

---

## 📊 Entender los logs

Mientras intentas el pago, deberías ver en Terminal 2:

```
[PROCESAR_PAGO_CONEKTA] INICIANDO PROCESAMIENTO DE PAGO
│
├─ ✓ JSON parseado
├─ ✓ Carrito encontrado
├─ ✓ Total calculado: 999.99 MXN
├─ 📤 Enviando a Conekta...
│
├─ 📥 Respuesta: Status HTTP 201  ← SI ES 201, PAGO OK
│  ├─ ✓ Charge ID: chr_XXXXX
│  └─ ✓ Status: paid
│
├─ ✓ Orden creada en BD
├─ ✓ Carrito vaciado
│
└─ ✅ PAGO PROCESADO EXITOSAMENTE
```

---

## 🔴 Si hay error, busca esto:

### "HTTP: 400" o "HTTP: 401"
```bash
tail -20 logs/conekta_payments.log | grep "Response:"
```
**Problemas:**
- 401 = API Key incorrecta
- 400 = Token inválido o datos mal formados

### "No se crea la orden"
```bash
grep "Orden creada en BD" logs/conekta_payments.log
```
Si no aparece, es que Conekta rechazó el pago. Busca el Status HTTP.

### "Connection error"
```bash
grep "ERROR DE CONEXIÓN" logs/conekta_payments.log
```
Problema de red o Conekta está caído.

---

## 💡 Herramientas útiles

### Ver resumen de todos los pagos
```bash
python analyze_logs.py
```

### Ver solo errores
```bash
python analyze_logs.py --errors
```

### Buscar un carrito específico
```bash
python analyze_logs.py --search "carrito_id"
```

---

## ✅ Validación

Después de intentar un pago, verifica:

```bash
# 1. ¿Se creó el archivo de log?
ls -la logs/

# 2. ¿Hay contenido?
wc -l logs/conekta_payments.log

# 3. ¿Cuál fue el último evento?
tail -5 logs/conekta_payments.log
```

---

## 📁 Archivos nuevos

| Archivo | Propósito |
|---------|-----------|
| `logs/` | Carpeta con archivos de log (auto-creada) |
| `analyze_logs.py` | Script para analizar logs |
| `CONEKTA_DEBUG_GUIDE.md` | Guía completa de debugging |
| `CONEKTA_VALIDATION_CHECKLIST.md` | Checklist de validación |
| `COMANDOS_LOGS_RAPIDOS.md` | Atajos y comandos rápidos |
| `RESUMEN_LOGS_CONEKTA.md` | Resumen general de cambios |
| `QUICK_START.md` | Este archivo |

---

## 🎓 Ejemplo: El flujo completo

### Escenario 1: Pago exitoso ✅
```
Cliente hace clic en "Pagar"
↓
JavaScript genera token con Conekta
↓
Se envía POST /pago/procesar-conekta/
↓ [LOG] JSON parseado
↓ [LOG] Carrito encontrado
↓ [LOG] Total calculado: 999.99 MXN
↓
Django envía charge a Conekta
↓ [LOG] Status HTTP: 201
↓ [LOG] Charge ID: chr_XXXXX
↓ [LOG] Status: paid
↓
Se crea Orden en BD
↓ [LOG] Orden creada: #42
↓
Cliente redirigido a éxito ✅
```

### Escenario 2: Pago con error ❌
```
Cliente hace clic en "Pagar"
↓
[Lo mismo hasta aquí]
↓
Django envía charge a Conekta
↓ [LOG] Status HTTP: 400
↓ [LOG] Error: "Invalid token"  ← AQUÍ ESTÁ EL PROBLEMA
↓
NO se crea Orden
↓
Cliente ve error ❌
↓ [LOG] ERROR guardado en payment_errors.log
```

---

## 🔍 Diagnóstico rápido

### ¿Se crea la orden?
```bash
grep "Orden creada en BD" logs/conekta_payments.log
```
- **Sí** → Pago fue exitoso, revisar si BD está bien
- **No** → Conekta rechazó el pago, buscar error HTTP

### ¿Cuál es el error?
```bash
grep "ERROR\|Status HTTP" logs/conekta_payments.log | tail -10
```

### ¿Cuál es el estado final?
```bash
tail -20 logs/conekta_payments.log | grep -E "EXITOSAMENTE|ERROR|charged"
```

---

## 🛠️ Solución rápida por error

### Error 401 (API Key inválida)
1. Abre `.env`
2. Verifica `CONEKTA_API_KEY=key_...`
3. Cópialo exactamente de https://panel.conekta.com/developers/api-keys
4. Reinicia servidor

### Error 400 (Token inválido)
1. Verifica que tu HTML/JS tenga Conekta.js correctamente
2. Comprueba que el token se genera con `Conekta.Token.create()`
3. Prueba con tarjeta `4242 4242 4242 4242`

### No se conecta a Conekta
1. Verifica tu conexión a internet
2. Intenta `ping api.conekta.io`
3. Revisa firewall/antivirus
4. Intenta más tarde

---

## 📞 Obtener ayuda

### Paso 1: Recopila información
```bash
# Exporta los últimos logs
tail -100 logs/conekta_payments.log > mi_problema.txt

# Exporta los errores
cat logs/payment_errors.log > errores.txt
```

### Paso 2: Comprarte con documentación
- Lee `CONEKTA_DEBUG_GUIDE.md` (problemas comunes)
- Lee `CONEKTA_VALIDATION_CHECKLIST.md` (validación paso a paso)

### Paso 3: Si aún necesitas ayuda
- Adjunta `mi_problema.txt` y `errores.txt`
- Incluye el mensaje de error exacto
- Describe qué estabas haciendo cuando falló

---

## ⏱️ Tiempo esperado

- **Configurar logs**: ✅ Ya hecho
- **Ver tu primer log**: 2 minutos
- **Identificar un problema**: 5 minutos
- **Arreglarlo**: Depende del error (5-30 minutos)

---

## 🎯 Siguiente paso

Ahora que tienes logs, intenta esto:

1. **Abre dos terminales**
   ```bash
   Terminal 1: tail -f logs/conekta_payments.log
   Terminal 2: python manage.py runserver
   ```

2. **Intenta varios pagos**
   - Uno exitoso (4242 4242 4242 4242)
   - Uno fallido (4000 0000 0000 0002)
   - Uno en revisión (4000 1400 0000 0008)

3. **Observa patrones en los logs**
   - ¿Cómo cambia el "Status" según la tarjeta?
   - ¿Dónde es el "point of failure"?

4. **Documenta tu problema específico**
   - "Mi pago se rechaza en Conekta con Status 400 porque..."
   - Ahora sabes exactamente qué está pasando

---

## 💻 Comandos clave memorizados

```bash
# Ver logs en vivo
tail -f logs/conekta_payments.log

# Solo errores
tail -f logs/payment_errors.log

# Búsqueda rápida
grep "ERROR" logs/conekta_payments.log

# Análisis automático
python analyze_logs.py --stats
```

---

## ✨ Resumen

| Antes | Ahora |
|-------|-------|
| ❌ Sin logs, solo consola confusa | ✅ Logs claros y persistentes |
| ❌ "No sé dónde falla" | ✅ Sé exactamente dónde y por qué |
| ❌ Difícil debuggear | ✅ Debugging es simple |
| ❌ Imposible auditar | ✅ Auditoría completa |

---

## 🚀 ¡Empecemos!

1. Abre dos terminales
2. Ejecuta: `tail -f logs/conekta_payments.log` en una
3. Ejecuta: `python manage.py runserver` en otra
4. Intenta hacer un pago
5. Observa los logs aparecer en tiempo real
6. ¡Identifica el problema!

**¿Listo? ¡Adelante! 🎉**

---

*Para ayuda detallada:*
- **Guía completa**: `CONEKTA_DEBUG_GUIDE.md`
- **Checklist**: `CONEKTA_VALIDATION_CHECKLIST.md`
- **Comandos rápidos**: `COMANDOS_LOGS_RAPIDOS.md`
