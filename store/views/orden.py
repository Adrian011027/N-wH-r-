
import json
import logging
from django.forms import model_to_dict
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from ..models import  Carrito, Orden, OrdenDetalle, Variante, Cliente
from django.db import models, transaction
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from .decorators import jwt_role_required, admin_required, login_required_user, admin_required_hybrid
logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# DASHBOARD ADMIN - Gestión de Órdenes
# ───────────────────────────────────────────────

@login_required_user
def dashboard_ordenes(request):
    """Vista HTML del panel de órdenes para admin"""
    return render(request, "dashboard/ordenes/lista.html")


@csrf_exempt
@admin_required_hybrid()
@require_GET
def get_all_ordenes(request):
    """API: Obtener todas las órdenes con filtros opcionales"""
    try:
        # Filtros opcionales
        status_filter = request.GET.get('status', '')
        cliente_filter = request.GET.get('cliente', '')
        fecha_desde = request.GET.get('desde', '')
        fecha_hasta = request.GET.get('hasta', '')
        
        ordenes = Orden.objects.all().select_related('cliente').prefetch_related(
            'detalles__variante__producto'
        ).order_by('-created_at')
        
        # Aplicar filtros
        if status_filter:
            ordenes = ordenes.filter(status__iexact=status_filter)
        
        if cliente_filter:
            ordenes = ordenes.filter(
                models.Q(cliente__username__icontains=cliente_filter) |
                models.Q(cliente__nombre__icontains=cliente_filter) |
                models.Q(cliente__correo__icontains=cliente_filter)
            )
        
        if fecha_desde:
            ordenes = ordenes.filter(created_at__date__gte=fecha_desde)
        
        if fecha_hasta:
            ordenes = ordenes.filter(created_at__date__lte=fecha_hasta)
        
        data = []
        for orden in ordenes:
            items = []
            for detalle in orden.detalles.all():
                variante = detalle.variante
                producto = variante.producto
                variante_principal = producto.variante_principal
                galeria = []
                if variante_principal:
                    galeria = [img.imagen.url for img in variante_principal.imagenes.all() if img.imagen]
                
                items.append({
                    'producto_id': producto.id,
                    'producto_nombre': producto.nombre,
                    'producto_imagen': galeria[0] if galeria else None,
                    'variante_id': variante.id,
                    'talla': variante.talla,
                    'color': variante.color,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.precio_unitario * detalle.cantidad)
                })
            
            data.append({
                'id': orden.id,
                'cliente': {
                    'id': orden.cliente.id,
                    'username': orden.cliente.username,
                    'nombre': orden.cliente.nombre or orden.cliente.username,
                    'correo': orden.cliente.correo or '',
                    'telefono': orden.cliente.telefono or '',
                    'direccion': orden.cliente.direccion_completa or orden.cliente.direccion or ''
                },
                'status': orden.status,
                'total_amount': float(orden.total_amount),
                'payment_method': orden.payment_method,
                'created_at': orden.created_at.strftime('%d/%m/%Y %H:%M'),
                'created_at_iso': orden.created_at.isoformat(),
                'items': items,
                'total_items': sum(item['cantidad'] for item in items)
            })
        
        # Estadísticas
        stats = {
            'total': Orden.objects.count(),
            'pendientes': Orden.objects.filter(status__iexact='pendiente').count(),
            'procesando': Orden.objects.filter(status__in=['procesando', 'proces']).count(),
            'enviados': Orden.objects.filter(status__iexact='enviado').count(),
            'entregados': Orden.objects.filter(status__iexact='entregado').count(),
            'cancelados': Orden.objects.filter(status__iexact='cancelado').count(),
        }
        
        return JsonResponse({
            'success': True,
            'ordenes': data,
            'stats': stats,
            'total': len(data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@admin_required_hybrid()
@require_http_methods(["POST", "PUT"])
def cambiar_estado_orden(request, id):
    """API: Cambiar el estado de una orden"""
    try:
        data = json.loads(request.body or '{}')
        nuevo_estado = data.get('status', '').lower()
        
        estados_validos = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False, 
                'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'
            }, status=400)
        
        orden = get_object_or_404(Orden, id=id)
        estado_anterior = orden.status
        orden.status = nuevo_estado
        orden.save(update_fields=['status'])
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Orden #{id} actualizada a "{nuevo_estado}"',
            'orden_id': id,
            'estado_anterior': estado_anterior,
            'estado_nuevo': nuevo_estado
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@jwt_role_required()
@require_http_methods(["GET"])
def get_orden(request, id):
    # 1. Recuperar la orden o devolver 404
    orden = get_object_or_404(Orden, id=id)

    # 2. Armar la respuesta
    data = {
        "id": orden.id,
        "cliente": {
            "username": orden.cliente.username,
            "nombre":   getattr(orden.cliente, "nombre", ""),
            "correo": orden.cliente.correo or "no proporcionado",
            "telefono": getattr(orden.cliente, "telefono", None),
        },
        "carrito_id":    orden.carrito.id,
        "total_piezas":  sum(det.cantidad for det in orden.detalles.all()),
        "total_amount":  float(orden.total_amount),
        "status":        orden.status,
        "payment_method":orden.payment_method,
        "created_at":    orden.created_at.isoformat(),
        "items":         [],
    }

    # 3. Recorrer cada OrdenDetalle para poblar "items"
    for det in orden.detalles.select_related("variante", "variante__producto"):
        variante = det.variante
        data["items"].append({
            "producto":        variante.producto.nombre,
            "variante_id":     variante.id,
            "talla":           variante.talla,
            "color":           variante.color,
            "cantidad":        det.cantidad,
            "precio_unitario": float(det.precio_unitario),
            "subtotal":        float(det.precio_unitario * det.cantidad)
        })

    # 4. Devolver JSON con indentación y caracteres unicode
    return JsonResponse(data, json_dumps_params={
        "ensure_ascii": False,
        "indent": 2
    })

@csrf_exempt
def crear_orden_desde_payload(payload):


    carrito_id    = payload["carrito_id"]
    total_amount  = payload["total_amount"]
    # Puedes tomar status / payment_method directo del payload si viene, 
        # o asignar uno por defecto:
    status= "pendiente"
    payment_method= payload.get("payment_method", "sin_especificar")

    # 1. Recuperamos carrito y cliente
    carrito = get_object_or_404(Carrito, id=carrito_id)
    cliente = carrito.cliente  # si carrito.cliente es None, falla aquí; valida antes si aceptas invitados

    with transaction.atomic():
        # 2. Crear la orden
        orden = Orden.objects.create(
            carrito        = carrito,
            cliente        = cliente,
            total_amount   = total_amount,
            status         = status,
            payment_method = payment_method,
        )

        # 3. Crear los detalles
        for item in payload["items"]:
            variante = get_object_or_404(Variante, id=item["variante_id"])
            OrdenDetalle.objects.create(
                order           = orden,
                variante        = variante,
                cantidad        = item["cantidad"],
                precio_unitario = item["precio_unitario"],
            )

        # 4. (Opcional) Actualizar el estado del carrito
        carrito.save()
        data = model_to_dict(carrito, fields=['id','status','created_at','cliente','session_key'])
        logger.debug("Carrito actualizado: %s", json.dumps(data, indent=2, default=str))
        
    return orden

@csrf_exempt
@admin_required()
@require_http_methods(["POST", "PUT"])
def update_status(request, id):
    orden = get_object_or_404(Orden, id=id)
    orden.status = 'proces'
    orden.save(update_fields=["status"]) #Reducir tráfico SQL realizando el update solo a es epar de columnas
    return JsonResponse({"mensaje":"en proceso"})


from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.http import HttpResponse, HttpResponseForbidden

signer = TimestampSigner()

def procesar_por_link(request, token):
    try:
        id_orden = signer.unsign(token, max_age=86400)  # link válido 24 h
    except SignatureExpired:
        return HttpResponseForbidden("El enlace ha expirado.")
    except BadSignature:
        return HttpResponseForbidden("Enlace inválido.")

    orden = get_object_or_404(Orden, id=id_orden)
    orden.status = 'procesando'
    orden.save(update_fields=['status'])
    return HttpResponse("✅ ¡Tu orden ha sido actualizada a 'procesando'!")


# ───────────────────────────────────────────────
# API CLIENTE - Obtener sus propias órdenes  
# ───────────────────────────────────────────────

@csrf_exempt
@jwt_role_required()
@require_GET
def get_ordenes_cliente(request):
    """API: Obtener órdenes del cliente autenticado (JWT)"""
    try:
        # El decorador jwt_role_required ya validó el token y agregó request.user_id
        cliente_id = request.user_id
        
        if not cliente_id:
            return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
        
        # Obtener órdenes del cliente
        ordenes = Orden.objects.filter(
            cliente_id=cliente_id
        ).select_related('cliente').prefetch_related(
            'detalles__variante__producto__variantes__imagenes'
        ).order_by('-created_at')
        
        data = []
        for orden in ordenes:
            items = []
            for detalle in orden.detalles.all():
                variante = detalle.variante
                producto = variante.producto
                variante_principal = producto.variante_principal
                galeria = []
                if variante_principal:
                    galeria = [img.imagen.url for img in variante_principal.imagenes.all() if img.imagen]
                
                items.append({
                    'producto_id': producto.id,
                    'producto_nombre': producto.nombre,
                    'producto_imagen': galeria[0] if galeria else None,
                    'variante_id': variante.id,
                    'talla': variante.talla,
                    'color': variante.color,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.precio_unitario * detalle.cantidad)
                })
            
            # Mapear estado a Display
            status_map = {
                'pendiente': {'text': 'Pendiente', 'color': '#FFA500', 'icon': 'clock'},
                'procesando': {'text': 'Procesando', 'color': '#4169E1', 'icon': 'settings'},
                'enviado': {'text': 'Enviado', 'color': '#32CD32', 'icon': 'truck'},
                'entregado': {'text': 'Entregado', 'color': '#228B22', 'icon': 'check'},
                'cancelado': {'text': 'Cancelado', 'color': '#DC143C', 'icon': 'x'},
                'reembolso': {'text': 'Reembolso', 'color': '#FF6347', 'icon': 'info'}
            }
            status_display = status_map.get(orden.status.lower(), {
                'text': orden.status.capitalize(),
                'color': '#808080',
                'icon': 'info'
            })
            
            data.append({
                'id': orden.id,
                'status': orden.status,
                'status_display': status_display,
                'total_amount': float(orden.total_amount),
                'payment_method': orden.payment_method,
                'created_at': orden.created_at.strftime('%d/%m/%Y %H:%M'),
                'created_at_iso': orden.created_at.isoformat(),
                'items': items,
                'total_items': sum(item['cantidad'] for item in items)
            })
        
        return JsonResponse({
            'success': True,
            'ordenes': data
        }, status=200)
        
    except Exception as e:
        logger.error("get_ordenes_cliente: %s", e, exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener órdenes'
        }, status=500)


