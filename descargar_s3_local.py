#!/usr/bin/env python3
"""
Script para descargar S3 → Local
Sincroniza media/ y static/ de S3 a tu máquina

Uso:
    python descargar_s3_local.py
    
Resultado:
    Todos los archivos de S3 se descargan a:
    - /N-WH-R-/media/
    - /N-WH-R-/static/
"""

import os
import sys
from pathlib import Path

# =====================================================
# CARGAR VARIABLES .ENV MANUALMENTE
# =====================================================

env_file = Path(__file__).resolve().parent / '.env'

if not env_file.exists():
    print("❌ No se encontró el archivo .env")
    print(f"   Esperado en: {env_file}")
    sys.exit(1)

# Leer .env y cargar en os.environ
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        # Saltar comentarios y líneas vacías
        if not line or line.startswith('#'):
            continue
        # Saltar líneas sin '='
        if '=' not in line:
            continue
        # Parsear KEY=VALUE
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        # Remover comillas si existen
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        # Cargar en os.environ
        os.environ[key] = value

# =====================================================
# CONFIGURACIÓN
# =====================================================

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'nowhere-store')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-2')

# Validar credenciales
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    print("❌ Falta configuración de AWS en .env")
    print("   Necesita: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    sys.exit(1)

# Importar boto3
import boto3
from botocore.exceptions import ClientError

# Rutas locales
BASE_DIR = Path(__file__).resolve().parent
LOCAL_MEDIA_DIR = BASE_DIR / 'media'
LOCAL_STATIC_DIR = BASE_DIR / 'static'

# Crear directorios si no existen
LOCAL_MEDIA_DIR.mkdir(exist_ok=True)
LOCAL_STATIC_DIR.mkdir(exist_ok=True)

# Inicializar cliente S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME
)

# =====================================================
# FUNCIONES
# =====================================================

def download_s3_folder(bucket, s3_prefix, local_dir):
    """
    Descarga una carpeta completa de S3 a local
    
    Args:
        bucket: Nombre del bucket
        s3_prefix: Prefijo en S3 (ej: 'media/', 'static/')
        local_dir: Ruta local donde guardar
    """
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=s3_prefix)
        
        file_count = 0
        
        for page in pages:
            if 'Contents' not in page:
                print(f"✓ {s3_prefix} está vacío")
                return 0
            
            for obj in page['Contents']:
                key = obj['Key']
                
                # Saltar si es un "directorio" (termina en /)
                if key.endswith('/'):
                    continue
                
                # Calcular ruta local
                relative_path = key[len(s3_prefix):]
                local_file = local_dir / relative_path
                
                # Crear subdirectorios si es necesario
                local_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Descargar archivo
                try:
                    print(f"  ↓ Descargando: {key}")
                    s3_client.download_file(bucket, key, str(local_file))
                    file_count += 1
                except ClientError as e:
                    print(f"  ✗ Error descargando {key}: {e}")
        
        return file_count
    
    except Exception as e:
        print(f"✗ Error en {s3_prefix}: {e}")
        return 0

def get_s3_stats(bucket, prefix):
    """Obtiene estadísticas de una carpeta en S3"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            return 0, 0
        
        total_files = len([obj for obj in response['Contents'] if not obj['Key'].endswith('/')])
        total_size = sum(obj['Size'] for obj in response['Contents'])
        
        return total_files, total_size
    except Exception as e:
        print(f"Error obteniendo stats: {e}")
        return 0, 0

# =====================================================
# MAIN
# =====================================================

def main():
    print("=" * 70)
    print("📥 DESCARGADOR S3 → LOCAL")
    print("=" * 70)
    print(f"\n🪣 Bucket: {AWS_STORAGE_BUCKET_NAME}")
    print(f"📂 Destino Media: {LOCAL_MEDIA_DIR}")
    print(f"📂 Destino Static: {LOCAL_STATIC_DIR}")
    print("\n" + "=" * 70)
    
    # Estadísticas antes de descargar
    print("\n📊 Estadísticas en S3:")
    
    media_files, media_size = get_s3_stats(AWS_STORAGE_BUCKET_NAME, 'media/')
    static_files, static_size = get_s3_stats(AWS_STORAGE_BUCKET_NAME, 'static/')
    
    print(f"\n  📦 media/")
    print(f"     - Archivos: {media_files}")
    print(f"     - Tamaño total: {media_size / (1024*1024):.2f} MB")
    
    print(f"\n  📦 static/")
    print(f"     - Archivos: {static_files}")
    print(f"     - Tamaño total: {static_size / (1024*1024):.2f} MB")
    
    total_files = media_files + static_files
    total_size_mb = (media_size + static_size) / (1024*1024)
    
    print(f"\n  ✓ Total: {total_files} archivos ({total_size_mb:.2f} MB)")
    
    # Confirmación
    print("\n" + "=" * 70)
    respuesta = input("\n¿Descargar ahora? (s/n): ").strip().lower()
    
    if respuesta != 's':
        print("❌ Descarga cancelada")
        return
    
    print("\n" + "=" * 70)
    print("⏳ Iniciando descarga...\n")
    
    # Descargar media/
    print("📥 Descargando media/...")
    media_downloaded = download_s3_folder(
        AWS_STORAGE_BUCKET_NAME, 
        'media/', 
        LOCAL_MEDIA_DIR
    )
    
    # Descargar static/
    print(f"\n📥 Descargando static/...")
    static_downloaded = download_s3_folder(
        AWS_STORAGE_BUCKET_NAME,
        'static/',
        LOCAL_STATIC_DIR
    )
    
    # Resumen
    print("\n" + "=" * 70)
    print("✅ DESCARGA COMPLETADA")
    print("=" * 70)
    print(f"\n  ✓ media/: {media_downloaded} archivos descargados")
    print(f"  ✓ static/: {static_downloaded} archivos descargados")
    print(f"  ✓ Total: {media_downloaded + static_downloaded} archivos")
    
    print(f"\n  📂 {LOCAL_MEDIA_DIR}")
    print(f"  📂 {LOCAL_STATIC_DIR}")
    
    print("\n" + "=" * 70)
    print("\n💡 Próximos pasos:")
    print("   1. Abre .env y asegúrate que USE_S3=False")
    print("   2. Reinicia Django (runserver)")
    print("   3. Las imágenes ahora se cargarán localmente")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
