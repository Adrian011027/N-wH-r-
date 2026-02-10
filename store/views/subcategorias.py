"""
Vistas para CRUD de Subcategorías
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from ..models import Subcategoria, Categoria
from .decorators import admin_required
import json


@require_GET
def get_subcategorias(request):
    """
    Obtener subcategorías, opcionalmente filtradas por categoría.
    
    Parámetros GET:
    - categoria_id: (opcional) ID de categoría para filtrar
    - activas: true/false (default: true) - mostrar solo subcategorías activas
    """
    subcategorias = Subcategoria.objects.all().select_related('categoria')
    
    # Filtrar por categoría si se especifica
    categoria_id = request.GET.get('categoria_id', '').strip()
    if categoria_id:
        try:
            subcategorias = subcategorias.filter(categoria_id=int(categoria_id))
        except ValueError:
            pass
    
    # Filtrar por estado activo (default: solo activas)
    solo_activas = request.GET.get('activas', 'true').strip().lower()
    if solo_activas != 'false':
        subcategorias = subcategorias.filter(activa=True)
    
    data = []
    for sc in subcategorias.order_by('orden', 'nombre'):
        data.append({
            'id': sc.id,
            'nombre': sc.nombre,
            'descripcion': sc.descripcion,
            'categoria_id': sc.categoria.id,
            'categoria_nombre': sc.categoria.nombre,
            'imagen': sc.imagen.url if sc.imagen else None,
            'orden': sc.orden,
            'activa': sc.activa,
            'created_at': sc.created_at.isoformat(),
            'productos_count': sc.productos.count(),
        })
    
    return JsonResponse(data, safe=False)


@csrf_exempt
@admin_required()
@require_http_methods(["POST"])
def create_subcategoria(request):
    """
    Crear una nueva subcategoría.
    
    Body FormData o JSON:
    {
        "nombre": "Dama",
        "categoria_id": 1,
        "descripcion": "Productos para mujeres",
        "orden": 1,
        "activa": true,
        "imagen": <archivo>
    }
    """
    # Detectar tipo de contenido
    if request.content_type and request.content_type.startswith("application/json"):
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre', '').strip()
            categoria_id = data.get('categoria_id')
            descripcion = data.get('descripcion', '').strip()
            orden = data.get('orden', 0)
            activa = data.get('activa', True)
            imagen = None
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
    else:
        # multipart/form-data
        nombre = request.POST.get('nombre', '').strip()
        categoria_id = request.POST.get('categoria_id')
        descripcion = request.POST.get('descripcion', '').strip()
        orden = request.POST.get('orden', 0)
        activa = request.POST.get('activa', 'true').lower() == 'true'
        imagen = request.FILES.get('imagen')
    
    # Validaciones
    if not nombre:
        return JsonResponse({"error": "El nombre es obligatorio"}, status=400)
    if not categoria_id:
        return JsonResponse({"error": "categoria_id es obligatorio"}, status=400)
    
    # Verificar que la categoría existe
    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        return JsonResponse({"error": "Categoría no encontrada"}, status=404)
    
    # Verificar que no exista ya una subcategoría con ese nombre en esa categoría
    if Subcategoria.objects.filter(categoria_id=categoria_id, nombre__iexact=nombre).exists():
        return JsonResponse({"error": "Ya existe una subcategoría con ese nombre en esta categoría"}, status=400)
    
    try:
        subcategoria = Subcategoria.objects.create(
            categoria=categoria,
            nombre=nombre,
            descripcion=descripcion,
            orden=int(orden),
            activa=bool(activa),
            imagen=imagen
        )
        
        return JsonResponse({
            'id': subcategoria.id,
            'nombre': subcategoria.nombre,
            'categoria_id': subcategoria.categoria.id,
            'categoria_nombre': subcategoria.categoria.nombre,
            'descripcion': subcategoria.descripcion,
            'imagen': subcategoria.imagen.url if subcategoria.imagen else None,
            'orden': subcategoria.orden,
            'activa': subcategoria.activa,
            'created_at': subcategoria.created_at.isoformat(),
        }, status=201)
    
    except Exception as e:
        return JsonResponse({"error": f"Error al crear subcategoría: {str(e)}"}, status=500)


@csrf_exempt
@admin_required()
@require_http_methods(["PUT", "PATCH"])
def update_subcategoria(request, id):
    """
    Actualizar una subcategoría existente.
    
    Body FormData o JSON (todos los campos opcionales):
    {
        "nombre": "Damas",
        "descripcion": "Nueva descripción",
        "orden": 2,
        "activa": false,
        "imagen": <archivo>
    }
    """
    subcategoria = get_object_or_404(Subcategoria, id=id)
    
    # Detectar tipo de contenido
    if request.content_type and request.content_type.startswith("application/json"):
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
    else:
        # multipart/form-data - convertir POST a dict-like
        data = request.POST.dict() if request.POST else {}
    
    # Actualizar solo los campos que se proporcionan
    if 'nombre' in data:
        nombre = data['nombre'].strip()
        if nombre:
            # Verificar unicidad en la categoría
            if Subcategoria.objects.filter(
                categoria_id=subcategoria.categoria_id, 
                nombre__iexact=nombre
            ).exclude(id=id).exists():
                return JsonResponse({"error": "Ya existe una subcategoría con ese nombre en esta categoría"}, status=400)
            subcategoria.nombre = nombre
    
    if 'descripcion' in data:
        subcategoria.descripcion = data['descripcion'].strip()
    
    if 'orden' in data:
        try:
            subcategoria.orden = int(data['orden'])
        except (ValueError, TypeError):
            return JsonResponse({"error": "orden debe ser un número"}, status=400)
    
    if 'activa' in data:
        subcategoria.activa = data['activa'].lower() == 'true' if isinstance(data['activa'], str) else bool(data['activa'])
    
    # Manejar imagen (solo si se envía archivo)
    if 'imagen' in request.FILES:
        subcategoria.imagen = request.FILES['imagen']
    
    subcategoria.save()
    
    return JsonResponse({
        'id': subcategoria.id,
        'nombre': subcategoria.nombre,
        'categoria_id': subcategoria.categoria.id,
        'categoria_nombre': subcategoria.categoria.nombre,
        'descripcion': subcategoria.descripcion,
        'imagen': subcategoria.imagen.url if subcategoria.imagen else None,
        'orden': subcategoria.orden,
        'activa': subcategoria.activa,
        'updated_at': subcategoria.updated_at.isoformat(),
    })


@csrf_exempt
@admin_required()
@require_http_methods(["DELETE"])
def delete_subcategoria(request, id):
    """
    Eliminar una subcategoría.
    Los productos asociados mantendrán null en subcategoria pero conservarán su categoría.
    """
    subcategoria = get_object_or_404(Subcategoria, id=id)
    nombre = subcategoria.nombre
    categoria_nombre = subcategoria.categoria.nombre
    
    subcategoria.delete()
    
    return JsonResponse({
        'message': f'Subcategoría "{nombre}" de la categoría "{categoria_nombre}" eliminada correctamente',
        'deleted_id': id,
    })


@require_GET
def get_subcategorias_por_categoria(request, categoria_id):
    """
    Obtener todas las subcategorías activas de una categoría específica.
    (Versión con categoria_id en la URL)
    
    Parámetros GET:
    - incluir_inactivas: true/false (default: false)
    """
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    subcategorias = categoria.subcategorias.all()
    
    incluir_inactivas = request.GET.get('incluir_inactivas', 'false').strip().lower()
    if incluir_inactivas != 'true':
        subcategorias = subcategorias.filter(activa=True)
    
    data = []
    for sc in subcategorias.order_by('orden', 'nombre'):
        data.append({
            'id': sc.id,
            'nombre': sc.nombre,
            'descripcion': sc.descripcion,
            'imagen': sc.imagen.url if sc.imagen else None,
            'orden': sc.orden,
            'activa': sc.activa,
            'productos_count': sc.productos.count(),
        })
    
    return JsonResponse({
        'categoria_id': categoria.id,
        'categoria_nombre': categoria.nombre,
        'subcategorias': data,
    })


@require_GET
def subcategorias_por_categoria_query(request):
    """
    Obtener subcategorías filtradas por categoría y género.
    Endpoint público para el navbar dinámico (usa query params).
    
    GET /api/subcategorias-por-categoria/?categoria_id=X&genero=hombre|mujer|unisex
    """
    categoria_id = request.GET.get('categoria_id', '').strip()
    genero_param = request.GET.get('genero', '').lower()
    
    # Mapeo de género
    genero_map = {
        'hombre': ['Hombre', 'Unisex'],
        'mujer': ['Mujer', 'Unisex'],
        'unisex': ['Unisex'],
        'h': ['Hombre', 'Unisex'],
        'm': ['Mujer', 'Unisex'],
        'u': ['Unisex'],
    }
    
    if not categoria_id:
        return JsonResponse({'error': 'categoria_id es requerido'}, status=400)
    
    try:
        categoria = get_object_or_404(Categoria, id=int(categoria_id))
    except ValueError:
        return JsonResponse({'error': 'categoria_id inválido'}, status=400)
    
    # Mapear parámetro a valores de BD
    genero_map = {
        'hombre': ['H', 'U'],
        'mujer': ['M', 'U'],
        'h': ['H', 'U'],
        'm': ['M', 'U'],
    }
    
    generos = genero_map.get(genero_param, [])
    
    # Obtener subcategorías activas de la categoría
    subcategorias = categoria.subcategorias.filter(activa=True)
    
    # Si hay filtro de género, solo mostrar subcategorías que tengan productos de ese género
    if generos:
        from django.db.models import Count, Q
        subcategorias = subcategorias.annotate(
            productos_genero=Count('productos', filter=Q(productos__genero__in=generos))
        ).filter(productos_genero__gt=0)
    
    data = []
    for sc in subcategorias.order_by('orden', 'nombre'):
        data.append({
            'id': sc.id,
            'nombre': sc.nombre,
            'descripcion': sc.descripcion,
            'imagen': sc.imagen.url if sc.imagen else None,
            'orden': sc.orden,
        })
    
    return JsonResponse({
        'categoria_id': categoria.id,
        'categoria_nombre': categoria.nombre,
        'subcategorias': data,
    })
