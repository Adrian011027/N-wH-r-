import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Producto, ProductoImagen

# Get product 14
p = Producto.objects.get(id=14)
print(f'Producto: {p.nombre}')
print(f'Imagen principal: {p.imagen.url if p.imagen else "No tiene"}')
print(f'\nImágenes de galería:')
imagenes = p.imagenes.all()
print(f'Total: {imagenes.count()}')
for img in imagenes:
    print(f'  - {img.imagen.url}')

# Also test the API response
print('\n' + '='*50)
print('API Response Check:')
print('='*50)

from store.views.products import get_all_products
from django.http import HttpRequest

request = HttpRequest()
response = get_all_products(request)
import json
data = json.loads(response.content)

for producto in data:
    if producto['id'] == 14:
        print(f"\nProducto ID 14 en API:")
        print(f"  imagen: {producto['imagen']}")
        print(f"  imagenes: {producto['imagenes']}")
        print(f"  imagenes type: {type(producto['imagenes'])}")
        print(f"  imagenes len: {len(producto['imagenes'])}")
