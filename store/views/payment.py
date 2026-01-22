"""
Vista para integrar pagos con Conekta
Plataforma de pagos mexicana - API v2.0
"""
import json
import requests
import hmac
import hashlib
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse

from ..models import Carrito, Orden, OrdenDetalle, Variante, Cliente

# Configurar logger para Conekta
logger = logging.getLogger('conekta_payments')
logger.setLevel(logging.DEBUG)

# Crear handler para archivo si no existe
if not logger.handlers:
    handler = logging.FileHandler('conekta_payments.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
    logger.info("="*80)
    logger.info("[CREAR_ORDEN_CONEKTA] INICIANDO")
    logger.info(f"Carrito ID: {carrito.id}")
    logger.info(f"Cliente: {cliente.username} ({cliente.correo})")
    
    try:
        # Construir línea de items
        logger.info("Procesando items del carrito...")
        line_items = []
        total_centavos = 0
        item_count = 0
        
        for cp in carrito.items.select_related('variante__producto').all():
            item_count += 1
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            precio_centavos = int(float(precio) * 100)
            subtotal = precio_centavos * cp.cantidad
            total_centavos += subtotal
            
            logger.debug(f"  Item {item_count}: {producto.nombre} | Talla: {variante.talla} | Color: {variante.color} | Cantidad: {cp.cantidad} | Precio: {precio} MXN ({precio_centavos} centavos)")
            
            line_items.append({
                "title": f"{producto.nombre} - {variante.talla} {variante.color}",
                "unit_price": precio_centavos,
                "quantity": cp.cantidad,
            })
        
        logger.info(f"Total calculado: {item_count} items | {total_centavos} centavos = {total_centavos/100} MXN")
        
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
        
        logger.info("Payload creado correctamente")
        logger.debug(f"Payload: {json.dumps(payload, indent=2, default=str)}")
        
        # Hacer petición POST a Conekta
        headers = {
            "Authorization": f"Bearer {settings.CONEKTA_API_KEY}",
            "Accept": "application/vnd.conekta-v2.0.0+json",
            "Content-Type": "application/json",
        }
        
        logger.info(f"Enviando petición POST a {CONEKTA_BASE_URL}/orders")
        
        response = requests.post(
            f"{CONEKTA_BASE_URL}/orders",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"Respuesta HTTP Status: {response.status_code}")
        logger.debug(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            order_data = response.json()
            logger.info(f"✓ Orden creada exitosamente en Conekta")
            logger.info(f"  Order ID: {order_data.get('id')}")
            logger.info(f"  Status: {order_data.get('status')}")
            return order_data
        else:
            logger.error(f"Error Conekta ({response.status_code}): {response.text}")
            logger.warning(f"Usando orden de prueba local (carrito_id={carrito.id})")
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
        logger.error(f"Error de conexión con Conekta API: {type(e).__name__} - {str(e)}")
        logger.warning(f"Usando orden de prueba local (carrito_id={carrito.id})")
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
        logger.exception(f"Error al crear orden en Conekta: {type(e).__name__}")
        logger.warning(f"Usando orden de prueba local (carrito_id={carrito.id})")
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
    logger.info("="*80)
    logger.info("[MOSTRAR_FORMULARIO_PAGO] INICIANDO")
    logger.info(f"Carrito ID: {carrito_id}")
    
    try:
        logger.debug(f"Buscando carrito #{carrito_id}...")
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente
        
        logger.info(f"Carrito encontrado | Cliente: {cliente.username if cliente else 'Sin cliente'}")
        
        if not cliente:
            logger.error("Error: Carrito sin cliente asociado")
            return JsonResponse({
                'error': 'Carrito sin cliente asociado'
            }, status=400)
        
        # Crear orden en Conekta (o usar orden de prueba si falla)
        logger.info("Creando orden en Conekta...")
        orden_conekta = crear_orden_conekta(carrito, cliente)
        logger.info(f"Orden Conekta creada: {orden_conekta.get('id')}")
        
        # Calcular total
        logger.info("Procesando items para contexto de template...")
        total = Decimal('0.00')
        items_detalle = []
        item_count = 0
        
        for cp in carrito.items.all():
            item_count += 1
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            subtotal = Decimal(str(precio)) * cp.cantidad
            total += subtotal
            
            logger.debug(f"  Item {item_count}: {producto.nombre} | {variante.talla}-{variante.color} | Qty: {cp.cantidad} | Subtotal: {subtotal}")
            
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
        
        logger.info(f"Total calculado: {total} MXN | {item_count} items")
        
        context = {
            'carrito': carrito,
            'cliente': cliente,
            'total': total,
            'items': items_detalle,
            'conekta_order_id': orden_conekta.get('id'),
            'conekta_public_key': settings.CONEKTA_PUBLIC_KEY,
        }
        
        logger.info(f"Renderizando template con contexto completo")
        logger.info("[MOSTRAR_FORMULARIO_PAGO] ✓ COMPLETADO")
        
        return render(request, 'public/pago/formulario_conekta.html', context)
    
    except Exception as e:
        logger.exception(f"Error en mostrar_formulario_pago_conekta: {type(e).__name__}")
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
    logger.info("\n" + "="*80)
    logger.info("[PROCESAR_PAGO_CONEKTA] INICIANDO PROCESAMIENTO DE PAGO")
    logger.info("="*80)
    
    try:
        logger.info("Parseando JSON del body...")
        data = json.loads(request.body)
        logger.info("✓ JSON parseado correctamente")
        
        carrito_id = data.get('carrito_id')
        token = data.get('token')
        payment_method = data.get('payment_method', 'card')
        
        logger.info(f"Datos extraídos del request:")
        logger.info(f"  - carrito_id: {carrito_id}")
        logger.info(f"  - token: {token[:30] if token else 'No proporcionado'}...")
        logger.info(f"  - payment_method: {payment_method}")
        
        if not carrito_id or not token:
            logger.warning("Datos incompletos: carrito_id o token faltante")
            return JsonResponse({
                'success': False,
                'error': 'carrito_id y token son requeridos'
            }, status=400)
        
        logger.info(f"Buscando carrito #{carrito_id}...")
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente
        
        logger.info(f"✓ Carrito encontrado | Cliente: {cliente.username if cliente else 'Sin cliente'}")
        
        if not cliente:
            logger.error("Error: Carrito sin cliente asociado")
            return JsonResponse({
                'success': False,
                'error': 'Carrito sin cliente'
            }, status=400)
        
        # Calcular total en centavos
        logger.info("Calculando total del carrito...")
        total_centavos = 0
        items_detalles = []
        item_count = 0
        
        for cp in carrito.items.all():
            item_count += 1
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            item_total = int(float(precio) * 100 * cp.cantidad)
            total_centavos += item_total
            
            logger.debug(f"  Item {item_count}: {producto.nombre} | {variante.talla}-{variante.color} | {precio} MXN x {cp.cantidad} = {item_total} centavos")
            items_detalles.append({
                'variante': variante,
                'producto': producto,
                'cantidad': cp.cantidad,
                'precio_unitario': precio
            })
        
        logger.info(f"✓ Total calculado: {total_centavos} centavos = {total_centavos/100} MXN | {item_count} items")
        
        # Crear cargo en Conekta vía API HTTP
        logger.info("Preparando payload para crear charge en Conekta...")
        payload = {
            "amount": total_centavos,
            "payment_method": {
                "type": payment_method,
                "token_id": token,
            }
        }
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        headers = {
            "Authorization": f"Bearer {settings.CONEKTA_API_KEY}",
            "Accept": "application/vnd.conekta-v2.0.0+json",
            "Content-Type": "application/json",
        }
        
        # Obtener el order_id del carrito (guardado en context anterior)
        logger.info(f"Enviando carga (charge) a Conekta API...")
        logger.info(f"  - Endpoint: {CONEKTA_BASE_URL}/orders/{carrito_id}/charges")
        logger.info(f"  - Monto: {total_centavos} centavos ({total_centavos/100} MXN)")
        logger.info(f"  - Método de pago: {payment_method}")
        
        response = requests.post(
            f"{CONEKTA_BASE_URL}/orders/{carrito_id}/charges",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"Respuesta Conekta - Status HTTP: {response.status_code}")
        logger.debug(f"Response Body (primeros 800 chars): {response.text[:800]}")
        
        if response.status_code in [200, 201]:
            charge_data = response.json()
            charge_status = charge_data.get('status')
            charge_id = charge_data.get('id')
            
            logger.info(f"✓ Respuesta exitosa de Conekta")
            logger.info(f"  - Charge ID: {charge_id}")
            logger.info(f"  - Status: {charge_status}")
            logger.debug(f"  - Datos completos: {json.dumps(charge_data, indent=2, default=str)}")
            
            # Si el pago fue exitoso o está pendiente, crear la orden en la BD
            if charge_status in ['paid', 'pending_payment', 'under_review']:
                logger.info(f"Creando registro de Orden en base de datos...")
                
                try:
                    # Crear registro de Orden
                    logger.info(f"Datos para crear Orden:")
                    logger.info(f"  - carrito_id: {carrito.id}")
                    logger.info(f"  - cliente_id: {cliente.id}")
                    logger.info(f"  - total_amount: {Decimal(str(total_centavos / 100))}")
                    logger.info(f"  - status: {'procesando' if charge_status == 'paid' else 'pendiente_pago'}")
                    logger.info(f"  - payment_method: conekta")
                    logger.info(f"  - conekta_order_id: {carrito_id}")
                    logger.info(f"  - conekta_charge_id: {charge_id}")
                    
                    orden = Orden.objects.create(
                        carrito=carrito,
                        cliente=cliente,
                        total_amount=Decimal(str(total_centavos / 100)),
                        status='procesando' if charge_status == 'paid' else 'pendiente_pago',
                        payment_method='conekta',
                        conekta_order_id=carrito_id,
                        conekta_charge_id=charge_id
                    )
                    logger.info(f"✓ Orden creada en BD: #{orden.id} | Status: {orden.status}")
                    
                    # Crear detalles de la orden
                    logger.info(f"Creando detalles de orden ({len(items_detalles)} items)...")
                    for idx, item_detail in enumerate(items_detalles, 1):
                        detalle = OrdenDetalle.objects.create(
                            order=orden,
                            variante=item_detail['variante'],
                            cantidad=item_detail['cantidad'],
                            precio_unitario=item_detail['precio_unitario']
                        )
                        logger.info(f"  ✓ Detalle {idx} creado: {item_detail['producto'].nombre} x{item_detail['cantidad']}")
                    
                    logger.info(f"✓ Detalles de orden creados exitosamente ({len(items_detalles)} items)")
                    
                    # Marcar carrito como vacío
                    logger.info(f"Marcando carrito como vacío...")
                    carrito.status = 'vacio'
                    carrito.save()
                    logger.info(f"✓ Carrito vaciado correctamente")
                    
                    # Verificar que la orden se creó
                    orden_verificada = Orden.objects.get(id=orden.id)
                    detalles_count = orden_verificada.detalles.count()
                    logger.info(f"\n✅ PAGO PROCESADO EXITOSAMENTE:")
                    logger.info(f"  - Orden ID: {orden_verificada.id}")
                    logger.info(f"  - Charge ID: {charge_id}")
                    logger.info(f"  - Status: {orden_verificada.status}")
                    logger.info(f"  - Monto total: {orden_verificada.total_amount} MXN")
                    logger.info(f"  - Detalles: {detalles_count} items")
                    logger.info("="*80 + "\n")
                    
                    return JsonResponse({
                        'success': True,
                        'mensaje': 'Pago procesado exitosamente',
                        'orden_id': orden.id,
                        'redirect': f"{reverse('pago_exitoso')}?orden_id={orden.id}"
                    })
                
                except Exception as db_error:
                    logger.exception(f"Error al crear orden en BD: {type(db_error).__name__}: {str(db_error)}")
                    import traceback
                    logger.error(f"Traceback completo:\n{traceback.format_exc()}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Error al guardar orden en BD: {str(db_error)}'
                    }, status=500)
            
            else:
                logger.warning(f"Pago no completado:")
                logger.warning(f"  - Estado del charge: {charge_status}")
                logger.warning("="*80 + "\n")
                return JsonResponse({
                    'success': False,
                    'error': f'Pago no completado. Estado: {charge_status}'
                }, status=400)
        
        else:
            logger.error(f"Error en respuesta de Conekta API:")
            logger.error(f"  - HTTP Status: {response.status_code}")
            
            try:
                error_response = response.json()
                error_msg = error_response.get('message', error_response.get('error', 'Error desconocido en Conekta'))
                logger.error(f"  - Mensaje Conekta: {error_msg}")
                logger.debug(f"  - Respuesta completa: {json.dumps(error_response, indent=2)}")
            except:
                error_msg = response.text
                logger.error(f"  - Error parsing response: {error_msg}")
            
            logger.error("="*80 + "\n")
            return JsonResponse({
                'success': False,
                'error': f'Error en Conekta: {error_msg}'
            }, status=response.status_code)
    
    except json.JSONDecodeError as e:
        logger.error(f"ERROR AL PARSEAR JSON:")
        logger.error(f"  - Tipo: JSONDecodeError")
        logger.error(f"  - Detalle: {str(e)}")
        logger.error(f"  - Body recibido: {request.body[:500]}")
        logger.error("="*80 + "\n")
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido en el body'
        }, status=400)
    except Exception as e:
        logger.exception(f"ERROR GENERAL EN PROCESAR_PAGO:")
        logger.error(f"  - Tipo: {type(e).__name__}")
        logger.error(f"  - Detalle: {str(e)}")
        logger.error("="*80 + "\n")
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
    logger.info("\n" + "="*80)
    logger.info("[WEBHOOK_CONEKTA] EVENTO RECIBIDO")
    logger.info("="*80)
    
    try:
        # Obtener el body crudo
        body = request.body.decode('utf-8')
        
        # Obtener headers
        signature = request.headers.get('X-Conekta-Signature', '')
        
        logger.info(f"Signature recibida: {signature[:50] if signature else 'No recibida'}...")
        logger.debug(f"Body (primeros 500 chars): {body[:500]}...")
        
        # Validar firma del webhook (opcional pero recomendado)
        if settings.CONEKTA_WEBHOOK_SECRET:
            computed_signature = hmac.new(
                settings.CONEKTA_WEBHOOK_SECRET.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            logger.info(f"Validando firma del webhook...")
            logger.debug(f"  - Esperada: {computed_signature}")
            logger.debug(f"  - Recibida: {signature}")
            
            if signature != computed_signature:
                logger.error(f"❌ Firma de webhook INVÁLIDA - Webhook rechazado")
                return JsonResponse({
                    'success': False,
                    'error': 'Firma de webhook inválida'
                }, status=401)
            
            logger.info(f"✓ Firma válida")
        
        # Parsear JSON
        data = json.loads(body)
        event_type = data.get('type')
        event_data = data.get('data', {})
        
        logger.info(f"✓ JSON parseado correctamente")
        logger.info(f"  - Tipo de evento: {event_type}")
        logger.debug(f"  - Datos del evento: {json.dumps(event_data, indent=2, default=str)}")
        
        # Manejar eventos de pago
        if event_type == 'order.paid':
            order = event_data.get('object', {})
            order_id = order.get('id')
            
            logger.info(f"📍 EVENTO: ORDEN PAGADA (order.paid)")
            logger.info(f"  - Order ID: {order_id}")
            
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'pagado'
                orden.save()
                logger.info(f"✓ Orden actualizada: #{orden.id} → Status: pagado")
            except Orden.DoesNotExist:
                logger.warning(f"⚠️ Orden no encontrada para order_id: {order_id}")

        elif event_type == 'charge.paid':
            charge = event_data.get('object', {})
            order_id = charge.get('order_id')
            charge_id = charge.get('id')
            
            logger.info(f"📍 EVENTO: CARGO PAGADO (charge.paid)")
            logger.info(f"  - Order ID: {order_id}")
            logger.info(f"  - Charge ID: {charge_id}")
            
            # Buscar la orden relacionada
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'pagado'
                orden.save()
                logger.info(f"✓ Orden actualizada: #{orden.id} → Status: pagado")
            except Orden.DoesNotExist:
                logger.warning(f"⚠️ Orden no encontrada para order_id: {order_id}")
        
        elif event_type == 'charge.under_review':
            charge = event_data.get('object', {})
            order_id = charge.get('order_id')
            
            logger.info(f"📍 EVENTO: PAGO EN REVISIÓN")
            logger.info(f"  - Order ID: {order_id}")
            
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'revisión'
                orden.save()
                logger.info(f"✓ Orden actualizada: #{orden.id} → Status: revisión")
            except Orden.DoesNotExist:
                logger.warning(f"⚠️ Orden no encontrada para order_id: {order_id}")
        
        elif event_type == 'charge.refunded':
            charge = event_data.get('object', {})
            order_id = charge.get('order_id')
            
            logger.info(f"📍 EVENTO: PAGO REEMBOLSADO")
            logger.info(f"  - Order ID: {order_id}")
            
            try:
                orden = Orden.objects.get(conekta_order_id=order_id)
                orden.status = 'reembolsado'
                orden.save()
                logger.info(f"✓ Orden actualizada: #{orden.id} → Status: reembolsado")
            except Orden.DoesNotExist:
                logger.warning(f"⚠️ Orden no encontrada para order_id: {order_id}")
        
        else:
            logger.warning(f"⚠️ Tipo de evento no manejado: {event_type}")
        
        logger.info("="*80 + "\n")
        return JsonResponse({
            'success': True,
            'webhook_processed': True
        })
    
    except Exception as e:
        logger.exception(f"ERROR PROCESANDO WEBHOOK:")
        logger.error(f"  - Tipo: {type(e).__name__}")
        logger.error(f"  - Detalle: {str(e)}")
        logger.error("="*80 + "\n")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ───────────────────────────────────────────────────────────────
# 3.5 AJAX - Crear Checkout de Conekta (Nueva ruta)
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def crear_checkout_conekta(request):
    """
    Crea un checkout en Conekta via API HTTP.
    Requiere: carrito_id
    Retorna: checkout_id y orden_id de Conekta
    """
    logger.info("\n" + "="*80)
    logger.info("[CREAR_CHECKOUT_CONEKTA] INICIANDO")
    logger.info("="*80)
    
    try:
        logger.info("Parseando JSON del body...")
        data = json.loads(request.body)
        carrito_id = data.get('carrito_id')
        logger.info(f"[OK] Body parseado | carrito_id: {carrito_id}")
        
        if not carrito_id:
            logger.warning("carrito_id no proporcionado en request")
            return JsonResponse({
                'success': False,
                'error': 'carrito_id requerido'
            }, status=400)
        
        # Obtener carrito y cliente
        logger.info(f"Buscando carrito #{carrito_id}...")
        carrito = get_object_or_404(Carrito, id=carrito_id)
        logger.info(f"[OK] Carrito encontrado")
        
        cliente = carrito.cliente
        
        if not cliente:
            logger.error("Carrito sin cliente asociado")
            return JsonResponse({
                'success': False,
                'error': 'Carrito sin cliente asociado'
            }, status=400)
        
        logger.info(f"[OK] Cliente: {cliente.username} ({cliente.correo})")
        
        # Calcular items y total
        logger.info("Procesando items del carrito...")
        line_items = []
        total_centavos = 0
        items_count = 0
        
        for cp in carrito.items.select_related('variante__producto').all():
            items_count += 1
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            
            precio_en_centavos = int(float(precio) * 100)
            subtotal = precio_en_centavos * cp.cantidad
            total_centavos += subtotal
            
            logger.debug(f"  Item #{items_count}: {producto.nombre} | Qty: {cp.cantidad} | Precio: {precio} MXN | Subtotal: {subtotal} centavos")
            
            line_items.append({
                "name": f"{producto.nombre}",
                "description": f"Talla: {variante.talla}, Color: {variante.color}",
                "unit_price": precio_en_centavos,
                "quantity": cp.cantidad,
                "sku": f"VAR-{variante.id}"
            })
        
        logger.info(f"[OK] Procesamiento completado: {items_count} items | Total: {total_centavos/100} MXN")
        
        # URLs de redirección (NO incluir en el payload para sandbox)
        # En producción, estas URLs deben ser públicas y accesibles
        logger.info(f"URLs de redirección configuradas:")
        logger.debug(f"  - Éxito: http://127.0.0.1:8000/pago/exitoso/?carrito={carrito_id}")
        logger.debug(f"  - Fallo: http://127.0.0.1:8000/pago/cancelado/?carrito={carrito_id}")
        
        # Payload para crear orden en Conekta
        logger.info("Construyendo payload para Conekta...")
        payload = {
            "currency": "MXN",
            "line_items": line_items,
            "customer_info": {
                "name": cliente.nombre or cliente.username,
                "email": cliente.correo,
                "phone": cliente.telefono or "+5200000000000"
            },
            "checkout": {
                "allowed_payment_methods": [
                    "card",
                    "cash",
                    "bank_transfer"
                ],
                "monthly_installments_enabled": True,
                "monthly_installments_options": [3, 6, 9, 12],
                "needs_shipping_contact": False
            },
            "metadata": {
                "carrito_id": str(carrito.id),
                "cliente_id": str(cliente.id),
                "source": "django_ecommerce"
            }
        }
        
        logger.info(f"Payload construido:")
        logger.debug(f"  Payload completo: {json.dumps(payload, indent=2, default=str)}")
        
        logger.info(f"Enviando petición POST a Conekta API...")
        logger.info(f"  Endpoint: {CONEKTA_BASE_URL}/orders")
        
        # Realizar petición POST a Conekta
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
        
        logger.info(f"Respuesta Conekta - Status HTTP: {response.status_code}")
        logger.debug(f"Response Body (primeros 1000 chars): {response.text[:1000]}")
        
        # Intentar parsear la respuesta
        try:
            response_data = response.json()
        except:
            logger.error(f"No se pudo parsear JSON de respuesta Conekta")
            return JsonResponse({
                'success': False,
                'error': f'Respuesta inválida de Conekta (status {response.status_code})'
            }, status=response.status_code)
        
        if response.status_code in [200, 201]:
            order_id = response_data.get('id')
            
            # Obtener el checkout_id del objeto checkout
            checkout_data = response_data.get('checkout', {})
            checkout_id = checkout_data.get('id')
            checkout_status = checkout_data.get('status')
            
            logger.info(f"[SUCCESS] ORDEN CREADA EXITOSAMENTE EN CONEKTA:")
            logger.info(f"  - Order ID: {order_id}")
            logger.info(f"  - Checkout ID: {checkout_id}")
            logger.info(f"  - Checkout Status: {checkout_status}")
            logger.info(f"  - Amount: {response_data.get('amount')} centavos ({response_data.get('amount')/100} MXN)")
            logger.debug(f"  - Full Checkout Object: {json.dumps(checkout_data, indent=2, default=str)}")
            
            # ──────────────────────────────────────────────────────────
            # CREAR ORDEN LOCAL (PENDIENTE DE PAGO)
            # ──────────────────────────────────────────────────────────
            try:
                # SIEMPRE crear una nueva orden (no actualizamos órdenes existentes)
                logger.info(f"Creando nueva orden local para carrito {carrito.id}...")
                
                orden = Orden.objects.create(
                    cliente=cliente,
                    carrito=None,  # Sin vincular - permite múltiples órdenes
                    total_amount=Decimal(str(total_centavos / 100)),
                    status='pendiente_pago',
                    payment_method='conekta',
                    conekta_order_id=order_id
                )
                logger.info(f"[OK] Orden #{orden.id} creada exitosamente")
                
                # Crear detalles de la orden
                for cp in carrito.items.select_related('variante__producto').all():
                    variante = cp.variante
                    producto = variante.producto
                    precio = variante.precio if variante.precio else producto.precio
                    
                    OrdenDetalle.objects.create(
                        order=orden,
                        variante=variante,
                        cantidad=cp.cantidad,
                        precio_unitario=precio
                    )
                logger.info(f"[OK] Detalles de orden guardados exitosamente")
                
                # VACIAR EL CARRITO (eliminar items y marcar como vacío)
                carrito.items.all().delete()
                carrito.status = 'vacio'
                carrito.save()
                logger.info(f"[OK] Carrito #{carrito.id} vaciado correctamente")
                
            except Exception as e:
                logger.error(f"Error al gestionar orden local: {e}")
                # Continuamos para no bloquear el checkout, el webhook podría corregirlo después

            logger.info("="*80 + "\n")
            
            return JsonResponse({
                'success': True,
                'order_id': order_id,
                'checkout_id': checkout_id,
                'public_key': settings.CONEKTA_PUBLIC_KEY
            })
        
        else:
            error_msg = f"Error Conekta ({response.status_code}): {response.text}"
            logger.error(f"ERROR AL CREAR ORDEN EN CONEKTA:")
            logger.error(f"  - HTTP Status: {response.status_code}")
            logger.error(f"  - Response: {response.text}")
            logger.error("="*80 + "\n")
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=response.status_code)
    
    except json.JSONDecodeError as e:
        logger.error(f"ERROR AL PARSEAR JSON:")
        logger.error(f"  - JSONDecodeError: {str(e)}")
        logger.error(f"  - Body: {request.body[:500]}")
        logger.error("="*80 + "\n")
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido en el body'
        }, status=400)
    except requests.RequestException as e:
        logger.error(f"ERROR DE CONEXIÓN CON CONEKTA:")
        logger.error(f"  - Tipo: {type(e).__name__}")
        logger.error(f"  - Detalle: {str(e)}")
        logger.error("="*80 + "\n")
        return JsonResponse({
            'success': False,
            'error': f'Error de conexión con Conekta: {str(e)}'
        }, status=503)
    except Exception as e:
        logger.exception(f"ERROR GENERAL EN CREAR_CHECKOUT:")
        logger.error(f"  - Tipo: {type(e).__name__}")
        logger.error(f"  - Detalle: {str(e)}")
        logger.error("="*80 + "\n")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ───────────────────────────────────────────────────────────────
