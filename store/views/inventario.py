# store/views/inventario.py
"""
Módulo de Inventario - Vistas para gestión de inventario.
Accesible por usuarios con role 'inventario' o 'admin' del modelo Usuario.
"""

import json
from functools import wraps

from django.contrib.auth.hashers import check_password
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET

from ..models import (
    Categoria, Producto, Subcategoria, Usuario, Variante, VarianteImagen
)
from store.utils.jwt_helpers import generate_access_token, generate_refresh_token

import logging
logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# Decorador de sesión para inventario
# ───────────────────────────────────────────────
INVENTARIO_ALLOWED_ROLES = ("inventario", "admin")


def login_required_inventario(view_func):
    """
    Decorador de sesión que permite acceso a usuarios con role 'inventario' o 'admin'.
    Redirige a la página de login de inventario si no cumple.
    Usa claves de sesión específicas del inventario (independientes del dashboard).
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_id = request.session.get("inventario_user_id")
        if not user_id:
            return redirect("inventario_login")
        try:
            user = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            return redirect("inventario_login")
        if user.role not in INVENTARIO_ALLOWED_ROLES:
            return redirect("inventario_login")
        request.inventario_user = user
        return view_func(request, *args, **kwargs)
    return _wrapped


# ───────────────────────────────────────────────
# Auth: Login para inventario
# ───────────────────────────────────────────────
def inventario_login_page(request):
    """Renderiza la página de login del módulo de inventario."""
    return render(request, "inventario/auth/login.html")


@csrf_exempt
@require_http_methods(["POST"])
def inventario_login(request):
    """
    Endpoint de login para el módulo de inventario.
    Acepta usuarios con role 'inventario' o 'admin' del modelo Usuario.
    """
    from ..utils.security import (
        get_client_ip, record_failed_login,
        record_successful_login, is_login_allowed
    )

    data = json.loads(request.body or "{}")
    identifier = data.get("username", "").strip()
    password = data.get("password")

    if not identifier or not password:
        return JsonResponse({"error": "Usuario y contraseña requeridos"}, status=400)

    ip = get_client_ip(request)
    allowed, remaining_time = is_login_allowed(identifier, ip)

    if not allowed:
        minutes = remaining_time // 60 if remaining_time else 15
        return JsonResponse({
            "error": f"Demasiados intentos fallidos. Espera {minutes} minutos.",
            "blocked": True,
            "retry_after": remaining_time
        }, status=429)

    try:
        user = Usuario.objects.get(username__iexact=identifier)
    except Usuario.DoesNotExist:
        record_failed_login(identifier, ip)
        return JsonResponse({"error": "Credenciales inválidas"}, status=401)

    if not check_password(password, user.password):
        record_failed_login(identifier, ip)
        return JsonResponse({"error": "Contraseña incorrecta"}, status=401)

    if user.role not in INVENTARIO_ALLOWED_ROLES:
        return JsonResponse({"error": "Acceso denegado. No tienes permisos para inventario."}, status=403)

    record_successful_login(identifier, ip)

    access = generate_access_token(user.id, user.role, user.username)
    refresh = generate_refresh_token(user.id)

    # Establecer sesión Django para INVENTARIO (independiente de dashboard)
    request.session.set_expiry(60 * 60 * 4)  # 4 horas
    request.session["inventario_user_id"] = user.id
    request.session["inventario_username"] = user.username
    request.session["inventario_role"] = user.role
    request.session.save()

    return JsonResponse({
        "access": access,
        "refresh": refresh,
        "username": user.username,
        "user_id": user.id,
        "role": user.role
    }, status=200)


# ───────────────────────────────────────────────
# Vista principal: Panel de Inventario
# ───────────────────────────────────────────────
@login_required_inventario
def inventario_panel(request):
    """
    Vista principal del inventario con tabla detallada de productos,
    variantes, colores, tallas, stock e imagen principal.
    """
    productos = (
        Producto.objects
        .select_related("categoria")
        .prefetch_related(
            Prefetch(
                "variantes",
                queryset=Variante.objects.prefetch_related("imagenes").order_by("-es_variante_principal", "color"),
            ),
            "subcategorias",
        )
        .order_by("-created_at")
    )

    # Construir datos serializados para la tabla
    inventario_data = []
    for producto in productos:
        variante_principal = producto.variante_principal
        imagen_url = None
        if variante_principal:
            primera_img = variante_principal.imagenes.all().order_by("orden").first()
            if primera_img and primera_img.imagen:
                imagen_url = primera_img.imagen.url

        for variante in producto.variantes.all():
            tallas_stock = variante.tallas_stock or {}
            stock_total = sum(tallas_stock.values()) if tallas_stock else 0

            # Imagen propia de la variante (si tiene)
            var_img = variante.imagenes.all().order_by("orden").first()
            var_imagen_url = var_img.imagen.url if var_img and var_img.imagen else imagen_url

            inventario_data.append({
                "producto_id": producto.id,
                "producto_nombre": producto.nombre,
                "categoria": producto.categoria.nombre if producto.categoria else "—",
                "marca": producto.marca or "—",
                "genero": producto.genero or "—",
                "variante_id": variante.id,
                "sku": variante.sku or "—",
                "color": variante.color or "N/A",
                "es_principal": variante.es_variante_principal,
                "tallas_stock": tallas_stock,
                "stock_total": stock_total,
                "imagen_url": var_imagen_url,
            })

    categorias = Categoria.objects.all()
    subcategorias = Subcategoria.objects.select_related("categoria").filter(activa=True)

    return render(request, "inventario/panel.html", {
        "inventario_data": inventario_data,
        "total_productos": productos.count(),
        "total_variantes": len(inventario_data),
        "categorias": categorias,
        "subcategorias": subcategorias,
    })


# ───────────────────────────────────────────────
# Vista: Crear producto (página)
# ───────────────────────────────────────────────
@login_required_inventario
def inventario_crear_producto(request):
    """Página para crear un nuevo producto desde el módulo de inventario."""
    categorias = Categoria.objects.all()
    subcategorias = Subcategoria.objects.select_related("categoria").filter(activa=True)
    return render(request, "inventario/crear_producto.html", {
        "categorias": categorias,
        "subcategorias": subcategorias,
    })


# ───────────────────────────────────────────────
# Vista: Gestión de categorías y subcategorías
# ───────────────────────────────────────────────
@login_required_inventario
def inventario_categorias(request):
    """Página para gestionar categorías y subcategorías."""
    categorias = Categoria.objects.prefetch_related("subcategorias").all()
    return render(request, "inventario/categorias.html", {
        "categorias": categorias,
    })


# ───────────────────────────────────────────────
# API: Actualizar stock de talla en variante
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def inventario_api_update_stock(request, variante_id):
    """Actualiza el stock de una talla específica de una variante."""
    # Verificar sesión del inventario
    user_id = request.session.get("inventario_user_id")
    if not user_id:
        return JsonResponse({"error": "No autenticado"}, status=401)
    try:
        user = Usuario.objects.get(id=user_id)
        if user.role not in INVENTARIO_ALLOWED_ROLES:
            return JsonResponse({"error": "Sin permisos"}, status=403)
    except Usuario.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)

    try:
        variante = Variante.objects.get(id=variante_id)
    except Variante.DoesNotExist:
        return JsonResponse({"error": "Variante no encontrada"}, status=404)

    data = json.loads(request.body or "{}")
    tallas_stock = data.get("tallas_stock")

    if tallas_stock is None:
        return JsonResponse({"error": "tallas_stock es requerido"}, status=400)

    # Validar que es un dict de talla->stock (enteros >= 0)
    if not isinstance(tallas_stock, dict):
        return JsonResponse({"error": "tallas_stock debe ser un objeto {talla: cantidad}"}, status=400)

    try:
        validated = {}
        for talla, stock in tallas_stock.items():
            stock_int = int(stock)
            if stock_int < 0:
                return JsonResponse({"error": f"Stock negativo no permitido para talla {talla}"}, status=400)
            validated[str(talla)] = stock_int
    except (ValueError, TypeError):
        return JsonResponse({"error": "Los valores de stock deben ser números enteros"}, status=400)

    variante.tallas_stock = validated
    variante.save()

    return JsonResponse({
        "success": True,
        "variante_id": variante.id,
        "tallas_stock": variante.tallas_stock,
        "stock_total": variante.stock_total_variante,
    })


# ───────────────────────────────────────────────
# API: Eliminar variante
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["DELETE"])
def inventario_api_delete_variante(request, variante_id):
    """Elimina una variante (solo si el producto tiene más de 1 variante)."""
    user_id = request.session.get("inventario_user_id")
    if not user_id:
        return JsonResponse({"error": "No autenticado"}, status=401)
    try:
        user = Usuario.objects.get(id=user_id)
        if user.role not in INVENTARIO_ALLOWED_ROLES:
            return JsonResponse({"error": "Sin permisos"}, status=403)
    except Usuario.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)

    try:
        variante = Variante.objects.select_related("producto").get(id=variante_id)
    except Variante.DoesNotExist:
        return JsonResponse({"error": "Variante no encontrada"}, status=404)

    # No permitir eliminar la última variante de un producto
    total_variantes = variante.producto.variantes.count()
    if total_variantes <= 1:
        return JsonResponse({
            "error": "No se puede eliminar la única variante del producto. Elimina el producto completo."
        }, status=400)

    producto_nombre = variante.producto.nombre
    color = variante.color
    variante.delete()

    return JsonResponse({
        "success": True,
        "message": f"Variante '{color}' del producto '{producto_nombre}' eliminada.",
    })


# ───────────────────────────────────────────────
# API: Obtener datos de inventario (JSON)
# ───────────────────────────────────────────────
@require_GET
def inventario_api_data(request):
    """API JSON del inventario completo, para búsquedas/filtros AJAX."""
    user_id = request.session.get("inventario_user_id")
    if not user_id:
        return JsonResponse({"error": "No autenticado"}, status=401)
    try:
        user = Usuario.objects.get(id=user_id)
        if user.role not in INVENTARIO_ALLOWED_ROLES:
            return JsonResponse({"error": "Sin permisos"}, status=403)
    except Usuario.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)

    # Filtros opcionales
    search = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria")
    stock_filter = request.GET.get("stock")  # "sin_stock", "bajo", "normal"

    productos = (
        Producto.objects
        .select_related("categoria")
        .prefetch_related(
            Prefetch(
                "variantes",
                queryset=Variante.objects.prefetch_related("imagenes").order_by("-es_variante_principal", "color"),
            ),
        )
        .order_by("-created_at")
    )

    if search:
        from django.db.models import Q
        productos = productos.filter(
            Q(nombre__icontains=search) |
            Q(marca__icontains=search) |
            Q(variantes__sku__icontains=search) |
            Q(variantes__color__icontains=search)
        ).distinct()

    if categoria_id:
        try:
            productos = productos.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            pass

    result = []
    for producto in productos:
        variante_principal = producto.variante_principal
        imagen_url = None
        if variante_principal:
            primera_img = variante_principal.imagenes.all().order_by("orden").first()
            if primera_img and primera_img.imagen:
                imagen_url = primera_img.imagen.url

        for variante in producto.variantes.all():
            tallas_stock = variante.tallas_stock or {}
            stock_total = sum(tallas_stock.values()) if tallas_stock else 0

            # Filtro por stock
            if stock_filter == "sin_stock" and stock_total > 0:
                continue
            if stock_filter == "bajo" and stock_total > 5:
                continue

            var_img = variante.imagenes.all().order_by("orden").first()
            var_imagen_url = var_img.imagen.url if var_img and var_img.imagen else imagen_url

            result.append({
                "producto_id": producto.id,
                "producto_nombre": producto.nombre,
                "categoria": producto.categoria.nombre if producto.categoria else "—",
                "marca": producto.marca or "—",
                "genero": producto.genero or "—",
                "variante_id": variante.id,
                "sku": variante.sku or "—",
                "color": variante.color or "N/A",
                "es_principal": variante.es_variante_principal,
                "tallas_stock": tallas_stock,
                "stock_total": stock_total,
                "imagen_url": var_imagen_url,
            })

    return JsonResponse({
        "success": True,
        "total": len(result),
        "data": result,
    })


@login_required_inventario
@require_GET
def inventario_api_producto_detalle(request, producto_id):
    """
    Devuelve los detalles completos de un producto con todas sus variantes e imágenes.
    Para el modal de edición completa.
    """
    try:
        producto = Producto.objects.prefetch_related(
            'variantes__imagenes',
            'subcategorias'
        ).select_related('categoria').get(id=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)

    # Serializar variantes con sus imágenes
    variantes_data = []
    for variante in producto.variantes.all().order_by('id'):
        imagenes_variante = [
            {
                "id": img.id,
                "url": img.imagen.url,
                "orden": img.orden
            }
            for img in variante.imagenes.all().order_by('orden')
            if img.imagen
        ]
        
        variantes_data.append({
            "id": variante.id,
            "color": variante.color or "N/A",
            "sku": variante.sku or "",
            "tallas_stock": variante.tallas_stock or {},
            "precio": float(variante.precio or producto.precio),
            "precio_mayorista": float(variante.precio_mayorista or producto.precio_mayorista),
            "es_variante_principal": variante.es_variante_principal,
            "stock_total": variante.stock_total_variante,
            "imagenes": imagenes_variante,
        })

    data = {
        "id": producto.id,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion or "",
        "marca": producto.marca or "",
        "categoria_id": producto.categoria.id if producto.categoria else None,
        "categoria_nombre": producto.categoria.nombre if producto.categoria else "",
        "genero": producto.genero or "Unisex",
        "precio": float(producto.precio),
        "precio_mayorista": float(producto.precio_mayorista),
        "subcategorias": [sc.id for sc in producto.subcategorias.all()],
        "variantes": variantes_data,
    }

    return JsonResponse({"success": True, "producto": data})
