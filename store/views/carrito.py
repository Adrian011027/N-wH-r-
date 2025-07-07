# store/views/carrito.py
# ==============================================================
from venv import logger
from django.forms import model_to_dict
from django.shortcuts            import get_object_or_404, render
from django.db                   import models, transaction
from django.db.models            import Sum
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from store.views.decorators      import login_required_client
from store.views.orden import crear_orden_desde_payload
from ..models import (
    Cliente, Carrito, Producto, AtributoValor,
    Variante, CarritoProducto
)

import json
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from twilio.rest import Client

# ───────────────────────────────────────────────────────────────
# Helpers de carrito
# ───────────────────────────────────────────────────────────────
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

# ---- Configuración Twilio (mejor si lo pones en settings.py) ----
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN  = ""
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

# Inicializas el cliente una sola vez
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@csrf_exempt
@require_http_methods(["POST"])
def finalizar_compra(request, carrito_id):
    """
    El carrito_id viene desde la URL: /ordenar/123/
    """
    # 1) Obtener carrito y cliente
    carrito = get_object_or_404(Carrito, id=carrito_id)
    cliente = carrito.cliente

    # 2) Traer productos del carrito
    qs = (
        CarritoProducto.objects
        .filter(carrito=carrito)
        .select_related('variante__producto')
        .prefetch_related('variante__attrs__atributo_valor')
    )

    # 3) Construir lista de ítems y calcular totales
    items = []
    total_amount = Decimal('0.00')
    total_piezas = 0

    for cp in qs:
        var        = cp.variante
        prod       = var.producto
        precio_unit= var.precio if var.precio is not None else prod.precio
        subtotal   = precio_unit * cp.cantidad

        items.append({
            "producto":        prod.nombre,
            "variante_id":     var.id,
            "cantidad":        cp.cantidad,
            "precio_unitario": float(precio_unit),
            "subtotal":        float(subtotal),
            "atributos":       [str(av) for av in var.attrs.all()],
        })

        total_amount += subtotal
        total_piezas += cp.cantidad

    # 4) Armar el payload JSON
    payload = {
        "cliente": {
            "username": cliente.username,
            "nombre":   cliente.nombre,
            "correo":   cliente.correo,
            "telefono": cliente.telefono,
        },
        "carrito_id":   carrito.id,
        "total_piezas": total_piezas,
        "total_amount": float(round(total_amount, 2)),
        "items":        items,
    }

    # 5) Debug: imprimo en consola
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(payload["cliente"]["nombre"])
    print(payload["items"])


    try:
        orden = crear_orden_desde_payload(payload)
        # opcional: hacer algo con la orden, p.ej. imprimir el ID
        print(f"Orden creada con ID: {orden.id}")
    except Exception as e:
        # aquí controlas errores (fallos de validación, variantes no encontradas, etc)
        logger.error("Error creando la orden: %s", e)
        # devolver un error HTTP, lanzar una excepción, etc.
        raise
    # … arriba queda todo igual …

    # 6) Envío por WhatsApp
    try:
        # Validar teléfono (si no lo tienes hardcodeado)
        
        # Usar número fijo o dinámico:
        to_whatsapp = "whatsapp:+5213340511109"  # <- temporalmente fijo
        #to_whatsapp = "whatsapp:+5213322118360"
        # Construcción del cuerpo del mensaje con talla incluida
        body_lines = [
            f"Hola {cliente.nombre}, gracias por tu compra.",
            "",
            f"Resumen (#{carrito.id}): {total_piezas} artículos → ${payload['total_amount']}",
            "",
            "Detalles:"
        ]

        for it in items:
            talla = None
            for attr in it['atributos']:
                if attr.lower().startswith("talla"):
                    _, valor = attr.split(":", 1)
                    talla = valor.strip()
                    break
                
            talla_text = f", Talla: {talla}" if talla else ""
            line = (
                f"· Modelo: {it['producto']}"
                f"{talla_text}, Cantidad: x{it['cantidad']}: "
                f"${it['precio_unitario']} c/u → ${it['subtotal']}"
            )
            body_lines.append(line)

        # Unimos todo con saltos de línea
        body = "\n".join(body_lines)

        msg = twilio_client.messages.create(
            body=body,
            from_=TWILIO_WHATSAPP_FROM,
            to=to_whatsapp
        )
        print("SID Twilio:", msg.sid)

    except Exception as e:
        print("Error Twilio:", e)
        return JsonResponse(
            {"error": "Fallo al enviar WhatsApp."},
            status=500
        )

    # 7) Respondo al front
    #return JsonResponse({"status": "ok", "payload": payload})
    return render(request, "public/carrito/finalizar_compra.html")
