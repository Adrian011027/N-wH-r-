# Guía de Despliegue: Gunicorn + Nginx + SSL en EC2

## Problema actual
- `runserver` funciona en `http://3.14.88.137:8000/` con estilos
- Gunicorn NO sirve archivos estáticos (CSS/JS) → eso es trabajo de Nginx
- El config de Nginx intentaba redirigir a HTTPS sin tener certificado SSL
- Las rutas en los archivos de configuración estaban incorrectas

## Archivos corregidos
- `nginx_nowheremx.conf` → rutas corregidas, HTTP primero (sin SSL hasta tener cert)
- `gunicorn.service` → usuario `ubuntu`, ruta `/home/ubuntu/n_wh_r`
- `ecommerce/settings.py` → `ALLOWED_HOSTS`, `STATIC_ROOT`, `CSRF_TRUSTED_ORIGINS`

---

## PASO 1: Subir archivos al servidor

Desde tu máquina local o con git pull en el servidor:
```bash
cd ~/n_wh_r
git pull origin main   # o como tengas configurado tu repo
```

---

## PASO 2: Preparar el entorno en el servidor

```bash
# Activar virtualenv
cd ~/n_wh_r
source venv/bin/activate

# Instalar dependencias (si no lo has hecho)
pip install -r requirements.txt

# Asegúrate de que gunicorn esté instalado
pip install gunicorn
```

---

## PASO 3: Configurar el .env de producción

Crea/edita el archivo `/home/ubuntu/n_wh_r/.env`:
```bash
nano ~/n_wh_r/.env
```

Contenido mínimo:
```env
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=nowheremx.com,www.nowheremx.com,3.14.88.137,localhost,127.0.0.1

# Base de datos
DB_NAME=nowhere_db
DB_USER=postgres
DB_PASSWORD=tu-password-de-postgres
DB_HOST=localhost
DB_PORT=5432

# Seguridad (activar DESPUÉS de tener SSL)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS=http://nowheremx.com,http://www.nowheremx.com,http://3.14.88.137

# Email
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# Twilio
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=xxx
TWILIO_ADMIN_PHONE=xxx

# Stripe
STRIPE_SECRET_KEY=xxx
STRIPE_PUBLIC_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx

# JWT
JWT_SECRET_KEY=tu-clave-jwt-segura

# S3 (si usas S3 para media)
USE_S3=False
```

---

## PASO 4: Recolectar archivos estáticos (CRÍTICO)

```bash
cd ~/n_wh_r
source venv/bin/activate
python manage.py collectstatic --noinput
```

Esto copia todos los CSS/JS/imágenes a `~/n_wh_r/staticfiles/` que es donde Nginx los buscará.

**Verificar que se creó:**
```bash
ls -la ~/n_wh_r/staticfiles/
# Deberías ver: admin/, dashboard/, public/, fonts/, images/, etc.
```

---

## PASO 5: Configurar Nginx

```bash
# Eliminar config default para evitar conflictos
sudo rm -f /etc/nginx/sites-enabled/default

# Copiar la nueva configuración
sudo cp ~/n_wh_r/nginx_nowheremx.conf /etc/nginx/sites-available/nowheremx.com

# Crear symlink (puede que ya exista)
sudo ln -sf /etc/nginx/sites-available/nowheremx.com /etc/nginx/sites-enabled/nowheremx.com

# Verificar que NO haya conflictos
sudo nginx -t
# Debe decir: syntax is ok / test is successful (SIN warnings de conflicting server name)

# Recargar nginx
sudo systemctl reload nginx
```

---

## PASO 6: Configurar Gunicorn como servicio

```bash
# Crear directorio de logs para gunicorn
sudo mkdir -p /var/log/gunicorn
sudo chown ubuntu:ubuntu /var/log/gunicorn

# Copiar servicio
sudo cp ~/n_wh_r/gunicorn.service /etc/systemd/system/gunicorn.service

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# Verificar que funciona
sudo systemctl status gunicorn
```

**Si hay errores, ver los logs:**
```bash
sudo journalctl -u gunicorn -n 50 --no-pager
sudo tail -f /var/log/gunicorn/error.log
```

---

## PASO 7: Verificar que funciona por HTTP

En este punto deberías poder acceder a:
- `http://3.14.88.137` → tu sitio con estilos (Nginx sirve estáticos, Gunicorn sirve Django)
- `http://nowheremx.com` → lo mismo, a través del dominio

**Si no funciona, verificar:**
```bash
# ¿Gunicorn está escuchando?
sudo ss -tulpn | grep 8000

# ¿Nginx está escuchando?
sudo ss -tulpn | grep 80

# ¿Error logs de nginx?
sudo tail -20 /var/log/nginx/nowheremx_error.log

# ¿Error logs de gunicorn?
sudo tail -20 /var/log/gunicorn/error.log
```

---

## PASO 8: Obtener certificado SSL con Let's Encrypt

```bash
# Crear directorio para certbot
sudo mkdir -p /var/www/certbot

# Obtener certificado (certbot modifica nginx automáticamente)
sudo certbot --nginx -d nowheremx.com -d www.nowheremx.com
```

Certbot te pedirá:
1. Tu email (para notificaciones de renovación)
2. Aceptar términos de servicio
3. Si quieres redirigir HTTP a HTTPS → **Sí**

Certbot automáticamente:
- Obtiene el certificado SSL
- Modifica `/etc/nginx/sites-available/nowheremx.com` para agregar HTTPS
- Agrega redirección de HTTP → HTTPS
- Configura renovación automática

---

## PASO 9: Activar seguridad SSL en Django

Después de tener SSL funcionando, edita `~/n_wh_r/.env`:

```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://nowheremx.com,https://www.nowheremx.com
```

Luego reiniciar gunicorn:
```bash
sudo systemctl restart gunicorn
```

---

## PASO 10: Verificar renovación automática de SSL

```bash
# Probar que la renovación funcione
sudo certbot renew --dry-run

# Ver certificados instalados
sudo certbot certificates

# La renovación se ejecuta automáticamente via systemd timer
sudo systemctl status certbot.timer
```

---

## Comandos útiles de mantenimiento

```bash
# Reiniciar gunicorn (después de cambios en código)
sudo systemctl restart gunicorn

# Recargar nginx (después de cambios en config)
sudo nginx -t && sudo systemctl reload nginx

# Ver logs en tiempo real
sudo tail -f /var/log/nginx/nowheremx_error.log
sudo tail -f /var/log/gunicorn/error.log
sudo journalctl -u gunicorn -f

# Probar que gunicorn funciona manualmente (debug)
cd ~/n_wh_r
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 ecommerce.wsgi:application
```

---

## Resumen de la arquitectura

```
Cliente (Browser)
       │
       ▼
   Cloudflare DNS (nowheremx.com → 3.14.88.137)
       │
       ▼
   Nginx (puerto 80/443)
       │
       ├── /static/  →  /home/ubuntu/n_wh_r/staticfiles/  (archivos CSS/JS)
       ├── /media/   →  /home/ubuntu/n_wh_r/media/         (imágenes subidas)
       └── /         →  proxy_pass http://127.0.0.1:8000   (Gunicorn → Django)
```

## Checklist de seguridad en EC2

- [ ] Security Group permite puertos 80 (HTTP) y 443 (HTTPS) desde 0.0.0.0/0
- [ ] Security Group NO expone el puerto 8000 al público (solo Nginx accede internamente)
- [ ] Puerto 22 (SSH) solo desde tu IP
- [ ] DEBUG=False en .env
- [ ] SECRET_KEY es único y seguro
- [ ] Certificado SSL instalado con certbot
