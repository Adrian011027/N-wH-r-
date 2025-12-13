#!/bin/bash
# =========================================
# Script para recopilar archivos estáticos a S3
# Uso: bash collectstatic-s3.sh
# =========================================

# Variables
APP_DIR="/home/ec2-user/N-wH-r-"
VENV_DIR="$APP_DIR/venv"

echo "📦 Recopilando archivos estáticos a S3..."
cd "$APP_DIR"
source "$VENV_DIR/bin/activate"

python manage.py collectstatic --noinput

echo "✅ Archivos estáticos recopilados en S3"
