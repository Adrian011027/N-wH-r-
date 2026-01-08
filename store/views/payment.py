"""
Vista para integrar pagos con Conekta
Plataforma de pagos mexicana - API v2.0
"""
import json
import requests
import hmac
import hashlib
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse

from ..models import Carrito, Orden, OrdenDetalle, Variante, Cliente

# Constantes para Conekta API
CONEKTA_BASE_URL = "https://api.conekta.io"
CONEKTA_SANDBOX_URL = "https://api.conekta.io"


# ───────────────────────────────────────────────────────────────
# Helper: Crear orden en Conekta via API HTTP
# ───────────────────────────────────────────────────────────────
def crear_orden_conekta(carrito, cliente):
    """
    Crea una orden en Conekta usando API HTTP.
    En caso de fallo, devuelve una orden de prueba local.
    Retorna el objeto Order de Conekta o un mock si hay error.
    """
    try:
        # Construir línea de items
        line_items = []
        for cp in carrito.items.select_related('variante__producto').all():
            variante = cp.variante
            producto = variante.producto
            
            line_items.append({
                "title": f"{producto.nombre} - {variante.talla} {variante.color}",
                "unit_price": int(float(variante.precio if variante.precio else producto.precio) * 100),  # En centavos
                "quantity": cp.cantidad,
            })
        
        # Payload para crear orden en Conekta
        payload = {
            "currency": "MXN",
            "customer_info": {
                "name": cliente.nombre or cliente.username,
                "email": cliente.correo,
                "phone": cliente.telefono or "",
            },
            "line_items": line_items,
            "metadata": {
                "carrito_id": str(carrito.id),
                "cliente_id": str(cliente.id),
            }
        }
        
        # Hacer petición POST a Conekta
        headers = {
            "Authorization": f"Bearer {settings.CONEKTA_API_KEY}",
            "Accept": "application/vnd.conekta-v2.0.0+json",
            "Content-Type": "application/json",
        }
        
        response = requests.post(
            f"{CONEKTA_BASE_URL}/orders",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"⚠️ Error Conekta ({response.status_code}): {response.text}")
            # En caso de error, devolver una orden de prueba para desarrollo
            print(f"⚠️ Usando orden de prueba local (carrito_id={carrito.id})")
            return {
                "id": f"test_order_{carrito.id}",
                "status": "pending_payment",
                "currency": "MXN",
                "customer_info": {
                    "name": cliente.nombre or cliente.username,
                    "email": cliente.correo,
                }
            }
    
    except requests.RequestException as e:
        print(f"⚠️ Error de conexión con Conekta: {e}")
        # Devolver orden de prueba en caso de error de conexión
        print(f"⚠️ Usando orden de prueba local (carrito_id={carrito.id})")
        return {
            "id": f"test_order_{carrito.id}",
            "status": "pending_payment",
            "currency": "MXN",
            "customer_info": {
                "name": cliente.nombre or cliente.username,
                "email": cliente.correo,
            }
        }
    except Exception as e:
        print(f"⚠️ Error al crear orden en Conekta: {e}")
        # Devolver orden de prueba
        return {
            "id": f"test_order_{carrito.id}",
            "status": "pending_payment",
            "currency": "MXN",
            "customer_info": {
                "name": cliente.nombre or cliente.username,
                "email": cliente.correo,
            }
        }


# ───────────────────────────────────────────────────────────────
# 1. GET - Mostrar formulario de pago con Conekta
# ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
def mostrar_formulario_pago_conekta(request, carrito_id):
    """
    Muestra el formulario de pago integrado con Conekta.
    """
    try:
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente
        
        if not cliente:
            return JsonResponse({
                'error': 'Carrito sin cliente asociado'
            }, status=400)
        
        # Crear orden en Conekta (o usar orden de prueba si falla)
        orden_conekta = crear_orden_conekta(carrito, cliente)
        
        # Calcular total
        total = Decimal('0.00')
        items_detalle = []
        for cp in carrito.items.all():
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            subtotal = Decimal(str(precio)) * cp.cantidad
            total += subtotal
            
            # Obtener imagen
            galeria = [img.imagen.url for img in producto.imagenes.all() if img.imagen]
            imagen = galeria[0] if galeria else "/static/img/no-image.jpg"
            
            items_detalle.append({
                'producto': producto.nombre,
                'variante': f"{variante.talla} - {variante.color}",
                'cantidad': cp.cantidad,
                'precio_unitario': precio,
                'subtotal': subtotal,
                'imagen': imagen,
            })
        
        context = {
            'carrito': carrito,
            'cliente': cliente,
            'total': total,
            'items': items_detalle,
            'conekta_order_id': orden_conekta.get('id'),
            'conekta_public_key': settings.CONEKTA_PUBLIC_KEY,
        }
        
        return render(request, 'public/pago/formulario_conekta.html', context)
    
    except Exception as e:
        print(f"Error en mostrar_formulario_pago_conekta: {e}")
        return JsonResponse({
            'error': f'Error al procesar: {str(e)}'
        }, status=500)


