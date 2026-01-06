import os
import django
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Producto, ProductoImagen, Categoria

# Create a test image
img = Image.new('RGB', (100, 100), color='red')
img_io = BytesIO()
img.save(img_io, format='PNG')
img_io.seek(0)

test_image = SimpleUploadedFile(
    "test_gallery.png",
    img_io.getvalue(),
    content_type="image/png"
)

# Get or create category
cat, _ = Categoria.objects.get_or_create(nombre="Test", defaults={'slug': 'test'})

# Create product
prod = Producto.objects.create(
    nombre="Producto con Galería",
    categoria=cat,
    genero='H',
    descripcion="Test product with gallery",
    precio=100.00
)
print(f'✅ Producto creado: {prod.id} - {prod.nombre}')

# Create gallery images
for i in range(3):
    img = Image.new('RGB', (100, 100), color=('blue' if i % 2 == 0 else 'green'))
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    img_file = SimpleUploadedFile(
        f"gallery_{i}.png",
        img_io.getvalue(),
        content_type="image/png"
    )
    
    prod_img = ProductoImagen(producto=prod, imagen=img_file, orden=i+1)
    # Generate canonical name
    canonical_name = prod_img._generate_image_key(img_file.name, i+1)
    img_file.name = canonical_name
    prod_img.imagen = img_file
    prod_img.save()
    print(f'  ✓ Imagen {i+1} guardada: {prod_img.imagen.url}')

# Now check the API response
print('\n' + '='*60)
print('Verificando respuesta de API:')
print('='*60)

from django.http import HttpRequest
from store.views.products import get_all_products
import json

request = HttpRequest()
request.method = 'GET'
response = get_all_products(request)
data = json.loads(response.content)

for p in data:
    if p['id'] == prod.id:
        print(f"\n📦 Producto API Response:")
        print(f"  ID: {p['id']}")
        print(f"  Nombre: {p['nombre']}")
        print(f"  Imagen principal: {p['imagen']}")
        print(f"  Galería imagenes ({len(p['imagenes'])}): {p['imagenes']}")
        break
