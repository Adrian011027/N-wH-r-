"""
API endpoints para obtener opciones de filtros dinámicos
"""
from django.http import JsonResponse
from django.db.models import Min, Max, Count, Q
from ..models import Producto, Variante, Categoria, Subcategoria


def get_filtros_disponibles(request):
    """
    Retorna todas las opciones de filtros disponibles para una página de colección.
    GET /api/filtros-disponibles/?genero=Hombre&categoria=1
    """
    genero = request.GET.get('genero', '').strip()
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    
    # Mapeo de género (acepta versiones antiguas y nuevas)
    genero_map = {
        'HOMBRE': 'Hombre',
        'MUJER': 'Mujer',
        'UNISEX': 'Unisex',
        'DAMA': 'Mujer',
        'CABALLERO': 'Hombre',
        'H': 'Hombre',
        'M': 'Mujer',
        'U': 'Unisex',
        'Hombre': 'Hombre',
        'Mujer': 'Mujer',
        'Unisex': 'Unisex'
    }
    genero_filtro = genero_map.get(genero.upper() if genero else '', None)
    
    # Query base de productos
    productos_qs = Producto.objects.all()
    
    if genero_filtro:
        productos_qs = productos_qs.filter(genero__in=[genero_filtro, 'Unisex'])
    
    if categoria_id:
        try:
            productos_qs = productos_qs.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            pass
    
    if subcategoria_id:
        try:
            productos_qs = productos_qs.filter(subcategorias__id=int(subcategoria_id))
        except (ValueError, TypeError):
            pass
    
    # Solo productos con stock
    productos_qs = productos_qs.filter(variantes__stock__gt=0).distinct()
    
    # IDs de productos filtrados
    producto_ids = list(productos_qs.values_list('id', flat=True))
    
    # Obtener variantes con stock de estos productos
    variantes_qs = Variante.objects.filter(
        producto_id__in=producto_ids,
        stock__gt=0
    )
    
    # Obtener tallas únicas (ordenadas numéricamente si es posible)
    tallas_raw = variantes_qs.values_list('talla', flat=True).distinct()
    tallas = []
    for t in tallas_raw:
        if t and t not in ['UNICA', 'N/A', '']:
            tallas.append(t)
    
    # Intentar ordenar numéricamente
    def talla_sort_key(t):
        try:
            return (0, float(t))
        except (ValueError, TypeError):
            return (1, t)
    
    tallas = sorted(set(tallas), key=talla_sort_key)
    
    # Obtener colores únicos
    colores_raw = variantes_qs.exclude(
        Q(color__isnull=True) | Q(color='') | Q(color='N/A')
    ).values_list('color', flat=True).distinct()
    colores = sorted(set(colores_raw))
    
    # Obtener marcas únicas
    marcas_raw = productos_qs.exclude(
        Q(marca__isnull=True) | Q(marca='')
    ).values_list('marca', flat=True).distinct()
    marcas = sorted(set(marcas_raw))
    
    # Obtener rango de precios
    precio_range = productos_qs.aggregate(
        min_precio=Min('precio'),
        max_precio=Max('precio')
    )
    
    # Obtener categorías disponibles
    categorias = list(productos_qs.values(
        'categoria__id', 'categoria__nombre'
    ).annotate(
        count=Count('id', distinct=True)
    ).order_by('categoria__nombre'))
    
    categorias_list = [
        {
            'id': c['categoria__id'],
            'nombre': c['categoria__nombre'],
            'count': c['count']
        }
        for c in categorias if c['categoria__nombre']
    ]
    
    # Obtener subcategorías disponibles
    subcategorias = productos_qs.values(
        'subcategorias__id', 'subcategorias__nombre'
    ).annotate(
        count=Count('id', distinct=True)
    ).order_by('subcategorias__nombre')
    
    subcategorias_list = [
        {
            'id': s['subcategorias__id'],
            'nombre': s['subcategorias__nombre'],
            'count': s['count']
        }
        for s in subcategorias if s['subcategorias__nombre']
    ]
    
    # Contar productos en oferta
    productos_oferta = productos_qs.filter(en_oferta=True).count()
    
    return JsonResponse({
        'success': True,
        'filtros': {
            'tallas': tallas,
            'colores': colores,
            'marcas': marcas,
            'precio': {
                'min': float(precio_range['min_precio'] or 0),
                'max': float(precio_range['max_precio'] or 0)
            },
            'categorias': categorias_list,
            'subcategorias': subcategorias_list,
            'productos_oferta': productos_oferta,
            'total_productos': productos_qs.count()
        }
    })


