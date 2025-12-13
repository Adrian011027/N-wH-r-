#!/bin/bash
# =====================================================
# CHECKLIST DE OPTIMIZACIÓN EC2 + RDS
# Ejecuta este script para verificar la configuración
# =====================================================

echo "🔍 VERIFICANDO CONFIGURACIÓN PARA EC2 + RDS"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $2 encontrado"
        return 0
    else
        echo -e "${RED}❌${NC} $2 NO encontrado"
        return 1
    fi
}

check_config() {
    if grep -q "$1" "$2" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $3"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC} $4"
        return 1
    fi
}

echo "📦 ARCHIVOS REQUERIDOS:"
check_file "requirements.txt" "requirements.txt"
check_file "manage.py" "manage.py"
check_file ".env.example" ".env.example"
check_file "deploy.sh" "deploy.sh"
check_file "ecommerce/settings.py" "settings.py"

echo ""
echo "🔧 CONFIGURACIÓN DE DJANGO:"
check_config "postgresql" "ecommerce/settings.py" "Base de datos PostgreSQL configurada" "Usar PostgreSQL para RDS"
check_config "config('DB_HOST'" "ecommerce/settings.py" "Variables de entorno en settings" "Agregar variables de entorno"
check_config "python-decouple" "requirements.txt" "python-decouple instalado" "Instalar python-decouple"
check_config "psycopg2" "requirements.txt" "Driver PostgreSQL presente" "Instalar psycopg2-binary"
check_config "gunicorn" "requirements.txt" "Gunicorn presente" "Instalar gunicorn"

echo ""
echo "📋 ARCHIVOS PARA PRODUCCIÓN:"
check_file ".env.example" "Plantilla .env"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️${NC} .env no existe (crear antes de desplegar)"
fi

echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo ""
echo "1️⃣ EN AWS:"
echo "   ☐ Crear RDS PostgreSQL (db.t3.micro)"
echo "   ☐ Anotar endpoint: nombre-db.xxxxxx.rds.amazonaws.com"
echo "   ☐ Crear Security Group para RDS (puerto 5432)"
echo "   ☐ Crear EC2 (t3.micro, 10GB storage, 1GB RAM)"
echo "   ☐ Crear Security Group para EC2 (puertos 80, 443, 22)"
echo "   ☐ Aceptar conexiones RDS desde SG de EC2"
echo ""
echo "2️⃣ EN EC2:"
echo "   ☐ git clone https://github.com/Adrian011027/N-wH-r-.git"
echo "   ☐ Copiar .env.example a .env"
echo "   ☐ Editar .env con datos de RDS"
echo "   ☐ bash deploy.sh (ejecutar script)"
echo ""
echo "3️⃣ POST-DESPLIEGUE:"
echo "   ☐ Configurar dominio"
echo "   ☐ Instalar SSL (certbot)"
echo "   ☐ Verificar logs: tail -f /var/log/gunicorn/error.log"
echo "   ☐ Monitorar: watch -n 1 free -h"
echo ""
echo "4️⃣ VALORES RECOMENDADOS PARA .env:"
echo ""
echo "   # Base de datos RDS"
echo "   DB_HOST=nombre-db.xxxxx.us-east-1.rds.amazonaws.com"
echo "   DB_USER=postgres"
echo "   DB_PASSWORD=[GENERA_UNA_FUERTE]"
echo "   DB_NAME=nowhere_db"
echo ""
echo "   # Producción"
echo "   DEBUG=False"
echo "   SECURE_SSL_REDIRECT=True"
echo "   SESSION_COOKIE_SECURE=True"
echo "   CSRF_COOKIE_SECURE=True"
echo ""
echo "   # Seguridad"
echo "   SECRET_KEY=[GENERA_UNA_NUEVA]"
echo "   JWT_SECRET_KEY=[GENERA_UNA_NUEVA]"
echo ""

echo ""
echo "📊 AHORRO DE RECURSOS:"
echo "   PostgreSQL Local: ~300-500 MB RAM"
echo "   Solo Django + RDS: ~100-200 MB RAM"
echo "   ✨ AHORRO: ~200-400 MB (20-40%)"
echo ""

echo "✅ CHECKLIST COMPLETADO"
echo ""
