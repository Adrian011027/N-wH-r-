### 🧪 Testing Rápido - Verificación de Email

#### 1. Test 404 - Verificar que NO se exponen las rutas
```bash
curl http://localhost:8000/ruta-inexistente/
```

**Esperado**: Página HTML amigable sin mostrar ninguna ruta del sistema

---

#### 2. Test Registro Nuevo Usuario
Abre tu navegador y ve a: `http://localhost:8000/`

1. Haz clic en "Registrarse"
2. Ingresa:
   - Email: `test@ejemplo.com`
   - Contraseña: `MiPassword123`
   - Confirmar: `MiPassword123`
3. Haz clic en "Crear Cuenta"

**Esperado**: Ves el mensaje "¡Cuenta creada! Revisa tu correo para verificarla."

---

#### 3. Test Email Enviado (Console del navegador)
En la consola del navegador (F12), ejecuta:
```javascript
// Deberías ver en la respuesta:
{
  "email_verification_sent": true,
  "requires_verification": true
}
```

---

#### 4. Test Link de Verificación (Obtener Token)
El token se guarda en la BD. Para simularlo:

```bash
python manage.py shell
```

```python
from store.models import Cliente
cliente = Cliente.objects.filter(correo='test@ejemplo.com').first()
print(f"Token: {cliente.email_verification_token}")
# Copia el token
```

Luego abre en el navegador:
```
http://localhost:8000/verificar-email/{token}/
```

**Esperado**: Página de éxito con mensaje "¡Correo verificado!"

---

#### 5. Test Rate Limiting
Intenta 6 veces hacer clic en reenviar verificación en menos de 1 hora:

```javascript
// Desde la consola del navegador
for(let i = 0; i < 6; i++) {
  fetch('/api/auth/reenviar-verificacion/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({correo: 'test@ejemplo.com'})
  }).then(r => r.json()).then(d => console.log(d))
}
```

**Esperado en el 6to intento**:
```json
{
  "error": "Demasiados intentos. Por favor espera X minutos.",
  "retry_after": 1800,
  "blocked": true
}
```
**Status**: 429 (Too Many Requests)

---

#### 6. Test Verificación de Estado
```bash
# Con token JWT válido
curl -H "Authorization: Bearer {tu_token}" \
  http://localhost:8000/api/auth/estado-verificacion/
```

**Esperado**:
```json
{
  "email_verified": true,
  "cliente_id": 1,
  "correo": "test@ejemplo.com"
}
```

---

#### 📊 Checklist de Prueba
- [ ] 404 no expone rutas
- [ ] Email de verificación se envía
- [ ] Link de verificación funciona
- [ ] Página de éxito se muestra
- [ ] Rate limiting bloquea después de 5 intentos
- [ ] Estado de verificación se actualiza correctamente
- [ ] Error 500 no expone detalles técnicos

---

**Nota**: Si no recibe emails, verifica que SMTP esté configurado en `.env`