def get_productos_filtrados(request):
    """
    Retorna productos filtrados según parámetros.
    GET /api/productos-filtrados/?genero=H&categoria=1&tallas=7,8&precio_min=500&...
    """
    # Parámetros de filtrado
    genero = request.GET.get('genero', '').upper()
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    tallas = request.GET.get('tallas', '').split(',') if request.GET.get('tallas') else []
    colores = request.GET.get('colores', '').split(',') if request.GET.get('colores') else []
    marcas = request.GET.get('marcas', '').split(',') if request.GET.get('marcas') else []
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    en_oferta = request.GET.get('en_oferta') == '1'
    solo_disponible = request.GET.get('disponible', '1') == '1'
    busqueda = request.GET.get('q', '').strip()
    
    # Ordenamiento
    orden = request.GET.get('orden', 'relevante')
    
    # Paginación
    pagina = int(request.GET.get('pagina', 1))
    por_pagina = int(request.GET.get('por_pagina', 24))
    
    # Mapeo de género (acepta versiones antiguas y nuevas)
    genero_map = {
        'HOMBRE': 'Hombre',
        'MUJER': 'Mujer',
        'UNISEX': 'Unisex',
        'DAMA': 'Mujer',
        'CABALLERO': 'Hombre',
        'H': 'Hombre',
        'M': 'Mujer',
        'U': 'Unisex',
        'HOMBRE': 'Hombre',
        'MUJER': 'Mujer',
        'UNISEX': 'Unisex'
    }
    genero_normalizado = genero_map.get(genero, None)
    
    # Query base
    qs = Producto.objects.select_related('categoria').prefetch_related(
        'subcategorias', 'imagenes', 'variantes'
    )
    
    # Filtro: Género
    if genero_normalizado:
        qs = qs.filter(genero__in=[genero_normalizado, 'Unisex'])
    
    # Filtro: Categoría
    if categoria_id:
        try:
            qs = qs.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            pass
    
    # Filtro: Subcategoría
    if subcategoria_id:
        try:
            qs = qs.filter(subcategorias__id=int(subcategoria_id))
        except (ValueError, TypeError):
            pass
    
    # Filtro: Tallas (productos que tienen variantes con esas tallas)
    if tallas:
        tallas_clean = [t.strip() for t in tallas if t.strip()]
        if tallas_clean:
            qs = qs.filter(variantes__talla__in=tallas_clean, variantes__stock__gt=0)
    
    # Filtro: Colores
    if colores:
        colores_clean = [c.strip() for c in colores if c.strip()]
        if colores_clean:
            qs = qs.filter(variantes__color__in=colores_clean, variantes__stock__gt=0)
    
    # Filtro: Marcas
    if marcas:
        marcas_clean = [m.strip() for m in marcas if m.strip()]
        if marcas_clean:
            qs = qs.filter(marca__in=marcas_clean)
    
    # Filtro: Precio
    if precio_min:
        try:
            qs = qs.filter(precio__gte=float(precio_min))
        except (ValueError, TypeError):
            pass
    
    if precio_max:
        try:
            qs = qs.filter(precio__lte=float(precio_max))
        except (ValueError, TypeError):
            pass
    
    # Filtro: En oferta
    if en_oferta:
        qs = qs.filter(en_oferta=True)
    
    # Filtro: Solo disponibles (con stock)
    if solo_disponible:
        qs = qs.filter(variantes__stock__gt=0)
    
    # Búsqueda por nombre
    if busqueda:
        qs = qs.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(marca__icontains=busqueda)
        )
    
    # Eliminar duplicados
    qs = qs.distinct()
    
    # Ordenamiento
    orden_map = {
        'precio_asc': 'precio',
        'precio_desc': '-precio',
        'nuevo': '-created_at',
        'nombre': 'nombre',
        'relevante': '-created_at'  # Por defecto, más nuevos primero
    }
    qs = qs.order_by(orden_map.get(orden, '-created_at'))
    
    # Contar total antes de paginar
    total_productos = qs.count()
    
    # Paginación
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    productos_pagina = qs[inicio:fin]
    
    # Serializar productos
    productos_data = []
    for p in productos_pagina:
        variante_principal = p.variante_principal
        if variante_principal:
            primera_img = variante_principal.imagenes.all().order_by('orden').first()
            imagen_url = primera_img.imagen.url if primera_img else None
        else:
            imagen_url = None
        
        # Verificar si tiene stock
        tiene_stock = p.variantes.filter(stock__gt=0).exists()
        
        productos_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': float(p.precio),
            'imagen': imagen_url,
            'categoria': p.categoria.nombre if p.categoria else None,
            'marca': p.marca,
            'en_oferta': p.en_oferta,
            'tiene_stock': tiene_stock
        })
    
    # Calcular paginación
    total_paginas = (total_productos + por_pagina - 1) // por_pagina
    
    return JsonResponse({
        'success': True,
        'productos': productos_data,
        'paginacion': {
            'pagina_actual': pagina,
            'total_paginas': total_paginas,
            'total_productos': total_productos,
            'por_pagina': por_pagina,
            'tiene_anterior': pagina > 1,
            'tiene_siguiente': pagina < total_paginas
        }
    })
