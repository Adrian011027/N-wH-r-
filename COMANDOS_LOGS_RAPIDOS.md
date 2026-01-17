# 🚀 Comandos Rápidos - Debugging Conekta

## 📋 Cheat Sheet

### Ver logs en tiempo real
```powershell
# Windows PowerShell (RECOMENDADO)
Get-Content -Path logs/conekta_payments.log -Tail 50 -Wait

# O más simple
tail -f logs/conekta_payments.log
```

### Ver solo errores
```powershell
# Windows
findstr "ERROR\|ERROR AL\|❌" logs/conekta_payments.log

# Linux/Mac
grep "ERROR" logs/conekta_payments.log
```

### Últimas N líneas
```powershell
# Windows
Get-Content -Path logs/conekta_payments.log -Tail 100

# Linux/Mac
tail -100 logs/conekta_payments.log
```

### Usar script de análisis
```bash
# Resumen estadístico
python analyze_logs.py

# Solo errores
python analyze_logs.py --errors

# Últimas 50 líneas
python analyze_logs.py --last 50

# Buscar palabra
python analyze_logs.py --search "carrito_id"

# Estadísticas detalladas
python analyze_logs.py --stats
```

---

## 🔍 Buscar información específica

### Buscar por carrito_id
```bash
# Windows
findstr "carrito_id: 42" logs/conekta_payments.log

# Linux/Mac
grep "carrito_id: 42" logs/conekta_payments.log
```

### Buscar pagos exitosos
```bash
# Windows
findstr "PAGO PROCESADO EXITOSAMENTE" logs/conekta_payments.log

# Linux/Mac
grep "PAGO PROCESADO EXITOSAMENTE" logs/conekta_payments.log
```

### Buscar errores de API
```bash
# Windows
findstr "HTTP: 4\|HTTP: 5" logs/conekta_payments.log

# Linux/Mac
grep "HTTP Status:" logs/conekta_payments.log | grep -E "4[0-9]{2}|5[0-9]{2}"
```

### Buscar por cliente
```bash
# Windows
findstr "Cliente: angel123" logs/conekta_payments.log

# Linux/Mac
grep "Cliente: angel123" logs/conekta_payments.log
```

---

## 📊 Análisis rápido

### Contar pagos procesados
```bash
# Windows
findstr "PAGO PROCESADO EXITOSAMENTE" logs/conekta_payments.log | find /c /v "" 

# Linux/Mac
grep -c "PAGO PROCESADO EXITOSAMENTE" logs/conekta_payments.log
```

### Contar errores
```bash
# Windows
findstr "ERROR" logs/payment_errors.log | find /c /v ""

# Linux/Mac
grep -c "ERROR" logs/payment_errors.log
```

### Ver montos totales procesados (aproximado)
```bash
# Windows (requiere PowerShell avanzado)
(Get-Content logs/conekta_payments.log | Select-String "Total calculado" | Measure-Object).Count

# Linux/Mac
grep "Total calculado" logs/conekta_payments.log | wc -l
```

---

## 🔧 Limpiar logs

### Archivar logs antiguos
```bash
# Renombrar log actual con timestamp
mv logs/conekta_payments.log logs/conekta_payments.log.backup_$(date +%Y%m%d_%H%M%S)
```

### Eliminar todos los logs (CUIDADO)
```bash
# Windows
del logs\*.log

# Linux/Mac
rm logs/*.log
```

---

## 💻 Flujo de debugging completo

```bash
# Terminal 1: Ver logs en tiempo real
tail -f logs/conekta_payments.log

# Terminal 2: Ejecutar servidor
python manage.py runserver

# Terminal 3: Ejecutar cliente (si aplica)
# npm start (si tienes frontend)

# Luego intenta un pago y observa Terminal 1
```

---

## 🎯 Checklist de debugging

- [ ] Ejecutar `python analyze_logs.py` para resumen
- [ ] Buscar "ERROR" en logs
- [ ] Verificar HTTP Status (201=ok, 4xx=error cliente, 5xx=error servidor)
- [ ] Ver Charge Status (paid=ok, declined=rechazado, etc)
- [ ] Confirmar que Orden se crea en BD
- [ ] Revisar logs de errores en `payment_errors.log`

---

## 🆘 Problemas rápidos

### "No se crea la orden"
```bash
# Busca esto en logs:
grep "Orden creada en BD" logs/conekta_payments.log

# Si no aparece, busca el error antes:
grep "ERROR" logs/conekta_payments.log
```

### "Pago rechazado"
```bash
# Busca el status de Conekta:
grep "Status:" logs/conekta_payments.log | tail -5

# Busca la razón del rechazo:
grep "declined\|rejected" logs/payment_errors.log
```

### "API Key no válida"
```bash
# Busca error 401:
grep "HTTP.*401\|unauthorized" logs/conekta_payments.log

# Verifica .env:
echo %CONEKTA_API_KEY%  # Windows
echo $CONEKTA_API_KEY   # Linux/Mac
```

### "Token inválido"
```bash
# Busca en errores:
grep "Invalid token\|token_id" logs/payment_errors.log

# Verifica que el token se envíe desde JavaScript
```

---

## 📈 Reportes útiles

### Últimos 5 pagos
```bash
python analyze_logs.py --last 500 | grep "PAGO PROCESADO\|ERROR" | tail -10
```

### Resumen de hoy
```bash
# Windows
findstr /D:logs * | findstr "2026-01-16"

# Linux/Mac
grep "2026-01-16" logs/conekta_payments.log | tail -20
```

### Total de pagos intentados
```bash
python analyze_logs.py --stats
```

---

## ⚡ Atajos útiles

### Ver resumen + últimos errores
```bash
echo "=== RESUMEN ===" && \
python analyze_logs.py --stats && \
echo "" && \
echo "=== ÚLTIMOS ERRORES ===" && \
python analyze_logs.py --errors | tail -20
```

### Ver flujo de un pago específico
```bash
python analyze_logs.py --search "carrito_id: 42"
```

### Exportar logs para compartir (primeras 100 líneas)
```bash
# Windows
Get-Content logs/conekta_payments.log -Tail 100 > logs_export.txt

# Linux/Mac
tail -100 logs/conekta_payments.log > logs_export.txt

# Luego comparte logs_export.txt
```

---

## 🔐 Antes de compartir logs

**REVISAR QUE NO HAYA:**
- ❌ Números de tarjeta completos
- ❌ CVV
- ❌ Datos personales sensibles

**OK para compartir:**
- ✅ Carrito IDs
- ✅ Order IDs
- ✅ Cliente username
- ✅ HTTP Status codes
- ✅ Mensajes de error

---

## 📱 Tips rápidos

1. **Logs se generan automáticamente** - No necesitas crear la carpeta
2. **Máximo 10 MB por archivo** - Se dividen automáticamente
3. **Guardan hasta 5 copias** - No necesitas limpiar manualmente
4. **Timestamps incluidos** - Siempre sabes cuándo pasó algo
5. **Búsqueda es rápida** - grep/findstr es instantáneo

---

*Última actualización: 16/01/2026*
