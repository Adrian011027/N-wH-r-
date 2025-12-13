"""
Utilidades para serializar productos y variantes con URLs canónicas de imágenes
"""

def serializar_producto_completo(producto):
    """
    Serializa un producto con todas sus variantes e imágenes
    
    Formato:
    {
        "id": 42,
        "nombre": "Nike Air Force",
        "descripcion": "...",
        "categoria": "Zapatos",
        "genero": "U",
        "precio": 150.00,
        "precio_mayorista": 100.00,
        "en_oferta": false,
        "imagen": "https://bucket.s3.us-east-1.amazonaws.com/media/productos/prod-42-nike-air-force.jpg",
        "variantes": [
            {
                "id": 156,
                "sku": "NIKE-AIR-38-BLK",
                "talla": "38",
                "color": "Negro",
                "imagen": "https://bucket.s3.us-east-1.amazonaws.com/media/variantes/var-42-156-38-negro-nike-air-force.jpg",
                "precio": 150.00,
                "precio_mayorista": 100.00,
                "stock": 5
            },
            ...
        ]
    }
    """
    variantes = []
    for v in producto.variantes.all():
        variantes.append({
            'id': v.id,
            'sku': v.sku,
            'talla': v.talla,
            'color': v.color,
            'otros': v.otros,
            'imagen': v.imagen.url if v.imagen else None,  # URL de S3 automática
            'precio': float(v.precio or producto.precio),
            'precio_mayorista': float(v.precio_mayorista or producto.precio_mayorista),
            'stock': v.stock,
        })

    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'categoria': producto.categoria.nombre,
        'genero': producto.genero,
        'en_oferta': producto.en_oferta,
        'imagen': producto.imagen.url if producto.imagen else None,  # URL de S3 automática
        'precio': float(producto.precio),
        'precio_mayorista': float(producto.precio_mayorista),
        'stock_total': producto.stock_total,
        'variantes': variantes,
    }


def serializar_variante_con_imagen(variante):
    """
    Serializa una variante individual con su imagen
    """
    return {
        'id': variante.id,
        'producto_id': variante.producto.id,
        'producto_nombre': variante.producto.nombre,
        'sku': variante.sku,
        'talla': variante.talla,
        'color': variante.color,
        'otros': variante.otros,
        'imagen': variante.imagen.url if variante.imagen else variante.producto.imagen.url if variante.producto.imagen else None,
        'precio': float(variante.precio or variante.producto.precio),
        'precio_mayorista': float(variante.precio_mayorista or variante.producto.precio_mayorista),
        'stock': variante.stock,
    }


def obtener_imagen_variante(variante):
    """
    Obtiene la imagen de la variante.
    Si no tiene, devuelve la imagen del producto.
    Si tampoco, devuelve None.
    """
    if variante.imagen:
        return variante.imagen.url
    elif variante.producto.imagen:
        return variante.producto.imagen.url
    return None
