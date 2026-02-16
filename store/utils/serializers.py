"""
Utilidades para serializar productos y variantes con URLs canónicas de imágenes.
Sistema: 1 variante = 1 color, con tallas_stock JSONField {"talla": stock}
"""

def serializar_producto_completo(producto):
    """
    Serializa un producto con todas sus variantes e imágenes.
    Cada variante es 1 color con múltiples tallas en tallas_stock.
    """
    variantes = []
    for v in producto.variantes.all():
        # Obtener imágenes de galería
        imagenes = [img.imagen.url for img in v.imagenes.all().order_by('orden') if img.imagen]
        variantes.append({
            'id': v.id,
            'sku': v.sku,
            'color': v.color,
            'tallas_stock': v.tallas_stock or {},
            'otros': v.otros,
            'imagen': imagenes[0] if imagenes else (v.imagen.url if v.imagen else None),
            'imagenes': imagenes,
            'precio': float(v.precio or producto.precio),
            'precio_mayorista': float(v.precio_mayorista or producto.precio_mayorista),
            'stock_total': v.stock_total_variante,
        })

    # Imagen principal desde variante principal
    variante_principal = producto.variante_principal
    galeria = []
    if variante_principal:
        galeria = [img.imagen.url for img in variante_principal.imagenes.all().order_by('orden') if img.imagen]

    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'categoria': producto.categoria.nombre,
        'genero': producto.genero,
        'en_oferta': producto.en_oferta,
        'imagen': galeria[0] if galeria else None,
        'imagenes': galeria,
        'precio': float(producto.precio),
        'precio_mayorista': float(producto.precio_mayorista),
        'stock_total': producto.stock_total,
        'variantes': variantes,
    }


def serializar_variante_con_imagen(variante):
    """
    Serializa una variante individual con su imagen.
    """
    imagenes = [img.imagen.url for img in variante.imagenes.all().order_by('orden') if img.imagen]
    return {
        'id': variante.id,
        'producto_id': variante.producto.id,
        'producto_nombre': variante.producto.nombre,
        'sku': variante.sku,
        'color': variante.color,
        'tallas_stock': variante.tallas_stock or {},
        'otros': variante.otros,
        'imagen': imagenes[0] if imagenes else (variante.imagen.url if variante.imagen else None),
        'imagenes': imagenes,
        'precio': float(variante.precio or variante.producto.precio),
        'precio_mayorista': float(variante.precio_mayorista or variante.producto.precio_mayorista),
        'stock_total': variante.stock_total_variante,
    }


def obtener_imagen_variante(variante):
    """
    Obtiene la primera imagen de galería de la variante.
    Si no tiene galería, intenta la imagen directa.
    """
    primera_img = variante.imagenes.all().order_by('orden').first()
    if primera_img and primera_img.imagen:
        return primera_img.imagen.url
    if variante.imagen:
        return variante.imagen.url
    return None
