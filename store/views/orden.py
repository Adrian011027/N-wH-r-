
import json
from django.forms import model_to_dict
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from ..models import  Carrito, Orden, OrdenDetalle, Variante
from django.db import models, transaction

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
        # Supongo que Variante tiene una relación a atributos; ajústalo a tu modelo real
        try:
            atributos = [
                f"{attr.nombre}: {attr.valor}"
                for attr in variante.atributos.all()
            ]
        except Exception:
            atributos = []

        data["items"].append({
            "producto":        variante.producto.nombre,
            "variante_id":     variante.id,
            "cantidad":        det.cantidad,
            "precio_unitario": float(det.precio_unitario),
            "subtotal":        float(det.precio_unitario * det.cantidad),
            "atributos":       atributos,
        })

    # 4. Devolver JSON con indentación y caracteres unicode
    return JsonResponse(data, json_dumps_params={
        "ensure_ascii": False,
        "indent": 2
    })


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
        print(json.dumps(data, indent=2, default=str))
        
    return orden

