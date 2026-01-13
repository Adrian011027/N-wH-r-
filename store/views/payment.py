"""
Vista para integrar pagos con Conekta Checkout
Plataforma de pagos mexicana - API v2.0

Implementación según documentación oficial:
https://developers.conekta.com/page/checkout

Flujo:
1. Crear Customer en Conekta (opcional si ya existe)
2. Crear Order con opciones de checkout
3. Renderizar iframe con el checkoutRequestId
4. Recibir webhook cuando el pago se complete
"""
import json
import requests
import hmac
import hashlib
import base64
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse

from ..models import Carrito, Orden, OrdenDetalle, Variante, Cliente

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN API CONEKTA
# ═══════════════════════════════════════════════════════════════
CONEKTA_API_URL = "https://api.conekta.io"
CONEKTA_API_VERSION = "application/vnd.conekta-v2.0.0+json"


def get_conekta_headers():
    """Genera headers para autenticación con Conekta API"""
    api_key = settings.CONEKTA_API_KEY
    # Conekta usa Basic Auth con la API key como usuario y sin password
    credentials = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Accept": CONEKTA_API_VERSION,
        "Content-Type": "application/json",
    }


# ═══════════════════════════════════════════════════════════════
# PASO 1: CREAR O OBTENER CUSTOMER EN CONEKTA
# ═══════════════════════════════════════════════════════════════
def crear_o_obtener_customer_conekta(cliente):
    """
    Crea un customer en Conekta o retorna el ID si ya existe.
    Guarda el conekta_customer_id en el modelo Cliente.
    """
    # Si el cliente ya tiene un ID de Conekta, usarlo
    if hasattr(cliente, 'conekta_customer_id') and cliente.conekta_customer_id:
        return cliente.conekta_customer_id
    
    try:
        payload = {
            "name": cliente.nombre or cliente.username or "Cliente",
            "email": cliente.correo,
            "phone": cliente.telefono or "+5200000000000",
        }
        
        response = requests.post(
            f"{CONEKTA_API_URL}/customers",
            json=payload,
            headers=get_conekta_headers(),
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            customer_data = response.json()
            customer_id = customer_data.get('id')
            print(f"✅ Customer creado en Conekta: {customer_id}")
            
            # Guardar el ID en el cliente (si el modelo lo soporta)
            if hasattr(cliente, 'conekta_customer_id'):
                cliente.conekta_customer_id = customer_id
                cliente.save(update_fields=['conekta_customer_id'])
            
            return customer_id
        else:
            print(f"⚠️ Error creando customer: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error creando customer en Conekta: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# PASO 2: CREAR ORDER CON CHECKOUT EN CONEKTA
# ═══════════════════════════════════════════════════════════════
def crear_orden_checkout_conekta(carrito, cliente, customer_id=None):
    """
    Crea una orden en Conekta con opciones de checkout.
    Retorna el checkout_id necesario para el iframe.
    
    Según documentación: https://developers.conekta.com/page/checkout
    """
    try:
        # Construir line_items desde el carrito
        line_items = []
        total_centavos = 0
        
        for cp in carrito.items.select_related('variante__producto').all():
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            precio_centavos = int(float(precio) * 100)
            subtotal = precio_centavos * cp.cantidad
            total_centavos += subtotal
            
            line_items.append({
                "name": f"{producto.nombre}",
                "description": f"Talla: {variante.talla}, Color: {variante.color}",
                "unit_price": precio_centavos,
                "quantity": cp.cantidad,
                "sku": f"VAR-{variante.id}",
            })
        
        # Si no hay items, agregar uno de prueba
        if not line_items:
            line_items.append({
                "name": "Producto de prueba",
                "unit_price": 10000,  # $100 MXN
                "quantity": 1,
            })
            total_centavos = 10000
        
        # Construir payload según documentación de Conekta
        payload = {
            "currency": "MXN",
            "line_items": line_items,
            "customer_info": {
                "name": cliente.nombre or cliente.username or "Cliente",
                "email": cliente.correo,
                "phone": cliente.telefono or "+5200000000000",
            },
            # Configuración del Checkout
            "checkout": {
                "type": "Integration",
                "allowed_payment_methods": ["card", "cash", "bank_transfer"],
                "monthly_installments_enabled": True,
                "monthly_installments_options": [3, 6, 9, 12],
                "needs_shipping_contact": False,
                "redirection_time": 5,  # Segundos antes de redirigir
                "success_url": settings.CONEKTA_SUCCESS_URL,
                "failure_url": settings.CONEKTA_CANCEL_URL,
            },
            # Metadata para tracking
            "metadata": {
                "carrito_id": str(carrito.id),
                "cliente_id": str(cliente.id),
                "source": "django_ecommerce",
            }
        }
        
        # Si tenemos customer_id, usarlo
        if customer_id:
            payload["customer_info"] = {"customer_id": customer_id}
        
        print(f"📤 Enviando orden a Conekta: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{CONEKTA_API_URL}/orders",
            json=payload,
            headers=get_conekta_headers(),
            timeout=30
        )
        
        print(f"📥 Respuesta Conekta ({response.status_code}): {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            order_data = response.json()
            
            # Extraer checkout info
            checkout_info = order_data.get('checkout', {})
            checkout_id = checkout_info.get('id')
            order_id = order_data.get('id')
            
            print(f"✅ Orden creada: {order_id}, Checkout ID: {checkout_id}")
            
            return {
                'success': True,
                'order_id': order_id,
                'checkout_id': checkout_id,
                'checkout_url': checkout_info.get('url'),
                'amount': total_centavos,
                'order_data': order_data,
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('details', [{}])[0].get('message', response.text)
            print(f"❌ Error Conekta: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code,
            }
            
    except requests.Timeout:
        print("⚠️ Timeout conectando con Conekta")
        return {'success': False, 'error': 'Timeout conectando con Conekta'}
    except requests.RequestException as e:
        print(f"⚠️ Error de conexión: {e}")
        return {'success': False, 'error': f'Error de conexión: {str(e)}'}
    except Exception as e:
        print(f"⚠️ Error inesperado: {e}")
        return {'success': False, 'error': str(e)}


# ═══════════════════════════════════════════════════════════════
# VISTA: MOSTRAR CHECKOUT CON IFRAME DE CONEKTA
# ═══════════════════════════════════════════════════════════════
@require_http_methods(["GET"])
def mostrar_formulario_pago_conekta(request, carrito_id):
    """
    PASO 3: Muestra el iframe de Conekta Checkout.
    
    1. Obtiene el carrito y cliente
    2. Crea la orden en Conekta con checkout
    3. Renderiza el template con el iframe
    """
    try:
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente
        
        if not cliente:
            return render(request, 'public/pago/error_pago.html', {
                'error': 'Carrito sin cliente asociado. Por favor inicia sesión.'
            })
        
        # Crear customer en Conekta (opcional)
        customer_id = crear_o_obtener_customer_conekta(cliente)
        
        # Crear orden con checkout en Conekta
        resultado = crear_orden_checkout_conekta(carrito, cliente, customer_id)
        
        if not resultado.get('success'):
            return render(request, 'public/pago/error_pago.html', {
                'error': resultado.get('error', 'Error al crear orden en Conekta'),
                'carrito': carrito,
            })
        
        # Calcular total para mostrar
        total = Decimal('0.00')
        items_detalle = []
        
        for cp in carrito.items.select_related('variante__producto').all():
            variante = cp.variante
            producto = variante.producto
            precio = Decimal(str(variante.precio if variante.precio else producto.precio))
            subtotal = precio * cp.cantidad
            total += subtotal
            
            # Obtener imagen
            galeria = [img.imagen.url for img in producto.imagenes.all() if img.imagen]
            imagen = galeria[0] if galeria else "/static/images/no-image.jpg"
            
            items_detalle.append({
                'producto': producto.nombre,
                'variante': f"{variante.talla} - {variante.color}",
                'cantidad': cp.cantidad,
                'precio_unitario': precio,
                'subtotal': subtotal,
                'imagen': imagen,
            })
        
        # Guardar orden preliminar en BD
        orden, created = Orden.objects.get_or_create(
            carrito=carrito,
            defaults={
                'cliente': cliente,
                'total_amount': total,
                'status': 'pendiente_pago',
                'payment_method': 'conekta',
                'conekta_order_id': resultado.get('order_id'),
            }
        )
        
        if not created:
            orden.conekta_order_id = resultado.get('order_id')
            orden.save()
        
        context = {
            'carrito': carrito,
            'cliente': cliente,
            'total': total,
            'items': items_detalle,
            'checkout_id': resultado.get('checkout_id'),
            'conekta_order_id': resultado.get('order_id'),
            'conekta_public_key': settings.CONEKTA_PUBLIC_KEY,
            'orden_id': orden.id,
        }
        
        return render(request, 'public/pago/checkout_conekta.html', context)
    
    except Exception as e:
        print(f"❌ Error en mostrar_formulario_pago_conekta: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'public/pago/error_pago.html', {
            'error': f'Error inesperado: {str(e)}'
        })


# ═══════════════════════════════════════════════════════════════
# API: CREAR CHECKOUT (para llamadas AJAX)
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def crear_checkout_conekta(request):
    """
    Endpoint AJAX para crear un checkout de Conekta.
    Retorna el checkout_id para inicializar el iframe.
    """
    try:
        data = json.loads(request.body)
        carrito_id = data.get('carrito_id')
        
        if not carrito_id:
            return JsonResponse({'success': False, 'error': 'carrito_id requerido'}, status=400)
        
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente
        
        if not cliente:
            return JsonResponse({'success': False, 'error': 'Sin cliente asociado'}, status=400)
        
        # Crear orden con checkout
        resultado = crear_orden_checkout_conekta(carrito, cliente)
        
        if resultado.get('success'):
            return JsonResponse({
                'success': True,
                'checkout_id': resultado.get('checkout_id'),
                'order_id': resultado.get('order_id'),
            })
        else:
            return JsonResponse({
                'success': False,
                'error': resultado.get('error'),
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════
# VISTA: PROCESAR PAGO (callback del iframe)
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def procesar_pago_conekta(request):
    """
    Procesa la notificación de pago desde el iframe de Conekta.
    El iframe llama a onFinalizePayment cuando el pago termina.
    """
    try:
        data = json.loads(request.body)
        
        order_id = data.get('order_id') or data.get('conekta_order_id')
        charge_id = data.get('charge_id')
        status = data.get('status', 'unknown')
        carrito_id = data.get('carrito_id')
        
        print(f"📍 Procesando pago - Order: {order_id}, Status: {status}")
        
        # Buscar la orden en BD
        orden = None
        if order_id:
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
            except Orden.DoesNotExist:
                pass
        
        if not orden and carrito_id:
            try:
                orden = Orden.objects.get(carrito_id=carrito_id)
            except Orden.DoesNotExist:
                pass
        
        if not orden:
            return JsonResponse({
                'success': False,
                'error': 'Orden no encontrada'
            }, status=404)
        
        # Actualizar estado según resultado
        if status in ['paid', 'completed', 'approved']:
            orden.status = 'pagado'
            orden.conekta_charge_id = charge_id
            orden.save()
            
            # Vaciar carrito
            if orden.carrito:
                orden.carrito.items.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Pago completado exitosamente',
                'redirect': reverse('pago_exitoso') + f'?orden={orden.id}'
            })
        
        elif status in ['pending', 'pending_payment']:
            orden.status = 'pendiente_pago'
            orden.save()
            return JsonResponse({
                'success': True,
                'message': 'Pago pendiente de confirmación',
                'redirect': reverse('pago_exitoso') + f'?orden={orden.id}&pending=1'
            })
        
        else:
            orden.status = 'fallido'
            orden.save()
            return JsonResponse({
                'success': False,
                'error': f'Pago no completado: {status}',
                'redirect': reverse('pago_cancelado')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        print(f"❌ Error procesando pago: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════
# WEBHOOK: RECIBIR NOTIFICACIONES DE CONEKTA
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def webhook_conekta(request):
    """
    PASO 6: Recibe eventos de Conekta (charge.paid, order.paid, etc.)
    
    Eventos principales:
    - order.paid: Orden pagada exitosamente
    - order.pending_payment: Pago pendiente (OXXO, SPEI)
    - charge.paid: Cargo individual pagado
    - charge.refunded: Cargo reembolsado
    """
    try:
        body = request.body.decode('utf-8')
        
        # Validar firma del webhook (si está configurado)
        signature = request.headers.get('Digest', '')
        
        if settings.CONEKTA_WEBHOOK_SECRET and signature:
            # Calcular firma esperada
            computed = hmac.new(
                settings.CONEKTA_WEBHOOK_SECRET.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            expected_signature = f"sha-256={computed}"
            if signature != expected_signature:
                print(f"⚠️ Firma webhook inválida: {signature} vs {expected_signature}")
                # En desarrollo, continuar aunque falle la firma
                if settings.CONEKTA_MODE == 'production':
                    return JsonResponse({'error': 'Firma inválida'}, status=401)
        
        # Parsear evento
        data = json.loads(body)
        event_type = data.get('type', '')
        event_data = data.get('data', {}).get('object', {})
        
        print(f"📩 Webhook Conekta: {event_type}")
        print(f"   Data: {json.dumps(event_data, indent=2)[:500]}")
        
        # Manejar eventos
        if event_type in ['order.paid', 'charge.paid']:
            order_id = event_data.get('id') or event_data.get('order_id')
            
            if order_id:
                try:
                    orden = Orden.objects.get(conekta_order_id=order_id)
                    orden.status = 'pagado'
                    
                    # Guardar ID del charge si viene
                    charges = event_data.get('charges', {}).get('data', [])
                    if charges:
                        orden.conekta_charge_id = charges[0].get('id')
                    
                    orden.save()
                    print(f"✅ Orden #{orden.id} marcada como pagada")
                    
                    # Vaciar carrito
                    if orden.carrito:
                        orden.carrito.items.all().delete()
                        
                except Orden.DoesNotExist:
                    print(f"⚠️ Orden no encontrada: {order_id}")
        
        elif event_type == 'order.pending_payment':
            order_id = event_data.get('id')
            if order_id:
                try:
                    orden = Orden.objects.get(conekta_order_id=order_id)
                    orden.status = 'pendiente_pago'
                    orden.save()
                    print(f"⏳ Orden #{orden.id} pendiente de pago")
                except Orden.DoesNotExist:
                    pass
        
        elif event_type == 'charge.refunded':
            order_id = event_data.get('order_id')
            if order_id:
                try:
                    orden = Orden.objects.get(conekta_order_id=order_id)
                    orden.status = 'reembolsado'
                    orden.save()
                    print(f"💰 Orden #{orden.id} reembolsada")
                except Orden.DoesNotExist:
                    pass
        
        elif event_type == 'order.expired':
            order_id = event_data.get('id')
            if order_id:
                try:
                    orden = Orden.objects.get(conekta_order_id=order_id)
                    orden.status = 'expirado'
                    orden.save()
                    print(f"⏰ Orden #{orden.id} expirada")
                except Orden.DoesNotExist:
                    pass
        
        return JsonResponse({'received': True, 'event': event_type})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════
# PÁGINAS DE RESULTADO
# ═══════════════════════════════════════════════════════════════
@require_GET
def pago_exitoso(request):
    """Página mostrada cuando el pago fue exitoso"""
    orden_id = request.GET.get('orden')
    pending = request.GET.get('pending')
    
    context = {
        'orden_id': orden_id,
        'pending': pending == '1',
    }
    
    if orden_id:
        try:
            orden = Orden.objects.get(id=orden_id)
            context['orden'] = orden
        except Orden.DoesNotExist:
            pass
    
    return render(request, 'public/pago/pago_exitoso.html', context)


@require_GET
def pago_cancelado(request):
    """Página mostrada cuando el pago fue cancelado o falló"""
    return render(request, 'public/pago/pago_cancelado.html')