@csrf_exempt
@admin_required()
@require_http_methods(["DELETE", "POST"])
def eliminar_orden(request, id):
    """
    Elimina la orden con el id dado y todos sus detalles asociados.
    """
    orden = get_object_or_404(Orden, id=id)
    # Primero borramos los detalles (si tienes cascade no haría falta)
    orden.detalles.all().delete()
    # Luego borramos la orden
    orden.delete()
    return JsonResponse(
        {"mensaje": f"Orden {id} eliminada correctamente."},
        status=200
    )

@csrf_exempt
@admin_required()
@require_http_methods(["DELETE", "POST"])
def eliminar_producto(request, orden_id, producto_id):
    """
    Elimina de la orden con el id dado el producto id producto.
    """
    orden = get_object_or_404(Orden, id=orden_id)
    # Primero borramos los detalles (si tienes cascade no haría falta)
    

    #Agarro todo el objeto filtrando el id de interes con variante id
    qs = (orden.detalles.select_related("variante", "variante__producto").filter(variante_id=producto_id))
    #print(f"qs: {qs[0].id}")
    det = qs.first()
    if det:
        det.delete()
        logger.debug("Eliminé el detalle de orden con id=%s", det.id)
        return JsonResponse(

        {"mensaje": f"Orden {qs.first().variante_id} eliminada correctamente."},
        status=200
    )
    else:
        return JsonResponse({"mensaje": "No se pudo eliminar el producto"})