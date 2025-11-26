"""
Vista de búsqueda y filtrado de productos
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q, Min, Max, Prefetch, Count
from ..models import Producto, Categoria, Variante, Atributo, AtributoValor
from decimal import Decimal
import json


@require_GET
def search_products(request):
    """
    API endpoint para búsqueda y filtrado de productos
    
    Parámetros GET:
    - q: Término de búsqueda (nombre o descripción)
    - categoria: ID o nombre de categoría
    - genero: M, H, Unisex
    - precio_min: Precio mínimo
    - precio_max: Precio máximo
    - en_oferta: true/false
    - tallas: Lista de tallas separadas por coma (ej: 25,26,27)
    - ordenar: precio_asc, precio_desc, nombre_asc, nombre_desc, nuevo, popular
    - page: Número de página (opcional)
    - per_page: Productos por página (default: 20)
    """
    
    # Iniciar queryset con prefetch para optimizar
    productos = Producto.objects.prefetch_related(
        Prefetch('variantes', queryset=Variante.objects.filter(stock__gt=0)),
        'categoria'
    ).distinct()
    
    # ============ FILTRO: Término de búsqueda ============
    q = request.GET.get('q', '').strip()
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | 
            Q(descripcion__icontains=q)
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
    
    # ============ FILTRO: Género ============
    genero = request.GET.get('genero', '').strip().upper()
    if genero in ['M', 'H', 'UNISEX']:
        productos = productos.filter(genero__iexact=genero)
    
    # ============ FILTRO: Precio ============
    precio_min = request.GET.get('precio_min', '').strip()
    precio_max = request.GET.get('precio_max', '').strip()
    
    if precio_min:
        try:
            productos = productos.filter(precio__gte=Decimal(precio_min))
        except:
            pass
    
    if precio_max:
        try:
            productos = productos.filter(precio__lte=Decimal(precio_max))
        except:
            pass
    
    # ============ FILTRO: En oferta ============
    en_oferta = request.GET.get('en_oferta', '').strip().lower()
    if en_oferta == 'true':
        productos = productos.filter(en_oferta=True)
    
    # ============ FILTRO: Tallas disponibles ============
    tallas = request.GET.get('tallas', '').strip()
    if tallas:
        tallas_list = [t.strip() for t in tallas.split(',') if t.strip()]
        if tallas_list:
            # Filtrar productos que tengan variantes con esas tallas
            productos = productos.filter(
                variantes__attrs__atributo_valor__atributo__nombre__iexact='Talla',
                variantes__attrs__atributo_valor__valor__in=tallas_list,
                variantes__stock__gt=0
            ).distinct()
    
    # ============ FILTRO: Solo con stock ============
    solo_disponibles = request.GET.get('disponibles', 'true').strip().lower()
    if solo_disponibles != 'false':
        productos = productos.filter(variantes__stock__gt=0).distinct()
    
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
        # Podrías agregar un campo de popularidad o contar ventas
        productos = productos.order_by('-id')  # Por ahora ordenar por ID
    
    # ============ PAGINACIÓN ============
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
    except:
        page = 1
        per_page = 20
    
    total = productos.count()
    start = (page - 1) * per_page
    end = start + per_page
    productos_pagina = productos[start:end]
    
    # ============ SERIALIZAR RESPUESTA ============
    data = []
    for p in productos_pagina:
        # Obtener tallas disponibles
        tallas_disponibles = set()
        variantes_data = []
        
        for v in p.variantes.all():
            if v.stock > 0:
                attrs = {
                    av.atributo_valor.atributo.nombre: av.atributo_valor.valor
                    for av in v.attrs.all()
                }
                
                talla = attrs.get('Talla', '')
                if talla:
                    tallas_disponibles.add(talla)
                
                variantes_data.append({
                    'id': v.id,
                    'talla': talla,
                    'precio': float(v.precio or p.precio),
                    'stock': v.stock,
                    'atributos': attrs
                })
        
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': float(p.precio),
            'precio_mayorista': float(p.precio_mayorista),
            'categoria': p.categoria.nombre,
            'categoria_id': p.categoria.id,
            'genero': p.genero,
            'en_oferta': p.en_oferta,
            'imagen': p.imagen.url if p.imagen else '',
            'tallas_disponibles': sorted(list(tallas_disponibles), key=lambda x: float(x) if x.replace('.','').isdigit() else x),
            'stock_total': sum(v['stock'] for v in variantes_data),
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
    Obtiene las opciones disponibles para filtros
    """
    
    # Categorías
    categorias = list(Categoria.objects.all().values('id', 'nombre'))
    
    # Rango de precios
    precios = Producto.objects.aggregate(
        min_precio=Min('precio'),
        max_precio=Max('precio')
    )
    
    # Tallas disponibles
    tallas_queryset = AtributoValor.objects.filter(
        atributo__nombre__iexact='Talla',
        variante__stock__gt=0
    ).values_list('valor', flat=True).distinct()
    
    tallas = sorted(
        list(set(tallas_queryset)),
        key=lambda x: float(x) if x.replace('.','').isdigit() else x
    )
    
    # Géneros
    generos = Producto.objects.values_list('genero', flat=True).distinct()
    
    return JsonResponse({
        'categorias': categorias,
        'precio_min': float(precios['min_precio'] or 0),
        'precio_max': float(precios['max_precio'] or 0),
        'tallas': tallas,
        'generos': list(generos),
    })


@require_GET
def search_page(request):
    """
    Página HTML de búsqueda con filtros
    """
    # Obtener opciones de filtros para pasarlas al template
    categorias = Categoria.objects.all()
    
    # Obtener tallas disponibles
    atributo_talla = Atributo.objects.filter(nombre__iexact='Talla').first()
    tallas = []
    if atributo_talla:
        tallas_queryset = AtributoValor.objects.filter(
            atributo=atributo_talla,
            variante__stock__gt=0
        ).values_list('valor', flat=True).distinct()
        
        tallas = sorted(
            list(set(tallas_queryset)),
            key=lambda x: float(x) if x.replace('.','').isdigit() else x
        )
    
    # Rango de precios
    precios = Producto.objects.aggregate(
        min_precio=Min('precio'),
        max_precio=Max('precio')
    )
    
    context = {
        'categorias': categorias,
        'tallas': tallas,
        'precio_min': precios['min_precio'] or 0,
        'precio_max': precios['max_precio'] or 0,
    }
    
    return render(request, 'public/busqueda/search.html', context)
