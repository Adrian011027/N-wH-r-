"""
Test de conexión AWS S3 para Nowhere E-commerce
Ejecutar: python test_s3_connection.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

def test_s3_connection():
    print("=" * 60)
    print("🧪 TEST DE CONEXIÓN AWS S3")
    print("=" * 60)
    
    # 1. Verificar configuración
    print("\n📋 1. Verificando configuración...")
    print(f"   USE_S3: {settings.USE_S3}")
    
    if settings.USE_S3:
        print(f"   ✅ AWS_STORAGE_BUCKET_NAME: {settings.AWS_STORAGE_BUCKET_NAME}")
        print(f"   ✅ AWS_S3_REGION_NAME: {settings.AWS_S3_REGION_NAME}")
        print(f"   ✅ AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID[:8]}...") 
    else:
        print("   ⚠️  S3 está desactivado (USE_S3=False)")
        print("   📂 Usando almacenamiento local")
        return
    
    # 2. Test de escritura
    print("\n📤 2. Test de escritura en S3...")
    try:
        test_content = ContentFile(b'Test de conexion S3 desde Django - Nowhere E-commerce')
        filename = default_storage.save('test/test_connection.txt', test_content)
        file_url = default_storage.url(filename)
        print(f"   ✅ Archivo subido exitosamente!")
        print(f"   📍 Ruta: {filename}")
        print(f"   🔗 URL: {file_url}")
    except Exception as e:
        print(f"   ❌ ERROR al subir archivo: {str(e)}")
        return
    
    # 3. Test de lectura
    print("\n📥 3. Test de lectura desde S3...")
    try:
        if default_storage.exists(filename):
            print(f"   ✅ Archivo encontrado en S3")
            file_size = default_storage.size(filename)
            print(f"   📊 Tamaño: {file_size} bytes")
        else:
            print(f"   ❌ ERROR: Archivo no encontrado")
            return
    except Exception as e:
        print(f"   ❌ ERROR al leer archivo: {str(e)}")
        return
    
    # 4. Test de eliminación
    print("\n🗑️  4. Test de eliminación...")
    try:
        default_storage.delete(filename)
        print(f"   ✅ Archivo eliminado correctamente")
    except Exception as e:
        print(f"   ❌ ERROR al eliminar archivo: {str(e)}")
        return
    
    # 5. Verificar estructura de carpetas
    print("\n📁 5. Estructura de carpetas configurada:")
    print(f"   • Categorías: media/categorias/")
    print(f"   • Productos: media/productos/")
    print(f"   • Galería: media/productos/galeria/")
    print(f"   • Variantes: media/variantes/")
    
    print("\n" + "=" * 60)
    print("✅ ¡CONEXIÓN S3 EXITOSA!")
    print("=" * 60)
    print("\n💡 Próximos pasos:")
    print("   1. Crear un producto con imagen desde el dashboard")
    print("   2. Verificar que la imagen se suba a S3")
    print("   3. Confirmar que la URL sea accesible públicamente")
    print("\n")

if __name__ == "__main__":
    try:
        test_s3_connection()
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
