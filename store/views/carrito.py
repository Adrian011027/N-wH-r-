# store/views/carrito.py
# ==============================================================
from venv import logger
from django.forms import model_to_dict
from django.shortcuts            import get_object_or_404, render
from django.db                   import models, transaction
from django.db.models            import Sum
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from store.views.decorators      import login_required_client, jwt_role_required
from store.views.orden import crear_orden_desde_payload
from ..models import (
    Cliente, Carrito, Producto, AtributoValor,
    Variante, CarritoProducto, Orden
)
from django.urls import reverse
from django.core.signing import TimestampSigner

import json
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from twilio.rest import Client
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

signer = TimestampSigner()
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# ───────────────────────────────────────────────────────────────
# Helpers de carrito
# ───────────────────────────────────────────────────────────────
def get_carrito_activo_cliente(cliente):
    """
    Devuelve UN carrito activo por cliente.
    • Si ya existe(n) → se queda con el más reciente (id más alto).
    • Si no existe    → lo crea.
    • Siempre elimina duplicados para evitar MultipleObjectsReturned.
    """
    # 1) Buscar TODOS los carritos activos de este cliente
    activos = (Carrito.objects
                        .filter(cliente=cliente, status="activo")
                        .order_by("-id"))          # más nuevo primero

    if activos:
        carrito = activos[0]                       # conserva primero
        # 2) Borra duplicados (todo lo demás)
        activos.exclude(id=carrito.id).delete()
    else:
        # 3) No había ninguno: se crea uno
        carrito = Carrito.objects.create(
            cliente     = cliente,
            status      = "activo",
            session_key = None
        )
    return carrito

def get_carrito_by_session(session_key):
    """Carrito de invitado (puede ser None)."""
    return (
        Carrito.objects
        .filter(cliente__isnull=True, session_key=session_key)
        .first()
    )

# -----------------------------------------------------------------
# 0. Detalle de carrito para invitados (session_key)
# -----------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def detalle_carrito_session(request):
    carrito = get_carrito_by_session(request.session.session_key)
    if not carrito:
        return JsonResponse({"items": [], "mayoreo": False}, status=200)
    return _build_detalle_response(carrito)

# -----------------------------------------------------------------
# 1. Crear / actualizar carrito  (cliente_id == 0 → invitado)
# -----------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def create_carrito(request, cliente_id):
    try:
        data       = json.loads(request.body)
        prod_id    = int(data["producto_id"])
        cantidad   = int(data.get("cantidad", 1))
        talla_val  = (data.get("talla") or "").strip()
    except (json.JSONDecodeError, KeyError, ValueError):
        return JsonResponse({"error": "JSON inválido o faltan campos"}, status=400)

    if cantidad < 1:
        return JsonResponse({"error": "Cantidad debe ser ≥ 1"}, status=400)

    # ── Invitado vs logueado ───────────────────────────────────
    if cliente_id == 0:                                       # ← invitado
        if not request.session.session_key:
            request.session.save()            # crea session_key si no existe
        cliente     = None
        session_key = request.session.session_key
    else:                                                     # ← logueado
        cliente     = get_object_or_404(Cliente, id=cliente_id)
        session_key = None

    producto = get_object_or_404(Producto, id=prod_id)

    # ── Carrito (uno por usuario o por sesión) ─────────────────
    if cliente is not None:
        # ✅ garantiza UN solo carrito activo por cliente
        carrito = get_carrito_activo_cliente(cliente)
    else:
        # invitado: un carrito por session_key
        carrito, _ = Carrito.objects.get_or_create(
            cliente     = None,
            session_key = session_key,
            defaults    = {"status": "activo"}
        )

    if carrito.status != "activo":               # revive carritos “vacio”
        carrito.status = "activo"
        carrito.save(update_fields=["status"])

    # ── Variante según talla ───────────────────────────────────
    if talla_val:
        atributo_valor = get_object_or_404(
            AtributoValor,
            atributo__nombre__iexact="Talla",
            valor__iexact=talla_val
        )
        variante = get_object_or_404(
            Variante.objects.prefetch_related("attrs"),
            producto=producto,
            attrs__atributo_valor=atributo_valor
        )
    else:
        variante = (
            Variante.objects
            .filter(producto=producto)
            .annotate(
                es_unica=models.Count(
                    "attrs",
                    filter=models.Q(
                        attrs__atributo_valor__atributo__nombre__iexact="Talla"
                    )
                )
            )
            .filter(es_unica=0)      # sin talla → única
            .first()
        )
        if not variante:
            return JsonResponse({"error": "Debes especificar una talla válida"}, status=400)

    if variante.stock < cantidad:
        return JsonResponse({"error": f"Stock insuficiente ({variante.stock})"}, status=409)

    # ── Línea de carrito ───────────────────────────────────────
    cp, creado = CarritoProducto.objects.get_or_create(
        carrito  = carrito,
        variante = variante,
        defaults = {"cantidad": cantidad}
    )
    if not creado:
        nueva_cant = cp.cantidad + cantidad
        if variante.stock < nueva_cant:
            return JsonResponse({"error": f"Stock insuficiente para {nueva_cant} piezas"}, status=409)
        cp.cantidad = nueva_cant
        cp.save(update_fields=["cantidad"])

    precio_unit = float(variante.precio or producto.precio)
    subtotal    = round(precio_unit * cp.cantidad, 2)

    return JsonResponse({
        "mensaje"   : "Producto agregado al carrito",
        "carrito_id": carrito.id,
        "status"    : carrito.status,
        "producto"  : producto.nombre,
        "variante"  : {
            "sku"      : variante.sku,
            "atributos": [str(av) for av in variante.attrs.all()]
        },
        "cantidad"  : cp.cantidad,
        "subtotal"  : subtotal
    }, status=201)