# 4. Páginas de resultado
# ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
@require_http_methods(["GET"])
def pago_exitoso(request):
    """Página de pago completado exitosamente"""
    # Obtener orden_id o carrito de los query params
    orden_id = request.GET.get('orden_id')
    carrito_id = request.GET.get('carrito')
    
    context = {}
    orden = None
    
    try:
        if orden_id:
            orden = Orden.objects.get(id=orden_id)
            context['orden'] = orden
            logger.info(f"[PAGO_EXITOSO] Mostrando página de éxito con orden #{orden.id}")
                
        elif carrito_id:
            # Buscar la orden más reciente para este cliente (ya no está vinculada al carrito)
            # El carrito_id aquí es solo para referencia, buscamos por conekta_order_id o la más reciente
            try:
                # Intentar buscar por el carrito original (aunque ya esté desvinculado)
                carrito = Carrito.objects.get(id=carrito_id)
                # Buscar la orden más reciente del cliente
                orden = Orden.objects.filter(cliente=carrito.cliente).order_by('-created_at').first()
                if orden:
                    context['orden'] = orden
                    logger.info(f"[PAGO_EXITOSO] Mostrando página de éxito para cliente -> Orden #{orden.id}")
            except Carrito.DoesNotExist:
                logger.warning(f"[PAGO_EXITOSO] Carrito #{carrito_id} no encontrado")
            
    except Orden.DoesNotExist:
        logger.warning(f"[PAGO_EXITOSO] Orden no encontrada para orden_id={orden_id}")
    except Exception as e:
        logger.error(f"[PAGO_EXITOSO] Error buscando orden: {e}")
    
    return render(request, 'public/pago/pago_exitoso.html', context)


