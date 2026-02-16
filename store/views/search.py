"""
Vista de búsqueda y filtrado de productos
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q, Min, Max, Prefetch, Count
from ..models import Producto, Categoria, Variante, Subcategoria
from decimal import Decimal, InvalidOperation
import json


@require_GET
def search_products(request):
    """
    API endpoint para búsqueda y filtrado de productos con soporte avanzado de filtros.
    
    Parámetros GET:
    - q: Término de búsqueda (nombre o descripción)
    - categoria: ID o nombre de categoría
    - subcategoria: ID o nombre de subcategoría
    - marca: Marca del producto
    - genero: M, H, Unisex (heredado - preferir subcategoria)
    - precio_min: Precio mínimo
    - precio_max: Precio máximo
    - en_oferta: true/false
    - tallas: Lista de tallas separadas por coma (ej: 25,26,27)
    - colores: Lista de colores separados por coma (ej: Negro,Blanco,Rojo)
    - ordenar: precio_asc, precio_desc, nombre_asc, nombre_desc, nuevo, popular
    - page: Número de página (opcional)
    - per_page: Productos por página (default: 20)
    """
    
    # Iniciar queryset con prefetch para optimizar
    productos = Producto.objects.prefetch_related(
        Prefetch('variantes', queryset=Variante.objects.prefetch_related('imagenes')),
        'categoria',
        'subcategorias'
    ).distinct()
    
    # ============ FILTRO: Término de búsqueda ============
    q = request.GET.get('q', '').strip()
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | 
            Q(descripcion__icontains=q) |
            Q(marca__icontains=q)
        )
    
    # ============ FILTRO: Categoría ============
    categoria = request.GET.get('categoria', '').strip()
    if categoria:
        try:
            # Intentar buscar por ID primero
            cat_id = int(categoria)
            productos = productos.filter(categoria_id=cat_id)
        except ValueError:
            # Si no es número, buscar por nombre
            productos = productos.filter(categoria__nombre__iexact=categoria)
    
    # ============ FILTRO: Subcategoría (nuevo sistema - ManyToMany) ============
    subcategoria = request.GET.get('subcategoria', '').strip()
    if subcategoria:
        try:
            # Intentar buscar por ID primero
            subcat_id = int(subcategoria)
            productos = productos.filter(subcategorias__id=subcat_id)
        except ValueError:
            # Si no es número, buscar por nombre
            productos = productos.filter(subcategorias__nombre__iexact=subcategoria)
    
    # ============ FILTRO: Marca (nuevo) ============
    marca = request.GET.get('marca', '').strip()
    if marca:
        productos = productos.filter(marca__iexact=marca)
    
    # ============ FILTRO: Género ============
    genero = request.GET.get('genero', '').strip()
    if genero:
        # Mapeo de género (acepta versiones antiguas y nuevas)
        genero_map = {
            'HOMBRE': 'Hombre',
            'MUJER': 'Mujer',
            'UNISEX': 'Unisex',
            'DAMA': 'Mujer',
            'CABALLERO': 'Hombre',
            'H': 'Hombre',
            'M': 'Mujer',
            'U': 'Unisex'
        }
        genero_normalizado = genero_map.get(genero.upper(), None)
        if genero_normalizado:
            productos = productos.filter(Q(genero=genero_normalizado) | Q(genero='Unisex'))
    
    # ============ FILTRO: Precio ============
    precio_min = request.GET.get('precio_min', '').strip()
    precio_max = request.GET.get('precio_max', '').strip()
    
    if precio_min:
        try:
            productos = productos.filter(precio__gte=Decimal(precio_min))
        except (ValueError, TypeError, InvalidOperation):
            pass
    
    if precio_max:
        try:
            productos = productos.filter(precio__lte=Decimal(precio_max))
        except (ValueError, TypeError, InvalidOperation):
            pass
    
    # ============ FILTRO: En oferta ============
    en_oferta = request.GET.get('en_oferta', '').strip().lower()
    if en_oferta == 'true':
        productos = productos.filter(en_oferta=True)
    
    # ============ FILTRO: Tallas disponibles ============
    tallas = request.GET.get('tallas', '').strip()
    tallas_filter_list = []
    if tallas:
        tallas_filter_list = [t.strip() for t in tallas.split(',') if t.strip()]
    
    # ============ FILTRO: Colores disponibles (nuevo) ============
    colores = request.GET.get('colores', '').strip()
    colores_filter_list = []
    if colores:
        colores_filter_list = [c.strip() for c in colores.split(',') if c.strip()]
        if colores_filter_list:
            productos = productos.filter(
                variantes__color__in=colores_filter_list
            ).distinct()
    
    # ============ FILTRO: Solo con stock (se aplica post-query) ============
    solo_disponibles = request.GET.get('disponibles', 'true').strip().lower()
    
    # ============ ORDENAMIENTO ============
    ordenar = request.GET.get('ordenar', 'nuevo').strip()
    
    if ordenar == 'precio_asc':
        productos = productos.order_by('precio')
    elif ordenar == 'precio_desc':
        productos = productos.order_by('-precio')
    elif ordenar == 'nombre_asc':
        productos = productos.order_by('nombre')
    elif ordenar == 'nombre_desc':
        productos = productos.order_by('-nombre')
    elif ordenar == 'nuevo':
        productos = productos.order_by('-created_at')
    elif ordenar == 'popular':
        productos = productos.order_by('-id')
    
    # ============ PAGINACIÓN ============
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
    except (ValueError, TypeError):
        page = 1
        per_page = 20
    
    total = productos.count()
    start = (page - 1) * per_page
    end = start + per_page
    productos_pagina = productos[start:end]
    
    # ============ SERIALIZAR RESPUESTA ============
    data = []
    for p in productos_pagina:
        # Obtener tallas y colores disponibles
        tallas_disponibles = set()
        colores_disponibles = set()
        variantes_data = []
        tiene_stock = False
        
        for v in p.variantes.all():
            if v.stock_total_variante > 0:
                tiene_stock = True
                for talla_key, stock_val in v.tallas_stock.items():
                    if stock_val > 0:
                        tallas_disponibles.add(talla_key)
                if v.color:
                    colores_disponibles.add(v.color)
                
                variantes_data.append({
                    'id': v.id,
                    'color': v.color,
                    'otros': v.otros,
                    'precio': float(v.precio or p.precio),
                    'tallas_stock': v.tallas_stock,
                    'stock_total': v.stock_total_variante,
                })
        
        # Filtrar por tallas si se solicitó
        if tallas_filter_list:
            if not tallas_disponibles.intersection(set(tallas_filter_list)):
                continue
        
        # Filtrar por stock
        if solo_disponibles != 'false' and not tiene_stock:
            continue
        
        # Galería de imágenes de la variante principal
        variante_principal = p.variante_principal
        galeria = []
        if variante_principal:
            galeria = [img.imagen.url for img in variante_principal.imagenes.all() if img.imagen]
        
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': float(p.precio),
            'precio_mayorista': float(p.precio_mayorista),
            'categoria': p.categoria.nombre,
            'categoria_id': p.categoria.id,
            'subcategorias': [{'id': s.id, 'nombre': s.nombre} for s in p.subcategorias.all()],
            'marca': p.marca,
            'genero': p.genero,
            'en_oferta': p.en_oferta,
            'imagen': galeria[0] if galeria else '',
            'imagenes_galeria': galeria,
            'tallas_disponibles': sorted(list(tallas_disponibles), key=lambda x: (float(x) if x.replace('.','').isdigit() else float('inf'), x)),
            'colores_disponibles': sorted(list(colores_disponibles)),
            'stock_total': sum(v['stock_total'] for v in variantes_data),
            'variantes': variantes_data,
        })
    
    # ============ METADATA ============
    response = {
        'productos': data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'has_next': end < total,
        'has_prev': page > 1,
    }
    
    return JsonResponse(response, safe=False)


@require_GET
def get_filter_options(request):
    """
    Obtiene las opciones disponibles para filtros avanzados.
    
    Parámetros GET:
    - categoria_id: (opcional) Limitar subcategorías y marcas a esta categoría
    """
    
    # Categorías
    categorias = list(Categoria.objects.all().values('id', 'nombre'))
    
    # Filtrar por categoría si se especifica
    categoria_id = request.GET.get('categoria_id', '').strip()
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            subcategorias_qs = Subcategoria.objects.filter(categoria_id=categoria_id, activa=True)
            productos_qs = Producto.objects.filter(categoria_id=categoria_id)
        except ValueError:
            subcategorias_qs = Subcategoria.objects.filter(activa=True)
            productos_qs = Producto.objects.all()
    else:
        subcategorias_qs = Subcategoria.objects.filter(activa=True)
        productos_qs = Producto.objects.all()
    
    # Subcategorías
    subcategorias = list(subcategorias_qs.values('id', 'nombre', 'categoria_id'))
    
    # Rango de precios
    precios = productos_qs.aggregate(
        min_precio=Min('precio'),
        max_precio=Max('precio')
    )
    
    # Tallas disponibles (extraer de JSONField tallas_stock)
    variantes_con_stock = Variante.objects.filter(producto__in=productos_qs)
    tallas_set = set()
    for v in variantes_con_stock:
        for talla_key, stock_val in v.tallas_stock.items():
            if stock_val > 0 and talla_key not in ('UNICA', 'N/A', ''):
                tallas_set.add(talla_key)
    
    tallas = sorted(
        list(tallas_set),
        key=lambda x: (float(x) if x.replace('.','').isdigit() else float('inf'), x)
    )
    
    # Colores disponibles
    colores_queryset = Variante.objects.filter(
        producto__in=productos_qs
    ).exclude(color='').values_list('color', flat=True).distinct()
    # Solo incluir variantes con stock > 0
    colores_set = set()
    for v in variantes_con_stock:
        if v.stock_total_variante > 0 and v.color and v.color != 'N/A':
            colores_set.add(v.color)
    colores = sorted(list(colores_set))
    
    # Marcas
    marcas_queryset = productos_qs.exclude(marca__isnull=True).exclude(marca='').values_list('marca', flat=True).distinct()
    marcas = sorted(list(set(marcas_queryset)))
    
    # Géneros (heredado)
    generos = productos_qs.exclude(genero__isnull=True).exclude(genero='').values_list('genero', flat=True).distinct()
    
    return JsonResponse({
        'categorias': categorias,
        'subcategorias': subcategorias,
        'precio_min': float(precios['min_precio'] or 0),
        'precio_max': float(precios['max_precio'] or 0),
        'tallas': tallas,
        'colores': colores,
        'marcas': marcas,
        'generos': list(generos),
    })


@require_GET
def search_page(request):
    """
    Página HTML de búsqueda avanzada con filtros
    """
    # Obtener opciones de filtros para pasarlas al template
    categorias = Categoria.objects.all()
    
    # Obtener tallas disponibles (de JSONField tallas_stock)
    todas_variantes = Variante.objects.all()
    tallas_set = set()
    for v in todas_variantes:
        for talla_key, stock_val in v.tallas_stock.items():
            if stock_val > 0 and talla_key not in ('UNICA', 'N/A', ''):
                tallas_set.add(talla_key)
    
    tallas = sorted(
        list(tallas_set),
        key=lambda x: (float(x) if x.replace('.','').isdigit() else float('inf'), x)
    )
    
    # Obtener colores disponibles
    colores_set = set()
    for v in todas_variantes:
        if v.stock_total_variante > 0 and v.color and v.color not in ('N/A', ''):
            colores_set.add(v.color)
    colores = sorted(list(colores_set))
    
    # Rango de precios
    precios = Producto.objects.aggregate(
        min_precio=Min('precio'),
        max_precio=Max('precio')
    )
    
    # Obtener marcas
    marcas_queryset = Producto.objects.exclude(marca__isnull=True).exclude(marca='').values_list('marca', flat=True).distinct()
    marcas = sorted(list(set(marcas_queryset)))
    
    context = {
        'categorias': categorias,
        'tallas': tallas,
        'colores': colores,
        'marcas': marcas,
        'precio_min': precios['min_precio'] or 0,
        'precio_max': precios['max_precio'] or 0,
    }
    
    return render(request, 'public/busqueda/search.html', context)
