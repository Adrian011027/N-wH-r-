#!/bin/bash

# ============================================================
# Script de instalación de nginx + Gunicorn en AWS para Django
# Dominio: nowheremx.com
# Usuario: ubuntu (EC2 con Ubuntu)
# Proyecto: /home/ubuntu/n_wh_r
# ============================================================

echo "🚀 Iniciando configuración de nginx + Gunicorn..."

# Variables
DOMAIN="nowheremx.com"
USER="ubuntu"
PROJECT_DIR="/home/$USER/n_wh_r"
VENV_DIR="$PROJECT_DIR/venv"

# ============================================================
# 1. ACTUALIZAR SISTEMA (Ubuntu/Debian)
# ============================================================
echo "📦 Actualizando sistema..."
sudo apt update -y
sudo apt install -y python3-pip nginx certbot python3-certbot-nginx git

# ============================================================
# 2. CREAR DIRECTORIOS DE LOGS
# ============================================================
echo "📁 Creando directorios..."
sudo mkdir -p /var/log/gunicorn
sudo chown $USER:$USER /var/log/gunicorn
sudo mkdir -p /var/www/certbot

# ============================================================
# 3. INSTALAR GUNICORN EN VENV
# ============================================================
echo "🔧 Instalando Gunicorn..."
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install gunicorn

# ============================================================
# 4. RECOLECTAR STATIC FILES (Django)
# ============================================================
echo "📂 Recolectando archivos estáticos..."
cd $PROJECT_DIR
$VENV_DIR/bin/python manage.py collectstatic --noinput

# ============================================================
# 5. COPIAR CONFIGURACIÓN DE NGINX
# ============================================================
echo "⚙️ Configurando nginx..."

# Amazon Linux usa conf.d/, Ubuntu/Debian usa sites-available/
if [ -d /etc/nginx/sites-available ]; then
    # Ubuntu/Debian
    sudo cp $PROJECT_DIR/nginx_nowheremx.conf /etc/nginx/sites-available/$DOMAIN
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
    sudo rm -f /etc/nginx/sites-enabled/default
elif [ -d /etc/nginx/conf.d ]; then
    # Amazon Linux / CentOS / RHEL
    sudo cp $PROJECT_DIR/nginx_nowheremx.conf /etc/nginx/conf.d/$DOMAIN.conf
    # Desactivar default si existe
    sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak 2>/dev/null || true
fi

# Verificar configuración de nginx
sudo nginx -t

# ============================================================
# 6. OBTENER SSL CON LET'S ENCRYPT
# ============================================================
echo "🔒 Obteniendo certificado SSL con Let's Encrypt..."

# Primero iniciar nginx solo con HTTP (certbot necesita validar)
sudo systemctl start nginx

# Obtener certificado (certbot-nginx lo configura automáticamente)
sudo certbot --nginx \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --non-interactive \
    --agree-tos \
    --email admin@$DOMAIN \
    --redirect

# Si certbot --nginx falla, intentar con standalone
if [ $? -ne 0 ]; then
    echo "⚠️ certbot --nginx falló, intentando con --standalone..."
    sudo systemctl stop nginx
    sudo certbot certonly --standalone \
        -d $DOMAIN \
        -d www.$DOMAIN \
        --non-interactive \
        --agree-tos \
        --email admin@$DOMAIN
    sudo systemctl start nginx
fi

# ============================================================
# 7. COPIAR SERVICIO SYSTEMD PARA GUNICORN
# ============================================================
echo "🔄 Instalando servicio systemd..."
sudo cp $PROJECT_DIR/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload

# ============================================================
# 8. ACTUALIZAR settings.py
# ============================================================
echo "⚙️ Actualizando settings.py de Django..."
# IMPORTANTES: Asegúrate de actualizar estos valores en settings.py:
# - ALLOWED_HOSTS = ['nowheremx.com', 'www.nowheremx.com']
# - DEBUG = False (IMPORTANTE!)
# - SECURE_SSL_REDIRECT = True
# - SESSION_COOKIE_SECURE = True
# - CSRF_COOKIE_SECURE = True

cat << 'EOF'

⚠️  IMPORTANTE - Actualiza estos valores en settings.py:

1. ALLOWED_HOSTS:
   ALLOWED_HOSTS = ['nowheremx.com', 'www.nowheremx.com']

2. DEBUG:
   DEBUG = False

3. Seguridad SSL:
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_HSTS_SECONDS = 31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True

EOF

# ============================================================
# 9. INICIAR SERVICIOS
# ============================================================
echo "🚀 Iniciando servicios..."
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl enable nginx
sudo systemctl restart nginx

# ============================================================
# 10. VERIFICAR ESTADO
# ============================================================
echo "✅ Verificando estado de servicios..."
sudo systemctl status gunicorn --no-pager
sudo systemctl status nginx --no-pager

# ============================================================
# 11. CONFIGURAR RENOVACIÓN AUTOMÁTICA DE SSL
# ============================================================
echo "🔄 Configurando renovación automática de SSL..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# ============================================================
# INFORMACIÓN FINAL
# ============================================================
echo ""
echo "============================================================"
echo "✅ ¡Instalación completada!"
echo "============================================================"
echo ""
echo "📍 Dominio: https://$DOMAIN"
echo "📍 Nginx config: /etc/nginx/sites-available/$DOMAIN"
echo "📍 Gunicorn logs: /var/log/gunicorn/"
echo "📍 Nginx logs: /var/log/nginx/"
echo ""
echo "🔧 Comandos útiles:"
echo "   sudo systemctl status gunicorn"
echo "   sudo systemctl restart gunicorn"
echo "   sudo systemctl status nginx"
echo "   sudo systemctl restart nginx"
echo "   sudo tail -f /var/log/gunicorn/error.log"
echo "   sudo tail -f /var/log/nginx/nowheremx_error.log"
echo ""
echo "🔒 SSL info:"
echo "   sudo certbot certificates"
echo "   sudo certbot renew --dry-run  (prueba renovación)"
echo ""
echo "============================================================"
