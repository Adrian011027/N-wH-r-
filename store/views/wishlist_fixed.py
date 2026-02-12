import json
import logging
import decimal
import jwt

from django.shortcuts import get_object_or_404
from django.http      import JsonResponse, Http404
from django.views.decorators.csrf  import csrf_exempt
from django.views.decorators.http  import require_http_methods
from django.utils.decorators       import method_decorator
from django.conf import settings
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
@require_http_methods(['GET', 'POST', 'DELETE'])
def wishlist_detail(request, id_cliente):
    """
    GET/POST/DELETE /wishlist/<id_cliente>/
    
    Requiere autenticación JWT. El token debe ser del mismo cliente o un admin.
    """
    # Extraer y validar token JWT
    auth_header = request.headers.get('Authorization')
    token_user_id = None
    token_user_role = None
    
    if auth_header:
        try:
            parts = auth_header.split(' ')
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                
                if payload.get('type') == 'access':
                    token_user_id = payload.get('user_id')
                    token_user_role = payload.get('role', 'cliente')
        except Exception as e:
            logger.debug(f"Error al decodificar token: {e}")
    
    # Si no hay token válido, retornar 401
    if not token_user_id:
        return JsonResponse({
            'error': 'Token de autenticación requerido',
            'detail': 'Debe incluir el header: Authorization: Bearer <token>'
        }, status=401)
    
    # Validar que el usuario solo puede acceder a su propia wishlist
    # Los admins pueden acceder a cualquiera
    if token_user_role != 'admin' and token_user_id != id_cliente:
        return JsonResponse({
            'error': 'No autorizado',
            'detail': 'Solo puedes acceder a tu propia wishlist'
        }, status=403)
    
    # 1️⃣  👉 nunca "or_create" aquí:
    cliente = get_object_or_404(Cliente, id=id_cliente)

    # La wishlist sí podemos crearla al vuelo
    wishlist, _ = Wishlist.objects.get_or_create(cliente=cliente)

    # ---------- GET ----------
    if request.method == 'GET':
        ids = list(wishlist.productos.values_list('id', flat=True))
        if request.GET.get('full') != 'true':
            return JsonResponse({'productos': ids})

        productos = []
        for p in Producto.objects.filter(id__in=ids).prefetch_related('variantes__imagenes'):
            variante_principal = p.variante_principal
            galeria = []
            if variante_principal:
                galeria = [img.imagen.url for img in variante_principal.imagenes.all() if img.imagen]
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
@require_http_methods(['DELETE'])
def wishlist_all(request, id_cliente):
    """
    DELETE /wishlist/all/<id_cliente>/
    Vacía la lista de deseos del cliente.
    
    Requiere autenticación JWT. El token debe ser del mismo cliente o un admin.
    """
    # Extraer y validar token JWT
    auth_header = request.headers.get('Authorization')
    token_user_id = None
    token_user_role = None
    
    if auth_header:
        try:
            parts = auth_header.split(' ')
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                
                if payload.get('type') == 'access':
                    token_user_id = payload.get('user_id')
                    token_user_role = payload.get('role', 'cliente')
        except Exception as e:
            logger.debug(f"Error al decodificar token: {e}")
    
    # Si no hay token válido, retornar 401
    if not token_user_id:
        return JsonResponse({
            'error': 'Token de autenticación requerido',
            'detail': 'Debe incluir el header: Authorization: Bearer <token>'
        }, status=401)
    
    # Validar que el usuario solo puede acceder a su propia wishlist
    # Los admins pueden acceder a cualquiera
    if token_user_role != 'admin' and token_user_id != id_cliente:
        return JsonResponse({
            'error': 'No autorizado',
            'detail': 'Solo puedes acceder a tu propia wishlist'
        }, status=403)
    
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
    Devuelve {"tallas": ["24","25",...]} o ["Única"] si no hay atributo "Talla".
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
    
    try:
        id_list = [int(i) for i in ids_raw.split(',') if i]
    except ValueError:
        return JsonResponse({'error': 'IDs inválidos'}, status=400)

    productos = []
    for p in Producto.objects.filter(id__in=id_list).prefetch_related('variantes__imagenes'):
        # Galería de imágenes de la variante principal
        variante_principal = p.variante_principal
        galeria = []
        if variante_principal:
            galeria = [img.imagen.url for img in variante_principal.imagenes.all().order_by('orden') if img.imagen]
        # La imagen principal es siempre la primera de la galería
        imagen_principal = galeria[0] if galeria else None
        
        productos.append({
            "id"    : p.id,
            "nombre": p.nombre,
            "precio": f"{p.precio.normalize():f}",
            "imagen": imagen_principal,
            "imagenes_galeria": galeria
        })

    return JsonResponse({'productos': productos})
