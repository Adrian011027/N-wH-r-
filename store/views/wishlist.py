import json
import logging
import decimal

from django.shortcuts import get_object_or_404
from django.http      import JsonResponse, Http404
from django.views.decorators.csrf  import csrf_exempt
from django.views.decorators.http  import require_http_methods
from django.utils.decorators       import method_decorator
from .decorators import jwt_role_required

from ..models import Cliente, Wishlist, Producto, Variante

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
#  1. Devuelve el ID de Cliente a partir del username
# ─────────────────────────────────────────────────────────────
@csrf_exempt
@jwt_role_required()
@require_http_methods(['GET'])
def get_cliente_id(request, username):
    """
    GET /api/cliente_id/<username>/
    Respuesta: {"id": <cliente.id>}  |  404 si no existe.
    """
    cliente = get_object_or_404(Cliente, username=username)
    return JsonResponse({'id': cliente.id})


# ─────────────────────────────────────────────────────────────
#  2. Wishlist REST (GET / PATCH / DELETE)
# ─────────────────────────────────────────────────────────────
@csrf_exempt
@jwt_role_required()
@require_http_methods(['GET', 'POST', 'DELETE'])
def wishlist_detail(request, id_cliente):

    # 1️⃣  👉 nunca “or_create” aquí:
    cliente = get_object_or_404(Cliente, id=id_cliente)

    # La wishlist sí podemos crearla al vuelo
    wishlist, _ = Wishlist.objects.get_or_create(cliente=cliente)

    # ---------- GET ----------
    if request.method == 'GET':
        ids = list(wishlist.productos.values_list('id', flat=True))
        if request.GET.get('full') != 'true':
            return JsonResponse({'productos': ids})

        productos = []
        for p in Producto.objects.filter(id__in=ids).prefetch_related('imagenes'):
            galeria = [img.imagen.url for img in p.imagenes.all() if img.imagen]
            productos.append({
                'id'    : p.id,
                'nombre': p.nombre,
                'precio': f'{p.precio.normalize():f}',
                'imagen': request.build_absolute_uri(p.imagen.url)
                           if p.imagen else None,
                'imagenes_galeria': [request.build_absolute_uri(img) for img in galeria]
            })
        return JsonResponse({'productos': productos})

    # ---------- POST / DELETE ----------
    try:
        prod_id = int(json.loads(request.body)['producto_id'])
    except Exception:
        return JsonResponse(
            {'error': 'JSON inválido o falta "producto_id"'},
            status=400
        )

    producto = get_object_or_404(Producto, id=prod_id)

    if request.method == 'POST':
        wishlist.productos.add(producto)      # si existe, no pasa nada
    else:                                     # DELETE
        wishlist.productos.remove(producto)

    # Siempre devolvemos el estado actual
    ids = list(wishlist.productos.values_list('id', flat=True))
    return JsonResponse({'productos': ids})

# ─────────────────────────────────────────────────────────────
#  3. Vaciar wishlist
# ─────────────────────────────────────────────────────────────
@csrf_exempt
@jwt_role_required()
@require_http_methods(['DELETE'])
def wishlist_all(request, id_cliente):
    """
    DELETE /api/wishlist/<id_cliente>/clear/
    Vacía la lista de deseos del cliente.
    """
    cliente, _  = Cliente.objects.get_or_create(id=id_cliente)
    wishlist, _ = Wishlist.objects.get_or_create(cliente=cliente)
    wishlist.productos.clear()
    return JsonResponse({'mensaje': 'Wishlist vaciada correctamente'})


# ─────────────────────────────────────────────────────────────
#  4. Obtener tallas disponibles de un producto
# ─────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['GET'])
def producto_tallas(request, id_producto):
    """
    GET /api/productos/<id_producto>/
    Devuelve {"tallas": ["24","25",...]} o ["Única"] si no hay atributo “Talla”.
    """
    producto = Producto.objects.filter(pk=id_producto).first()
    if not producto:
        raise Http404("Producto no encontrado")

    tallas_qs = (
        Variante.objects
        .filter(
            producto=producto,
            stock__gt=0
        )
        .exclude(talla='')
        .values_list("talla", flat=True)
        .distinct()
    )

    tallas = sorted(tallas_qs) or ["Única"]
    return JsonResponse({"tallas": tallas})


# ─────────────────────────────────────────────────────────────
#  5. Endpoint genérico para INVITADOS → info por IDs
# ─────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['GET'])
def productos_por_ids(request):
    """
    GET /api/productos_por_ids/?ids=2,5,9
    Respuesta: {"productos":[{id,nombre,precio,imagen,imagenes_galeria}, … ]}
    """
    ids_raw = request.GET.get('ids', '')
    print(f"[DEBUG] productos_por_ids - ids_raw: {ids_raw}")
    
    try:
        id_list = [int(i) for i in ids_raw.split(',') if i]
    except ValueError:
        print(f"[DEBUG] Error al parsear IDs")
        return JsonResponse({'error': 'IDs inválidos'}, status=400)

    print(f"[DEBUG] id_list: {id_list}")
    
    productos = []
    for p in Producto.objects.filter(id__in=id_list).prefetch_related('imagenes'):
        galeria = [img.imagen.url for img in p.imagenes.all().order_by('orden') if img.imagen]
        # La imagen principal es siempre la primera de la galería
        imagen_principal = galeria[0] if galeria else None
        
        print(f"[DEBUG] Producto {p.id}: {p.nombre}")
        print(f"  - Galería: {len(galeria)} imágenes")
        print(f"  - Primera imagen: {imagen_principal}")
        
        productos.append({
            "id"    : p.id,
            "nombre": p.nombre,
            "precio": f"{p.precio.normalize():f}",
            "imagen": imagen_principal,  # Ya es una URL absoluta de S3
            "imagenes_galeria": galeria   # Ya son URLs absolutas de S3
        })

    print(f"[DEBUG] Retornando {len(productos)} productos")
    return JsonResponse({'productos': productos})
