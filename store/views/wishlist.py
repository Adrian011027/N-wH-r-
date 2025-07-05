import json
import logging
import decimal

from django.shortcuts import get_object_or_404
from django.http      import JsonResponse, Http404
from django.views.decorators.csrf  import csrf_exempt
from django.views.decorators.http  import require_http_methods
from django.utils.decorators       import method_decorator

from ..models import Cliente, Wishlist, Producto, VarianteAtributo

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
#  1. Devuelve el ID de Cliente a partir del username
# ─────────────────────────────────────────────────────────────
@csrf_exempt
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

        productos = [
            {
                'id'    : p.id,
                'nombre': p.nombre,
                'precio': f'{p.precio.normalize():f}',
                'imagen': request.build_absolute_uri(p.imagen.url)
                           if p.imagen else None
            }
            for p in Producto.objects.filter(id__in=ids)
        ]
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
        VarianteAtributo.objects
        .filter(
            variante__producto  = producto,
            variante__stock__gt = 0,
            atributo_valor__atributo__nombre__iexact = "talla"
        )
        .values_list("atributo_valor__valor", flat=True)
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
    Respuesta: {"productos":[{id,nombre,precio,imagen}, … ]}
    """
    ids_raw = request.GET.get('ids', '')
    try:
        id_list = [int(i) for i in ids_raw.split(',') if i]
    except ValueError:
        return JsonResponse({'error': 'IDs inválidos'}, status=400)

    productos = []
    for p in Producto.objects.filter(id__in=id_list):
        productos.append({
            "id"    : p.id,
            "nombre": p.nombre,
            "precio": f"{p.precio.normalize():f}",
            "imagen": (
                request.build_absolute_uri(p.imagen.url)
                if p.imagen else None
            )
        })

    return JsonResponse({'productos': productos})
