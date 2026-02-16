"""
Vista para integrar pagos con Stripe
Pasarela de pagos internacional - Stripe Checkout Embebido + Webhooks
"""
import json
import logging
import stripe
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from ..models import Carrito, Orden, OrdenDetalle, Cliente

# ───────────────────────────────────────────────────────────────
# Logger
# ───────────────────────────────────────────────────────────────
logger = logging.getLogger('stripe_payments')
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.FileHandler('stripe_payments.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger.debug(f"[INIT] stripe.api_key configurado: {stripe.api_key[:30] if stripe.api_key else 'NONE'}...")


# ───────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────
def _calcular_items_carrito(carrito):
    """
    Calcula items del carrito con lógica de mayoreo.
    Retorna: (line_items_stripe, total_centavos, items_detalle, aplicar_mayoreo)
    """
    carrito_items = list(carrito.items.select_related('variante__producto').all())
    total_piezas = sum(cp.cantidad for cp in carrito_items)
    aplicar_mayoreo = total_piezas >= 6

    line_items = []
    items_detalle = []
    total_centavos = 0

    for cp in carrito_items:
        variante = cp.variante
        producto = variante.producto

        if aplicar_mayoreo:
            precio = float(
                variante.precio_mayorista if variante.precio_mayorista > 0
                else producto.precio_mayorista
            )
        else:
            precio = float(variante.precio if variante.precio else producto.precio)

        precio_centavos = int(precio * 100)
        subtotal = precio_centavos * cp.cantidad
        total_centavos += subtotal

        # Formato requerido por Stripe Checkout Session
        line_items.append({
            'price_data': {
                'currency': 'mxn',
                'product_data': {
                    'name': producto.nombre,
                    'description': f"Talla: {cp.talla}, Color: {variante.color}",
                },
                'unit_amount': precio_centavos,
            },
            'quantity': cp.cantidad,
        })

        items_detalle.append({
            'variante': variante,
            'producto': producto,
            'cantidad': cp.cantidad,
            'precio_unitario': Decimal(str(precio)),
            'talla': cp.talla,
        })

    return line_items, total_centavos, items_detalle, aplicar_mayoreo


def _crear_orden_local(carrito, cliente, total_centavos, items_detalle,
                       stripe_session_id='', stripe_payment_intent='',
                       status='pendiente_pago'):
    """
    Crea la Orden y sus OrdenDetalle en la BD local.
    """
    orden = Orden.objects.create(
        cliente=cliente,
        carrito=None,   # Sin vincular para permitir múltiples órdenes
        total_amount=Decimal(str(total_centavos / 100)),
        status=status,
        payment_method='stripe',
        stripe_session_id=stripe_session_id,
        stripe_payment_intent=stripe_payment_intent,
    )

    for item in items_detalle:
        OrdenDetalle.objects.create(
            order=orden,
            variante=item['variante'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio_unitario'],
            talla=item.get('talla', 'UNICA'),
        )

    return orden


# ───────────────────────────────────────────────────────────────
# 1. POST/AJAX - Crear Stripe Checkout Session (flujo principal)
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def crear_checkout_stripe(request):
    """
    Crea una Stripe Checkout Session en modo embebido.
    Retorna el client_secret para montar el Embedded Checkout
    en el frontend con Stripe.js.
    """
    logger.info("=" * 80)
    logger.info("[CREAR_CHECKOUT_STRIPE] INICIANDO")

    try:
        data = json.loads(request.body)
        carrito_id = data.get('carrito_id')

        if not carrito_id:
            return JsonResponse({
                'success': False,
                'error': 'carrito_id requerido'
            }, status=400)

        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente

        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Carrito sin cliente asociado'
            }, status=400)

        logger.info(f"Carrito #{carrito_id} | Cliente: {cliente.username} ({cliente.correo})")

        # Calcular items
        line_items, total_centavos, items_detalle, mayoreo = _calcular_items_carrito(carrito)

        if not line_items:
            return JsonResponse({
                'success': False,
                'error': 'El carrito está vacío'
            }, status=400)

        logger.info(f"Items: {len(line_items)} | Total: {total_centavos / 100} MXN | Mayoreo: {mayoreo}")

        # Verificar que stripe.api_key esté configurado
        if not stripe.api_key:
            logger.error("❌ stripe.api_key está VACÍO")
            return JsonResponse({'success': False, 'error': 'Error de configuración: API key de Stripe no configurada'}, status=500)
        else:
            logger.info(f"✅ stripe.api_key configurado: {stripe.api_key[:30]}...")

        # URL de retorno después del pago (Stripe redirige aquí)
        base_url = request.build_absolute_uri('/')[:-1]
        return_url = f"{base_url}/pago/exitoso/?session_id={{CHECKOUT_SESSION_ID}}"

        # ─── Crear Stripe Checkout Session (embebido) ───
        session = stripe.checkout.Session.create(
            ui_mode='embedded',
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            return_url=return_url,
            customer_email=cliente.correo,
            metadata={
                'carrito_id': str(carrito.id),
                'cliente_id': str(cliente.id),
            },
            payment_intent_data={
                'metadata': {
                    'carrito_id': str(carrito.id),
                    'cliente_id': str(cliente.id),
                },
            },
        )

        logger.info(f"Stripe Session creada: {session.id}")
        logger.info(f"Client Secret: {session.client_secret[:30]}...")

        # Crear orden local pendiente de pago
        orden = _crear_orden_local(
            carrito, cliente, total_centavos, items_detalle,
            stripe_session_id=session.id,
            status='pendiente_pago',
        )
        logger.info(f"Orden local #{orden.id} creada (pendiente_pago)")

        # Vaciar carrito
        carrito.items.all().delete()
        carrito.status = 'vacio'
        carrito.save()
        logger.info(f"Carrito #{carrito.id} vaciado")

        return JsonResponse({
            'success': True,
            'client_secret': session.client_secret,
            'session_id': session.id,
        })

    except stripe.error.StripeError as e:
        msg = e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)
        logger.error(f"Stripe Error: {msg}")
        return JsonResponse({
            'success': False,
            'error': f'Error de Stripe: {msg}'
        }, status=400)

    except json.JSONDecodeError:
        logger.error("JSON inválido en el body")
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)

    except Exception as e:
        logger.exception(f"Error general: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ───────────────────────────────────────────────────────────────
# 2. GET - Mostrar formulario de pago con Stripe (standalone)
# ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
def mostrar_formulario_pago_stripe(request, carrito_id):
    """
    Muestra una página standalone de pago con Stripe Checkout embebido.
    Alternativa al flujo multi-step del carrito.
    """
    logger.info(f"[FORMULARIO_PAGO_STRIPE] Carrito #{carrito_id}")

    try:
        carrito = get_object_or_404(Carrito, id=carrito_id)
        cliente = carrito.cliente

        if not cliente:
            return JsonResponse({'error': 'Carrito sin cliente asociado'}, status=400)

        total = Decimal('0.00')
        items_detalle = []

        for cp in carrito.items.select_related('variante__producto').all():
            variante = cp.variante
            producto = variante.producto
            precio = variante.precio if variante.precio else producto.precio
            subtotal = Decimal(str(precio)) * cp.cantidad
            total += subtotal

            variante_principal = producto.variante_principal
            galeria = []
            if variante_principal:
                galeria = [img.imagen.url for img in variante_principal.imagenes.all() if img.imagen]
            imagen = galeria[0] if galeria else "/static/images/no-image.jpg"

            items_detalle.append({
                'producto': producto.nombre,
                'variante': f"{cp.talla} - {variante.color}",
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
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        }

        return render(request, 'public/pago/checkout_stripe.html', context)

    except Exception as e:
        logger.exception(f"Error en formulario_pago_stripe: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ───────────────────────────────────────────────────────────────
# 3. POST - Webhook de Stripe
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def webhook_stripe(request):
    """
    Recibe eventos de Stripe y actualiza el estado de la orden.
    Eventos manejados:
      - checkout.session.completed
      - payment_intent.succeeded
      - payment_intent.payment_failed
      - charge.refunded
    """
    logger.info("=" * 80)
    logger.info("[WEBHOOK_STRIPE] EVENTO RECIBIDO")

    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', '')

    # Verificar firma del webhook
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Payload inválido")
        return JsonResponse({'error': 'Payload inválido'}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Firma de webhook inválida")
        return JsonResponse({'error': 'Firma inválida'}, status=401)

    event_type = event['type']
    event_data = event['data']['object']
    logger.info(f"Evento: {event_type} | ID: {event_data.get('id', 'N/A')}")

    # ── checkout.session.completed ──
    if event_type == 'checkout.session.completed':
        session_id = event_data['id']
        payment_intent_id = event_data.get('payment_intent', '')
        payment_status = event_data.get('payment_status', '')

        logger.info(f"Session: {session_id} | PI: {payment_intent_id} | Status: {payment_status}")

        try:
            orden = Orden.objects.get(stripe_session_id=session_id)

            if payment_status == 'paid':
                orden.status = 'procesando'
            else:
                orden.status = 'pendiente_pago'

            if payment_intent_id:
                orden.stripe_payment_intent = payment_intent_id

            orden.save()
            logger.info(f"Orden #{orden.id} actualizada → {orden.status}")

        except Orden.DoesNotExist:
            logger.warning(f"Orden no encontrada para session: {session_id}")

    # ── payment_intent.succeeded ──
    elif event_type == 'payment_intent.succeeded':
        pi_id = event_data['id']
        logger.info(f"PaymentIntent exitoso: {pi_id}")

        try:
            orden = Orden.objects.get(stripe_payment_intent=pi_id)
            orden.status = 'pagado'
            orden.save()
            logger.info(f"Orden #{orden.id} → pagado")
        except Orden.DoesNotExist:
            logger.warning(f"Orden no encontrada para PI: {pi_id}")

    # ── payment_intent.payment_failed ──
    elif event_type == 'payment_intent.payment_failed':
        pi_id = event_data['id']
        error_msg = event_data.get('last_payment_error', {}).get('message', '')
        logger.warning(f"PaymentIntent fallido: {pi_id} | Error: {error_msg}")

        try:
            orden = Orden.objects.get(stripe_payment_intent=pi_id)
            orden.status = 'rechazado'
            orden.save()
            logger.info(f"Orden #{orden.id} → rechazado")
        except Orden.DoesNotExist:
            logger.warning(f"Orden no encontrada para PI fallido: {pi_id}")

    # ── charge.refunded ──
    elif event_type == 'charge.refunded':
        pi_id = event_data.get('payment_intent', '')
        logger.info(f"Reembolso para PI: {pi_id}")

        try:
            orden = Orden.objects.get(stripe_payment_intent=pi_id)
            orden.status = 'reembolsado'
            orden.save()
            logger.info(f"Orden #{orden.id} → reembolsado")
        except Orden.DoesNotExist:
            logger.warning(f"Orden no encontrada para reembolso PI: {pi_id}")

    else:
        logger.info(f"Evento no manejado: {event_type}")

    return JsonResponse({'success': True, 'event': event_type})


# ───────────────────────────────────────────────────────────────
# 4. Verificar estado de la orden
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["GET"])
def verificar_orden_creada(request):
    """
    Verifica si la orden fue creada y su estado actual.
    Acepta: session_id o orden_id como query param.
    """
    session_id = request.GET.get('session_id')
    orden_id = request.GET.get('orden_id')

    try:
        if session_id:
            orden = Orden.objects.get(stripe_session_id=session_id)
        elif orden_id:
            orden = Orden.objects.get(id=orden_id)
        else:
            return JsonResponse({
                'success': False,
                'error': 'session_id u orden_id requerido'
            }, status=400)

        return JsonResponse({
            'success': True,
            'orden_id': orden.id,
            'status': orden.status,
            'total_amount': str(orden.total_amount),
            'created_at': orden.created_at.isoformat() if orden.created_at else None,
            'detalles_count': orden.detalles.count(),
        })

    except Orden.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Orden no encontrada'
        }, status=404)
    except Exception as e:
        logger.exception(f"Error verificando orden: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ───────────────────────────────────────────────────────────────
# 5. Sincronizar estado con Stripe (para dev local)
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST", "GET"])
def sincronizar_orden_stripe(request):
    """
    Consulta el estado de un PaymentIntent o Session en Stripe
    y actualiza la BD local. Útil en desarrollo local donde
    los webhooks no llegan.
    """
    orden_id = request.GET.get('orden_id') or request.POST.get('orden_id')

    if not orden_id:
        return JsonResponse({
            'success': False,
            'error': 'orden_id requerido'
        }, status=400)

    try:
        orden = Orden.objects.get(id=orden_id)
        status_anterior = orden.status

        if orden.stripe_session_id:
            session = stripe.checkout.Session.retrieve(orden.stripe_session_id)
            payment_status = session.get('payment_status', '')
            pi_id = session.get('payment_intent', '')

            if pi_id and not orden.stripe_payment_intent:
                orden.stripe_payment_intent = pi_id

            status_map = {
                'paid': 'pagado',
                'unpaid': 'pendiente_pago',
                'no_payment_required': 'pagado',
            }
            orden.status = status_map.get(payment_status, orden.status)

        elif orden.stripe_payment_intent:
            pi = stripe.PaymentIntent.retrieve(orden.stripe_payment_intent)
            pi_status = pi.get('status', '')

            status_map = {
                'succeeded': 'pagado',
                'processing': 'procesando',
                'requires_payment_method': 'pendiente_pago',
                'requires_action': 'pendiente_pago',
                'canceled': 'cancelado',
            }
            orden.status = status_map.get(pi_status, orden.status)

        else:
            return JsonResponse({
                'success': False,
                'error': 'Orden sin IDs de Stripe asociados'
            }, status=400)

        orden.save()
        logger.info(f"[SYNC] Orden #{orden.id}: {status_anterior} → {orden.status}")

        return JsonResponse({
            'success': True,
            'orden_id': orden.id,
            'status_anterior': status_anterior,
            'status_nuevo': orden.status,
        })

    except Orden.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Orden #{orden_id} no encontrada'
        }, status=404)
    except stripe.error.StripeError as e:
        logger.error(f"[SYNC] Stripe Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception(f"[SYNC] Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ───────────────────────────────────────────────────────────────
# 6. Páginas de resultado
# ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
def pago_exitoso(request):
    """Página de pago completado exitosamente."""
    session_id = request.GET.get('session_id')
    orden_id = request.GET.get('orden_id')

    context = {}
    orden = None

    try:
        if session_id:
            try:
                orden = Orden.objects.get(stripe_session_id=session_id)

                # Si la orden aún está pendiente, sincronizar con Stripe
                if orden.status == 'pendiente_pago':
                    try:
                        session = stripe.checkout.Session.retrieve(session_id)
                        if session.payment_status == 'paid':
                            orden.status = 'procesando'
                            orden.stripe_payment_intent = session.payment_intent or ''
                            orden.save()
                            logger.info(f"[PAGO_EXITOSO] Orden #{orden.id} sincronizada → procesando")
                    except stripe.error.StripeError as e:
                        logger.warning(f"[PAGO_EXITOSO] Error sincronizando: {e}")

            except Orden.DoesNotExist:
                logger.warning(f"[PAGO_EXITOSO] Orden no encontrada para session={session_id}")

        elif orden_id:
            try:
                orden = Orden.objects.get(id=orden_id)
            except Orden.DoesNotExist:
                logger.warning(f"[PAGO_EXITOSO] Orden #{orden_id} no encontrada")

        if orden:
            context['orden'] = orden

    except Exception as e:
        logger.error(f"[PAGO_EXITOSO] Error: {e}")

    return render(request, 'public/pago/pago_exitoso.html', context)


@require_http_methods(["GET"])
def pago_cancelado(request):
    """Página de pago cancelado."""
    return render(request, 'public/pago/pago_cancelado.html')


# ───────────────────────────────────────────────────────────────
# 7. API - Estado de sesión de Stripe (para polling del frontend)
# ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["GET"])
def session_status(request):
    """
    El frontend puede consultar este endpoint para verificar el estado
    de la sesión de Stripe Checkout.
    """
    session_id = request.GET.get('session_id')

    if not session_id:
        return JsonResponse({
            'success': False,
            'error': 'session_id requerido'
        }, status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        return JsonResponse({
            'success': True,
            'status': session.status,
            'payment_status': session.payment_status,
            'customer_email': (
                session.customer_details.email
                if session.customer_details else None
            ),
        })

    except stripe.error.StripeError as e:
        logger.error(f"Error consultando session: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