@require_http_methods(["GET"])
def pago_cancelado(request):
    """Página de pago cancelado"""
    return render(request, 'public/pago/pago_cancelado.html')


# ───────────────────────────────────────────────────────────────
# Verificar estado de la orden después del pago
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["GET"])
def verificar_orden_creada(request):
    """
    Verifica si la orden fue creada exitosamente después del pago.
    Usado por el frontend para confirmar que la orden existe.
    """
    carrito_id = request.GET.get('carrito_id')
    
    if not carrito_id:
        return JsonResponse({
            'success': False,
            'error': 'carrito_id requerido'
        }, status=400)
    
    try:
        # Buscar orden por carrito_id
        orden = Orden.objects.get(conekta_order_id=carrito_id)
        
        logger.info(f"[VERIFICAR_ORDEN] Orden encontrada: #{orden.id} para carrito {carrito_id}")
        
        return JsonResponse({
            'success': True,
            'orden_id': orden.id,
            'status': orden.status,
            'total_amount': str(orden.total_amount),
            'created_at': orden.created_at.isoformat() if orden.created_at else None,
            'detalles_count': orden.detalles.count()
        })
    
    except Orden.DoesNotExist:
        logger.warning(f"[VERIFICAR_ORDEN] Orden NO encontrada para carrito {carrito_id}")
        return JsonResponse({
            'success': False,
            'error': 'Orden no encontrada',
            'carrito_id': carrito_id
        }, status=404)
    
    except Exception as e:
        logger.exception(f"[VERIFICAR_ORDEN] Error: {type(e).__name__}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ───────────────────────────────────────────────────────────────
# Sincronizar estado de orden con Conekta (para desarrollo local)
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST", "GET"])
def sincronizar_orden_conekta(request):
    """
    Consulta el estado de una orden directamente en Conekta y actualiza la BD local.
    Útil para desarrollo local donde los webhooks no funcionan.
    """
    orden_id = request.GET.get('orden_id') or request.POST.get('orden_id')
    
    if not orden_id:
        return JsonResponse({
            'success': False,
            'error': 'orden_id requerido (ID local de la orden)'
        }, status=400)
    
    try:
        # Buscar la orden local
        orden = Orden.objects.get(id=orden_id)
        conekta_order_id = orden.conekta_order_id
        
        if not conekta_order_id:
            return JsonResponse({
                'success': False,
                'error': 'Esta orden no tiene un ID de Conekta asociado'
            }, status=400)
        
        logger.info(f"[SYNC] Consultando estado de orden {conekta_order_id} en Conekta...")
        
        # Consultar Conekta API
        headers = {
            "Authorization": f"Bearer {settings.CONEKTA_API_KEY}",
            "Accept": "application/vnd.conekta-v2.0.0+json",
            "Content-Type": "application/json",
        }
        
        response = requests.get(
            f"{CONEKTA_BASE_URL}/orders/{conekta_order_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            conekta_data = response.json()
            payment_status = conekta_data.get('payment_status', '')
            
            logger.info(f"[SYNC] Estado en Conekta: {payment_status}")
            
            # Mapear estados de Conekta a estados locales
            status_anterior = orden.status
            if payment_status == 'paid':
                orden.status = 'pagado'
            elif payment_status == 'pending_payment':
                orden.status = 'pendiente_pago'
            elif payment_status == 'declined':
                orden.status = 'rechazado'
            elif payment_status == 'expired':
                orden.status = 'expirado'
            elif payment_status == 'refunded':
                orden.status = 'reembolsado'
            
            orden.save()
            
            logger.info(f"[SYNC] Orden #{orden.id} actualizada: {status_anterior} -> {orden.status}")
            
            return JsonResponse({
                'success': True,
                'orden_id': orden.id,
                'conekta_order_id': conekta_order_id,
                'status_anterior': status_anterior,
                'status_nuevo': orden.status,
                'conekta_payment_status': payment_status
            })
        else:
            logger.error(f"[SYNC] Error consultando Conekta: {response.status_code} - {response.text}")
            return JsonResponse({
                'success': False,
                'error': f'Error de Conekta: {response.status_code}'
            }, status=response.status_code)
            
    except Orden.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Orden #{orden_id} no encontrada'
        }, status=404)
    except Exception as e:
        logger.exception(f"[SYNC] Error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