# ───────────────────────────────────────────────────────────────
# 2. POST - Procesar pago con Conekta (AJAX)
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def procesar_pago_conekta(request):
    """
    Procesa el pago mediante Conekta usando el token del cliente.
    Requiere:
    - carrito_id: ID del carrito
    - token: Token de pago de Conekta
    - payment_method: Método de pago (card, oxxo, etc.)
    """
    print(f"📍 DEBUG: Entrando a procesar_pago_conekta")
    print(f"📍 REQUEST METHOD: {request.method}")
    print(f"📍 REQUEST HEADERS: {dict(request.headers)}")
    
    try:
        # Validar JWT si es necesario (agregar si hay middleware JWT)
        # El @csrf_exempt debería permitir peticiones sin CSRF
        
        print(f"📍 DEBUG: Intentando parsear JSON del body")
        data = json.loads(request.body)
        print(f"📍 DEBUG: Data parseada: {data}")
        
        carrito_id = data.get('carrito_id')
        token = data.get('token')
        payment_method = data.get('payment_method', 'card')
        
        print(f"📍 DEBUG: carrito_id={carrito_id}, token={token}, payment_method={payment_method}")
        
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente
        
        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Carrito sin cliente'
            }, status=400)
        
        # Calcular total en centavos
        total_centavos = 0
        for cp in carrito.items.all():
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            total_centavos += int(float(precio) * 100 * cp.cantidad)
        
        # Crear cargo en Conekta vía API HTTP
        payload = {
            "amount": total_centavos,
            "payment_method": {
                "type": payment_method,
                "token_id": token,
            }
        }
        
        headers = {
            "Authorization": f"Bearer {settings.CONEKTA_API_KEY}",
            "Accept": "application/vnd.conekta-v2.0.0+json",
            "Content-Type": "application/json",
        }
        
        # Obtener el order_id del carrito (guardado en context anterior)
        # Para este ejemplo, usamos carrito_id como referencia
        response = requests.post(
            f"{CONEKTA_BASE_URL}/orders/{carrito_id}/charges",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            charge_data = response.json()
            charge_status = charge_data.get('status')
            
            # Si el pago fue exitoso o está pendiente, crear la orden en la BD
            if charge_status in ['paid', 'pending_payment', 'under_review']:
                # Crear registro de Orden
                orden = Orden.objects.create(
                    carrito=carrito,
                    cliente=cliente,
                    total_amount=Decimal(str(total_centavos / 100)),
                    status='procesando' if charge_status == 'paid' else 'pendiente_pago',
                    payment_method='conekta',
                    conekta_order_id=carrito_id,
                    conekta_charge_id=charge_data.get('id')
                )
                
                # Crear detalles de la orden
                for cp in carrito.items.all():
                    variante = cp.variante
                    producto = variante.producto
                    precio_unitario = variante.precio if variante.precio else producto.precio
                    
                    OrdenDetalle.objects.create(
                        order=orden,
                        variante=variante,
                        cantidad=cp.cantidad,
                        precio_unitario=precio_unitario
                    )
                
                # Marcar carrito como vacío
                carrito.status = 'vacio'
                carrito.save()
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Pago procesado exitosamente',
                    'orden_id': orden.id,
                    'redirect': reverse('pago_exitoso')
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Pago no completado. Estado: {charge_status}'
                }, status=400)
        
        else:
            error_response = response.json()
            error_msg = error_response.get('message', 'Error desconocido en Conekta')
            return JsonResponse({
                'success': False,
                'error': f'Error en Conekta: {error_msg}'
            }, status=response.status_code)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ───────────────────────────────────────────────────────────────
# 3. Webhook - Confirmar pagos desde Conekta
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def webhook_conekta(request):
    """
    Recibe eventos de Conekta (charge.paid, charge.under_review, etc.)
    Valida la firma del webhook con CONEKTA_WEBHOOK_SECRET
    """
    try:
        # Obtener el body crudo
        body = request.body.decode('utf-8')
        
        # Obtener headers
        signature = request.headers.get('X-Conekta-Signature', '')
        
        # Validar firma del webhook (opcional pero recomendado)
        if settings.CONEKTA_WEBHOOK_SECRET:
            computed_signature = hmac.new(
                settings.CONEKTA_WEBHOOK_SECRET.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if signature != computed_signature:
                print(f"⚠️ Firma de webhook inválida")
                return JsonResponse({
                    'success': False,
                    'error': 'Firma de webhook inválida'
                }, status=401)
        
        # Parsear JSON
        data = json.loads(body)
        event_type = data.get('type')
        event_data = data.get('data', {})
        
        # Manejar eventos de pago
        if event_type == 'charge.paid':
            charge = event_data.get('object', {})
            order_id = charge.get('order_id')
            
            # Buscar la orden relacionada
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'pagado'
                orden.save()
                print(f"✅ Pago confirmado para orden #{orden.id}")
            except Orden.DoesNotExist:
                print(f"⚠️ Orden no encontrada para order_id {order_id}")
        
        elif event_type == 'charge.under_review':
            charge = event_data.get('object', {})
            order_id = charge.get('order_id')
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'revisión'
                orden.save()
                print(f"🔍 Pago en revisión para orden #{orden.id}")
            except Orden.DoesNotExist:
                pass
        
        elif event_type == 'charge.refunded':
            charge = event_data.get('object', {})
            order_id = charge.get('order_id')
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'reembolsado'
                orden.save()
                print(f"💰 Pago reembolsado para orden #{orden.id}")
            except Orden.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'webhook_processed': True
        })
    
    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ───────────────────────────────────────────────────────────────
# 4. Páginas de resultado
# ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
def pago_exitoso(request):
    """Página de pago completado exitosamente"""
    return render(request, 'public/pago/pago_exitoso.html')


@require_http_methods(["GET"])
def pago_cancelado(request):
    """Página de pago cancelado"""
    return render(request, 'public/pago/pago_cancelado.html')
