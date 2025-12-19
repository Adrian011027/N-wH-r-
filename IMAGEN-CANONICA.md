# Sistema de Nombres Canónicos para Imágenes en S3

## Objetivo
Evitar solapaciones de nombres de imágenes y mantener una estructura clara y predecible en S3.

## Estructura de Nombres

### Imágenes de Productos
```
productos/prod-{id}-{slug-nombre}.{ext}

Ejemplos:
- productos/prod-42-nike-air-force.jpg
- productos/prod-5-bolsa-roja-diesel.png
- productos/prod-100-playera-blanca-adidas.jpg
```

**Formato:**
- `prod-{id}`: ID único del producto
- `{slug-nombre}`: Nombre del producto en slug (lowercase, sin caracteres especiales, máximo 50 caracteres)
- Garantiza: No hay duplicados porque cada producto tiene ID único

---

### Imágenes de Variantes
```
variantes/var-{producto_id}-{variante_id}-{talla}-{color}-{slug-nombre}.{ext}

Ejemplos:
- variantes/var-42-156-38-negro-nike-air-force.jpg
- variantes/var-42-157-40-blanco-nike-air-force.jpg
- variantes/var-5-23-unique-rojo-bolsa-diesel.jpg
```

**Formato:**
- `var-{producto_id}`: ID del producto padre
- `{variante_id}`: ID único de la variante
- `{talla}`: Talla (slugificada, máximo 10 caracteres)
- `{color}`: Color (slugificada, máximo 10 caracteres)
- `{slug-nombre}`: Nombre del producto padre (máximo 30 caracteres)

**Garantiza:**
- No hay duplicados porque cada variante tiene ID único
- Fácil encontrar todas las imágenes de un producto: `variantes/var-42-*`
- Fácil identificar la variante específica: talla y color están en el nombre
- Descriptivo y legible para humanos

---

## Implementación en Django

### En el Modelo Producto
```python
def _generate_image_key(self, filename):
    """Genera clave canónica: productos/prod-{id}-{slug}.{ext}"""
    if not self.id:
        return f'productos/{filename}'
    
    ext = os.path.splitext(filename)[1].lower()
    slug = slugify(self.nombre)[:50]
    return f'productos/prod-{self.id}-{slug}{ext}'
```

### En el Modelo Variante
```python
def _generate_image_key(self, filename):
    """Genera clave canónica: variantes/var-{prod_id}-{var_id}-{talla}-{color}-{slug}.{ext}"""
    if not self.id:
        return f'variantes/{filename}'
    
    ext = os.path.splitext(filename)[1].lower()
    producto_slug = slugify(self.producto.nombre)[:30]
    talla_clean = slugify(self.talla or "unica")[:10]
    color_clean = slugify(self.color or "na")[:10]
    
    return f'variantes/var-{self.producto_id}-{self.id}-{talla_clean}-{color_clean}-{producto_slug}{ext}'
```

### En las Vistas
```python
# Crear/Actualizar Producto
if 'imagen' in request.FILES:
    imagen_file = request.FILES['imagen']
    nombre_canonico = producto._generate_image_key(imagen_file.name)
    imagen_file.name = nombre_canonico
    producto.imagen = imagen_file

# Crear/Actualizar Variante
if 'imagen' in request.FILES:
    imagen_file = request.FILES['imagen']
    nombre_canonico = variante._generate_image_key(imagen_file.name)
    imagen_file.name = nombre_canonico
    variante.imagen = imagen_file
```

---

## URLs de Acceso en S3

Con `USE_S3=True` en `.env`:

### Imagen de Producto
```
https://tu-bucket.s3.us-east-1.amazonaws.com/media/productos/prod-42-nike-air-force.jpg
```

### Imagen de Variante
```
https://tu-bucket.s3.us-east-1.amazonaws.com/media/variantes/var-42-156-38-negro-nike-air-force.jpg
```

---

## Serialización en APIs

### Producto Completo (get_all_products)
```json
{
  "id": 42,
  "nombre": "Nike Air Force",
  "imagen": "https://bucket.s3.../media/productos/prod-42-nike-air-force.jpg",
  "variantes": [
    {
      "id": 156,
      "talla": "38",
      "color": "Negro",
      "imagen": "https://bucket.s3.../media/variantes/var-42-156-38-negro-nike-air-force.jpg",
      "stock": 5
    }
  ]
}
```

---

## Fallback de Imágenes

Si una variante no tiene imagen propia, se usa la del producto:
```python
def obtener_imagen_variante(variante):
    if variante.imagen:
        return variante.imagen.url
    elif variante.producto.imagen:
        return variante.producto.imagen.url
    return None
```

---

## Ventajas de Este Sistema

✅ **No hay solapaciones**: Cada imagen tiene identificadores únicos
✅ **Descriptivo**: El nombre te dice qué es la imagen
✅ **Escalable**: Funciona con millones de productos y variantes
✅ **S3-friendly**: Fácil de buscar y listar en S3 Console
✅ **Caché-friendly**: Nombres consistentes y predecibles
✅ **Reversible**: Puedes extraer el ID del producto/variante del nombre

---

## Ejemplos de Estructura en S3

```
mi-bucket/
├── media/
│   ├── productos/
│   │   ├── prod-1-playera-blanca-adidas.jpg
│   │   ├── prod-1-playera-blanca-adidas-2.png
│   │   ├── prod-42-nike-air-force.jpg
│   │   ├── prod-100-bolsa-roja-diesel.jpg
│   │   └── ...
│   ├── variantes/
│   │   ├── var-42-156-38-negro-nike-air-force.jpg
│   │   ├── var-42-157-40-blanco-nike-air-force.jpg
│   │   ├── var-42-158-42-gris-nike-air-force.jpg
│   │   ├── var-1-5-s-blanco-playera-blanca-adidas.jpg
│   │   ├── var-1-6-m-blanco-playera-blanca-adidas.jpg
│   │   ├── var-1-7-l-blanco-playera-blanca-adidas.jpg
│   │   └── ...
│   └── static/
│       ├── css/
│       └── js/
└── ...
```

