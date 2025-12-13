#!/bin/bash
# =========================================
# SCRIPT DE DESPLIEGUE EC2 CON RDS
# Uso: bash deploy.sh
# =========================================

set -e  # Salir si hay error

echo "🚀 Iniciando despliegue de NöwHėrē en EC2 con RDS..."
echo "=================================================="

# Variables
APP_DIR="/home/ec2-user/N-wH-r-"
VENV_DIR="$APP_DIR/venv"
GUNICORN_WORKERS=2
GUNICORN_PORT=8000

# 1. Actualizar sistema
echo "1️⃣ Actualizando sistema..."
sudo yum update -y > /dev/null 2>&1

# 2. Instalar dependencias del sistema
echo "2️⃣ Instalando dependencias del sistema..."
sudo yum install -y \
    python3.10 \
    python3.10-pip \
    python3.10-devel \
    postgresql15-devel \
    gcc \
    nginx \
    git > /dev/null 2>&1

# 3. Crear/actualizar virtual environment
echo "3️⃣ Configurando Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3.10 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 4. Instalar requirements
echo "4️⃣ Instalando dependencias Python..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r "$APP_DIR/requirements.txt" > /dev/null 2>&1
pip install gunicorn psycopg2-binary > /dev/null 2>&1

# 5. Ejecutar migraciones
echo "5️⃣ Ejecutando migraciones de BD..."
cd "$APP_DIR"
python manage.py migrate --noinput

# 6. Recopilar archivos estáticos
echo "6️⃣ Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# 7. Crear logs directory
echo "7️⃣ Creando directorio de logs..."
sudo mkdir -p /var/log/gunicorn
sudo chown -R ec2-user:ec2-user /var/log/gunicorn

# 8. Configurar Gunicorn systemd service
echo "8️⃣ Configurando servicio Gunicorn..."
sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=Gunicorn application server for NöwHėrē
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --bind 127.0.0.1:$GUNICORN_PORT \\
    --workers $GUNICORN_WORKERS \\
    --worker-class sync \\
    --timeout 120 \\
    --max-requests 1000 \\
    --access-logfile /var/log/gunicorn/access.log \\
    --error-logfile /var/log/gunicorn/error.log \\
    ecommerce.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 9. Configurar Nginx
echo "9️⃣ Configurando Nginx..."
sudo tee /etc/nginx/conf.d/nowhere.conf > /dev/null <<'EOF'
upstream gunicorn {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_request_buffering off;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias /home/ec2-user/N-wH-r-/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/ec2-user/N-wH-r-/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF

# 10. Probar configuración Nginx
echo "🔟 Verificando configuración Nginx..."
sudo nginx -t

# 11. Crear SWAP para 1GB RAM
echo "1️⃣1️⃣ Configurando SWAP..."
if [ ! -f /swapfile ]; then
    sudo dd if=/dev/zero of=/swapfile bs=1G count=2
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    echo "   ✅ SWAP de 2GB creado"
else
    echo "   ⚠️ SWAP ya existe"
fi

# 12. Iniciar servicios
echo "1️⃣2️⃣ Iniciando servicios..."
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn
sudo systemctl restart nginx
sudo systemctl enable nginx

# 13. Verificar estado
echo ""
echo "✅ DESPLIEGUE COMPLETADO"
echo "=================================================="
echo ""
echo "📊 Estado de servicios:"
sudo systemctl status gunicorn --no-pager | head -5
sudo systemctl status nginx --no-pager | head -5

echo ""
echo "📝 Logs disponibles en:"
echo "   • Gunicorn: /var/log/gunicorn/error.log"
echo "   • Nginx: /var/log/nginx/error.log"
echo ""
echo "🔗 Tu aplicación está en: http://TU_IP_EC2"
echo ""
echo "💡 Próximos pasos:"
echo "   1. Configurar dominio"
echo "   2. Instalar SSL (Let's Encrypt)"
echo "   3. Configurar RDS Security Group"
echo "   4. Añadir IP EC2 a ALLOWED_HOSTS"
echo ""
