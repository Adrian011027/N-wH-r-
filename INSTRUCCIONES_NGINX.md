# 🚀 Guía de Configuración Profesional con nginx + Gunicorn

## 📋 Archivos Creados

- **`gunicorn_config.py`** - Configuración de Gunicorn para producción
- **`nginx_nowheremx.conf`** - Configuración nginx con SSL, seguridad y optimización
- **`gunicorn.service`** - Servicio systemd para iniciar Gunicorn automáticamente
- **`setup_production.sh`** - Script automatizado de instalación
- **`SETTINGS_PRODUCCION.md`** - Configuración necesaria en Django settings.py

---

## 🔧 Pasos de Instalación

### 1️⃣ Copiar archivos a tu servidor AWS

```bash
# En tu EC2 (asumiendo que clonas el repo en /home/ec2-user/nowheremx)
cd /home/ec2-user/nowheremx

# Los archivos ya deben estar en tu proyecto:
ls -la gunicorn_config.py nginx_nowheremx.conf gunicorn.service setup_production.sh
```

### 2️⃣ Ejecutar el script de instalación

```bash
# Dar permisos de ejecución
chmod +x setup_production.sh

# Ejecutar (necesita sudo)
sudo -s
./setup_production.sh
```

**O hacer manualmente los pasos:**

### 3️⃣ Instalación Manual Paso a Paso

#### A) Actualizar sistema
```bash
sudo yum update -y
sudo yum install -y nginx certbot python3-certbot-nginx
```

#### B) Instalar Gunicorn
```bash
cd /home/ec2-user/nowheremx
source venv/bin/activate
pip install gunicorn
```

#### C) Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

#### D) Configurar nginx
```bash
sudo cp nginx_nowheremx.conf /etc/nginx/sites-available/nowheremx.com

# En Amazon Linux (no tiene sites-enabled por defecto):
# Editar /etc/nginx/nginx.conf y reemplazar 'include /etc/nginx/conf.d/*.conf;' con:
# include /etc/nginx/sites-available/*;

sudo nginx -t  # Verificar configuración
```

#### E) Configurar SSL con Let's Encrypt
```bash
sudo certbot certonly --standalone \
    -d nowheremx.com \
    -d www.nowheremx.com \
    --non-interactive \
    --agree-tos \
    --email tu_email@gmail.com
```

#### F) Instalar y activar servicio Gunicorn
```bash
sudo cp gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

#### G) Activar nginx
```bash
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### 4️⃣ Actualizar Django settings.py

Reemplaza estos valores en `ecommerce/settings.py`:

```python
# Dominio
ALLOWED_HOSTS = ['nowheremx.com', 'www.nowheremx.com']

# Desactivar DEBUG en producción
DEBUG = False

# SSL/HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

Ver más en `SETTINGS_PRODUCCION.md`

---

## ✅ Verificación

### Comprobar estado de servicios
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx

# En tiempo real:
sudo journalctl -u gunicorn -f
```

### Ver logs
```bash
# Gunicorn
sudo tail -f /var/log/gunicorn/error.log
sudo tail -f /var/log/gunicorn/access.log

# Nginx
sudo tail -f /var/log/nginx/nowheremx_error.log
sudo tail -f /var/log/nginx/nowheremx_access.log
```

### Probar conexión
```bash
# Debería retornar texto "healthy"
curl http://127.0.0.1:8000/health/

# Verificar HTTPS
curl -I https://nowheremx.com
```

---

## 🔄 Comandos Útiles en Producción

### Reiniciar después de cambios en código
```bash
cd /home/ec2-user/nowheremx
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

### Actualizar SSL (se hace automáticamente)
```bash
sudo certbot renew --dry-run  # Prueba
sudo certbot renew            # Real
```

### Monitorear en tiempo real
```bash
watch -n 1 'sudo systemctl status gunicorn gunicorn'
```

---

## 🛡️ Security Checklist

- ✅ DEBUG = False
- ✅ ALLOWED_HOSTS es específico
- ✅ SSL/HTTPS activado
- ✅ HSTS habilitado
- ✅ Cookies seguras (Secure + HttpOnly)
- ✅ Static files con cache-control
- ✅ Logs centralizados
- ✅ Firewall AWS Security Group configurado
- ✅ Certbot autorrenovable

---

## 🆘 Troubleshooting

### "502 Bad Gateway"
```bash
# Gunicorn no está corriendo
sudo systemctl status gunicorn
sudo systemctl restart gunicorn
sudo tail -f /var/log/gunicorn/error.log
```

### "Connection refused"
```bash
# Puerto 8000 no está abierto entre nginx y Gunicorn
# Verificar en nginx_nowheremx.conf: proxy_pass http://127.0.0.1:8000
sudo netstat -tlnp | grep 8000
```

### "SSL certificate problem"
```bash
sudo certbot certificates
sudo certbot renew --force-renewal
```

### "Permission denied" en logs
```bash
sudo chown ec2-user:ec2-user /var/log/gunicorn/
sudo chmod 755 /var/log/gunicorn/
```

---

## 📊 Arquitectura Final

```
🌐 Internet (HTTPS)
    ↓
🔒 Certbot/Let's Encrypt
    ↓
Nginx (Reverse Proxy)
├─ Puerto 80 → redirige a HTTPS
├─ Puerto 443 (SSL) → Gunicorn
├─ /static/ → Archivos estáticos
├─ /media/ → Archivos media
└─ / → Gunicorn en 127.0.0.1:8000
    ↓
Gunicorn (App Server)
├─ Django 5.2
├─ PostgreSQL
└─ AWS S3 (Media storage)
```

---

## 📞 Soporte

Si algo falla:
1. Revisa logs: `sudo journalctl -u gunicorn -f`
2. Verifica nginx: `sudo nginx -t`
3. Reinicia todo: `sudo systemctl restart gunicorn nginx`

¡Listo! Tu sitio está profesionalizado con nginx + Gunicorn + Let's Encrypt. 🎉