# -----------------------------------------------------------------
# 2. Detalle de carrito (cliente logueado)
# -----------------------------------------------------------------
@csrf_exempt
@jwt_role_required()
@require_http_methods(["GET"])
def detalle_carrito_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    carrito = get_carrito_activo_cliente(cliente)
    return _build_detalle_response(carrito)


# -----------------------------------------------------------------
# 2-B. Builder de respuesta JSON reutilizable
# -----------------------------------------------------------------
def _build_detalle_response(carrito):
    qs = (
        CarritoProducto.objects
        .filter(carrito=carrito)
        .select_related("variante__producto")
        .prefetch_related("variante__attrs__atributo_valor")
    )

    total_piezas    = sum(cp.cantidad for cp in qs)
    aplicar_mayoreo = total_piezas >= 6

    items = []
    for cp in qs:
        var, prod = cp.variante, cp.variante.producto
        precio_unit = (
            float(
                var.precio_mayorista if var.precio_mayorista > 0 else prod.precio_mayorista
            ) if aplicar_mayoreo else
            float(var.precio if var.precio else prod.precio)
        )
        items.append({
            "producto_id"    : prod.id,
            "producto"       : prod.nombre,
            "precio_unitario": precio_unit,
            "precio_menudeo" : float(var.precio if var.precio else prod.precio),
            "precio_mayorista": float(
                var.precio_mayorista if var.precio_mayorista > 0 else prod.precio_mayorista
            ),
            "cantidad"       : cp.cantidad,
            "atributos"      : [str(av) for av in var.attrs.all()],
            "subtotal"       : round(precio_unit * cp.cantidad, 2),
            "variante_id"    : var.id,
            "imagen"           : prod.imagen.url if prod.imagen else None,  
        })

    return JsonResponse({
        "carrito_id": carrito.id,
        "status"    : carrito.status,
        "mayoreo"   : aplicar_mayoreo,
        "items"     : items,
    }, status=200)


