import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.views.products import get_all_products
from django.http import HttpRequest

# Create a mock request
request = HttpRequest()
request.method = 'GET'

# Get the response
response = get_all_products(request)
data = json.loads(response.content)

print(f"Total productos: {len(data)}")

# Find product 18
encontrado = False
for p in data:
    if p['id'] == 18:
        encontrado = True
        print(f"\n✅ Producto {p['id']}: {p['nombre']}")
        print(f"📸 Imagen principal: {p['imagen']}")
        print(f"🖼️  Galería ({len(p['imagenes'])} imágenes):")
        for img in p['imagenes']:
            print(f"   - {img}")
        break

if not encontrado:
    print(f"\n⚠️ Producto 18 no encontrado en {len(data)} productos")
