#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Producto

print("\n=== REVISANDO PRODUCTOS ===\n")
for p in Producto.objects.all()[:10]:
    galeria = [img.imagen.url for img in p.imagenes.all().order_by('orden') if img.imagen]
    print(f"ID {p.id}: {p.nombre}")
    print(f"  Galería: {len(galeria)} imágenes")
    if galeria:
        print(f"  ✓ Primera imagen: ...{galeria[0][-50:]}")
    else:
        print(f"  ✗ SIN GALERÍA")
    print()