# -----------------------------------------------------------------
# 3. Eliminar producto
# -----------------------------------------------------------------
@csrf_exempt
@jwt_role_required()
@require_http_methods(["DELETE"])
def delete_producto_carrito(request, cliente_id, variante_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    carrito = get_carrito_activo_cliente(cliente)
    cp      = get_object_or_404(CarritoProducto, carrito=carrito, variante_id=variante_id)
    cp.delete()
    return JsonResponse({"mensaje": "Producto eliminado del carrito."}, status=200)


# -----------------------------------------------------------------
# 4. Vaciar carrito  (cliente logueado  o  invitado)
# -----------------------------------------------------------------
@csrf_exempt
@jwt_role_required()
@require_http_methods(["DELETE"])
def vaciar_carrito(request, cliente_id):
    # ===============  invitado  ==========================
    if cliente_id == 0:
        # si aún no hay session_key la creamos para poder localizar el carrito
        if not request.session.session_key:
            request.session.save()

        carrito = get_carrito_by_session(request.session.session_key)
        if not carrito:          # invitado sin carrito → ok silencioso
            return JsonResponse({'mensaje': 'Carrito vaciado.'}, status=200)

    # ===============  cliente logueado  =================
    else:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        carrito = get_carrito_activo_cliente(cliente)

    # ── elimina líneas y marca vacío ────────────────────
    carrito.items.all().delete()
    carrito.status = 'vacio'
    carrito.save(update_fields=['status'])

    return JsonResponse({'mensaje': 'Carrito vaciado.'}, status=200)


@csrf_exempt
@require_http_methods(["DELETE"])
def vaciar_carrito_guest(request):
    # invitado = por session_key
    carrito = get_carrito_by_session(request.session.session_key)
    if not carrito:
        return JsonResponse({'mensaje': 'Ya estaba vacío.'}, status=200)

    carrito.items.all().delete()
    carrito.status = 'vacio'
    carrito.save(update_fields=['status'])
    return JsonResponse({'mensaje': 'Carrito vaciado.'}, status=200)


# -----------------------------------------------------------------
# 5. PATCH cantidad (con bloqueo de fila)
# -----------------------------------------------------------------
@csrf_exempt
@jwt_role_required()
@require_http_methods(["PATCH"])
def actualizar_cantidad_producto(request, cliente_id, variante_id):
    try:
        cantidad = int(json.loads(request.body).get("cantidad", 0))
        if cantidad < 1:
            raise ValueError
    except Exception:
        return JsonResponse({"error": "JSON inválido o faltan campos"}, status=400)

    cliente = get_object_or_404(Cliente, id=cliente_id)
    carrito = get_carrito_activo_cliente(cliente)

    with transaction.atomic():
        cp = (
            CarritoProducto.objects
            .select_for_update()
            .get(carrito=carrito, variante_id=variante_id)
        )
        cp.cantidad = cantidad
        cp.save(update_fields=["cantidad"])

    return _build_detalle_response(carrito)


# -----------------------------------------------------------------
# 6. Vista protegida (cliente logueado)
# -----------------------------------------------------------------
@login_required_client
def carrito_cliente(request):
    # Reutiliza la vista unificada
    return carrito_publico(request)


# 7. Vista pública (invitado / logueado)
# -----------------------------------------------------------------

def carrito_publico(request):
    # 🔐 Forzar la creación de la session_key (clave para carritos de invitados)
    if not request.session.session_key:
        request.session.save()

    cliente_id  = request.session.get("cliente_id")
    session_key = request.session.session_key

    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        carrito = get_carrito_activo_cliente(cliente)
    else:
        carrito = get_carrito_by_session(session_key)

    datos = _carrito_to_template(carrito)

    return render(
        request,
        "public/carrito/carrito.html",
        {
            "productos": datos["items"],
            "mayoreo": datos["mayoreo"],
            "session_key": session_key,  # Puedes usarlo en el HTML si quieres
            "carrito": carrito,
        }
    )


# -----------------------------------------------------------------
# 8. Helper: convierte un Carrito para la plantilla
# -----------------------------------------------------------------
def _carrito_to_template(carrito):
    if not carrito:
        return {"items": [], "mayoreo": False}

    qs             = (
        carrito.items
        .select_related("variante__producto")
        .prefetch_related("variante__attrs__atributo_valor")
    )
    total_piezas   = sum(it.cantidad for it in qs)
    aplicar_mayoro = total_piezas >= 6

    items = []
    for it in qs:
        prod, var = it.variante.producto, it.variante
        precio_unit = (
            float(var.precio_mayorista if var.precio_mayorista > 0 else prod.precio_mayorista)
            if aplicar_mayoro else
            float(var.precio if var.precio else prod.precio)
        )
        talla = next(
            (
                str(av.atributo_valor.valor)
                for av in var.attrs.all()
                if av.atributo_valor.atributo.nombre.lower() == "talla"
            ),
            "Única",
        )
        items.append({
            "nombre"          : prod.nombre,
            "precio"          : precio_unit,
            "cantidad"        : it.cantidad,
            "talla"           : talla,
            "imagen"          : prod.imagen.url if prod.imagen else None,
            "variante_id"     : var.id,
            "precio_mayorista": float(
                var.precio_mayorista if var.precio_mayorista > 0 else prod.precio_mayorista
            ),
            "precio_menudeo"  : float(var.precio if var.precio else prod.precio),
        })

    return {"items": items, "mayoreo": aplicar_mayoro}

@csrf_exempt
@require_http_methods(["PATCH"])
def actualizar_cantidad_guest(request, variante_id):
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'Sesión no encontrada'}, status=400)

    try:
        data = json.loads(request.body)
        cantidad = int(data.get("cantidad", 1))
    except:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    carrito = get_carrito_by_session(session_key)
    if not carrito:
        return JsonResponse({'error': 'Carrito no encontrado'}, status=404)

    item = carrito.items.filter(variante_id=variante_id).first()
    if not item:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    item.cantidad = max(cantidad, 1)
    item.save()
    return JsonResponse({'ok': True})


