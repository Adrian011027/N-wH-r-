import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Producto, ProductoImagen

# Obtener el producto 18 (jejejejejej)
try:
    p = Producto.objects.get(id=18)
    print(f'✅ Producto encontrado: {p.nombre} (ID: {p.id})')
    
    # Verificar imágenes de galería
    imagenes = p.imagenes.all()
    print(f'\n📸 Imágenes de galería: {imagenes.count()}')
    
    for img in imagenes:
        print(f'  - Orden {img.orden}: {img.imagen.url}')
        print(f'    Path: {img.imagen.name}')
    
    if imagenes.count() == 0:
        print('  ⚠️ No hay imágenes asociadas')
        
        # Verificar si existen ProductoImagen sin asociar
        orfanos = ProductoImagen.objects.filter(producto__isnull=True)
        if orfanos.exists():
            print(f'\n⚠️ Encontradas {orfanos.count()} imágenes huérfanas')
    
except Producto.DoesNotExist:
    print('❌ Producto 18 no encontrado')
except Exception as e:
    print(f'❌ Error: {e}')