@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_item_guest(request, variante_id):
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'Sesión no encontrada'}, status=400)

    carrito = get_carrito_by_session(session_key)
    if not carrito:
        return JsonResponse({'error': 'Carrito no encontrado'}, status=404)

    item = carrito.items.filter(variante_id=variante_id).first()
    if not item:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    item.delete()
    return JsonResponse({'ok': True})


# views.py

@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST"])
def finalizar_compra(request, carrito_id):
    carrito = get_object_or_404(Carrito, id=carrito_id)
    cliente = carrito.cliente

    # ───── Obtener productos del carrito ───────────────────────────
    qs = (
        CarritoProducto.objects
        .filter(carrito=carrito)
        .select_related('variante__producto__categoria')
        .prefetch_related('variante__attrs__atributo_valor')
    )

    items         = []
    total_amount  = Decimal('0.00')
    total_piezas  = 0

    for cp in qs:
        var   = cp.variante
        prod  = var.producto
        precio_unit = var.precio if var.precio is not None else prod.precio
        subtotal    = precio_unit * cp.cantidad

        items.append({
            "producto"   : prod.nombre,
            "categoria"  : prod.categoria.nombre,          # ← NUEVO
            "variante_id": var.id,
            "cantidad"   : cp.cantidad,
            "precio_unitario": float(precio_unit),
            "subtotal"   : float(subtotal),
            "atributos"  : [str(av) for av in var.attrs.all()],
        })

        total_amount += subtotal
        total_piezas += cp.cantidad

    payload = {
        "cliente": {
            "username": cliente.username,
            "nombre"  : cliente.nombre,
            "correo"  : cliente.correo,
            "telefono": cliente.telefono,
        },
        "carrito_id"  : carrito.id,
        "total_piezas": total_piezas,
        "total_amount": float(round(total_amount, 2)),
        "items"       : items,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # ───── Evitar duplicación de órdenes ───────────────────────────
    orden = Orden.objects.filter(carrito=carrito).first()
    if not orden:
        try:
            orden = crear_orden_desde_payload(payload)
            print(f"[✅] Orden creada con ID: {orden.id}")
        except Exception as e:
            logger.error("Error creando la orden: %s", e)
            return JsonResponse({"error": "Fallo al crear orden."}, status=500)
    else:
        print(f"[⚠️] Orden ya existente con ID: {orden.id}")

    # ───── Generar token y link para cambiar estatus ───────────────
    token = signer.sign(str(orden.id))
    link  = request.build_absolute_uri(
        reverse('procesar_por_link', args=[token])
    )

    # ───── Enviar WhatsApp ─────────────────────────────────────────
    try:
        from twilio.rest import Client
        twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        raw_tel  = cliente.telefono or ""
        cleaned  = "".join(filter(str.isdigit, raw_tel))
        if cleaned.startswith("1"):
            cleaned = f"+{cleaned}"
        elif len(cleaned) == 10:
            cleaned = f"+521{cleaned}"
        elif len(cleaned) == 12 and cleaned.startswith("52"):
            cleaned = f"+{cleaned}"
        else:  # fallback al admin
            cleaned = settings.TWILIO_ADMIN_PHONE or "+5213322118360"

        to_whatsapp = settings.TWILIO_ADMIN_PHONE   # admin por ahora

        # ----------  Cuerpo “detallado” para fallback ----------
        body_lines = [
            f"Hola {cliente.nombre}, gracias por tu compra.",
            "",
            f"🧾 Pedido #{carrito.id}",
            f"🛍️ Artículos: {total_piezas}",
            f"💰 Total: ${payload['total_amount']}",
            "",
            "📦 Detalles:"
        ]
        for idx, it in enumerate(items, start=1):
            talla = next(
                (a.split(":",1)[1].strip() for a in it["atributos"] if a.lower().startswith("talla")),
                "Única"
            )
            body_lines.extend([
                f"{idx}️⃣ *{it['producto']}*",
                f"  🔸 Categoría: {it['categoria']}",     # ← NUEVO
                f"  🔸 Talla: {talla}",
                f"  🔸 Cantidad: {it['cantidad']}",
                f"  🔸 Precio: ${it['precio_unitario']}",
                f"  🔸 Subtotal: ${it['subtotal']}",
                ""
            ])
        body_lines.append(f"💰 *Total: ${payload['total_amount']}*")
        body_lines.append("------------------------------------------")
        body_lines.extend([
            f"🙍 Cliente: {cliente.nombre}",
            f"📞 Teléfono: {cliente.telefono or 'No disponible'}",
            f"📧 Correo: {cliente.correo or 'No disponible'}",
            f"🏠 Dirección: {cliente.direccion or 'No especificada'}",
            "",
            "👉 Pulsa aquí para marcar tu pedido como 'procesando':",
            link
        ])
        fallback_body = "\n".join(body_lines)

        # ----------  Mensaje interactivo con botón URL ----------
        interactive_body = {
            "type": "button",
            "body": {
                "text": f"Pedido #{carrito.id}\nTotal ${payload['total_amount']}\n¿Procesar ahora?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "url",
                        "url" : link,
                        "text": "Marcar procesando"
                    }
                ]
            }
        }

        try:
            # Enviar interactivo
            msg = twilio_client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=to_whatsapp,
                interactive=interactive_body
            )
        except Exception as e:
            # Si falla (p.ej. plantilla no aprobada), usa texto plano
            logger.warning("Interactive message falló, usando texto plano. Motivo: %s", e)
            msg = twilio_client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=to_whatsapp,
                body=fallback_body
            )

        print("✅ WhatsApp enviado. SID:", msg.sid)

        # Vaciar carrito
        carrito.items.all().delete()
        carrito.status = "vacio"
        carrito.save(update_fields=["status"])

        # Bandera de éxito y redirección
        request.session["pedido_exitoso"] = True
        return redirect(reverse("mostrar_confirmacion_compra", args=[carrito.id]))

    except Exception as e:
        import traceback                      # ← importar aquí
        logger.error("❌ Error Twilio: %s", e)
        traceback.print_exc()
        return JsonResponse({"error": "Fallo al enviar WhatsApp."}, status=500)



@require_http_methods(["GET"])
def mostrar_confirmacion_compra(request, carrito_id):
    # Obtener sin eliminar
    pedido_exitoso = request.session.get("pedido_exitoso", False)

    if not pedido_exitoso:
        return redirect(reverse("ver_carrito"))

    carrito = get_object_or_404(Carrito, id=carrito_id)

    qs = (
        carrito.items
        .select_related("variante__producto")
        .prefetch_related("variante__attrs__atributo_valor")
    )

    total = 0
    total_piezas = 0
    items = []

    for it in qs:
        prod = it.variante.producto
        var = it.variante
        atributos = [str(av) for av in var.attrs.all()]
        precio = float(var.precio if var.precio else prod.precio)
        subtotal = precio * it.cantidad
        imagen = prod.imagen.url if prod.imagen else "/static/img/no-image.jpg"

        items.append({
            "nombre": prod.nombre,
            "talla": next(
                (
                    av.atributo_valor.valor
                    for av in var.attrs.all()
                    if av.atributo_valor.atributo.nombre.lower() == "talla"
                ),
                "Única"
            ),
            "cantidad": it.cantidad,
            "precio_unitario": precio,
            "subtotal": subtotal,
            "imagen": imagen,
        })

        total += subtotal
        total_piezas += it.cantidad

    context = {
        "carrito": carrito,
        "cliente": carrito.cliente,
        "items": items,
        "total": round(total, 2),
        "total_piezas": total_piezas,
        "pedido_exitoso": True
    }

    # ← Limpiar la sesión *después* de mostrar
    response = render(request, "public/carrito/finalizar_compra.html", context)
    try:
        del request.session["pedido_exitoso"]
    except KeyError:
        pass
    return response


@require_http_methods(["GET"])
def mostrar_formulario_confirmacion(request, carrito_id):
    carrito = get_object_or_404(Carrito, id=carrito_id)

    qs = (
        carrito.items
        .select_related("variante__producto")
        .prefetch_related("variante__attrs__atributo_valor")
    )

    total = 0
    total_piezas = 0
    items = []

    for it in qs:
        prod = it.variante.producto
        var = it.variante
        atributos = [str(av) for av in var.attrs.all()]
        precio = float(var.precio if var.precio else prod.precio)
        subtotal = precio * it.cantidad
        imagen = prod.imagen.url if prod.imagen else "/static/img/no-image.jpg"

        items.append({
            "nombre": prod.nombre,
            "talla": next(
                (
                    av.atributo_valor.valor
                    for av in var.attrs.all()
                    if av.atributo_valor.atributo.nombre.lower() == "talla"
                ),
                "Única"
            ),
            "cantidad": it.cantidad,
            "precio_unitario": precio,
            "subtotal": subtotal,
            "imagen": imagen,
        })

        total += subtotal
        total_piezas += it.cantidad

    context = {
        "carrito": carrito,
        "cliente": carrito.cliente,
        "items": items,
        "total": round(total, 2),
        "total_piezas": total_piezas,
    }

    return render(request, "public/carrito/finalizar_compra.html", context)
