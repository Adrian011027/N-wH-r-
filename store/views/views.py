from random import sample
import json
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

import jwt
from django.conf import settings
from store.models import BlacklistedToken

from ..models import Categoria, Cliente, Producto, Usuario, Variante
from store.utils.jwt_helpers import generate_access_token, generate_refresh_token, decode_jwt
from .decorators import jwt_role_required, login_required_user


# ───────────────────────────────────────────────
# Home pública
# ───────────────────────────────────────────────
def index(request):
    # Productos Hombre (incluye Unisex)
    qs_h = Producto.objects.filter(genero__in=["H", "U"], variantes__stock__gt=0) \
        .distinct().prefetch_related(Prefetch("variantes", Variante.objects.all()))
    
    # Productos Mujer (incluye Unisex)
    qs_m = Producto.objects.filter(genero__in=["M", "U"], variantes__stock__gt=0) \
        .distinct().prefetch_related(Prefetch("variantes", Variante.objects.all()))

    cab_home  = sample(list(qs_h), min(4, qs_h.count()))
    dama_home = sample(list(qs_m), min(4, qs_m.count()))

    return render(request, "public/home/index.html", {
        "cab_home": cab_home,
        "dama_home": dama_home,
    })


def registrarse(request):
    from django.conf import settings
    return render(request, "public/registro/registro-usuario.html", {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })


# ───────────────────────────────────────────────
# Catálogo por género
# ───────────────────────────────────────────────
def genero_view(request, genero):
    genero_map = {"dama": "M", "caballero": "H"}
    genero_cod = genero_map.get(genero.lower())
    if not genero_cod:
        return HttpResponseNotFound("Género no válido")

    # Incluir productos Unisex en ambas secciones
    qs = Producto.objects.filter(genero__in=[genero_cod, "U"], variantes__stock__gt=0) \
        .select_related("categoria").distinct()
    categorias = sorted({p.categoria.nombre for p in qs})
    return render(request, "public/catalogo/productos_genero.html", {
        "seccion": genero,
        "titulo": "Mujer" if genero == "dama" else "Hombre",
        "categorias": categorias,
        "productos": qs,
    })


# ───────────────────────────────────────────────
# Login Admin con JWT
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    """
    Login de administrador con JWT + sesión Django.
    Permite login con usuario o correo (case-insensitive).
    Retorna tokens JWT y establece sesión para vistas HTML del dashboard.
    """
    data = json.loads(request.body or "{}")
    identifier = data.get("username", "").strip()  # Puede ser username o correo
    password = data.get("password")

    if not identifier or not password:
        return JsonResponse({"error": "Usuario/correo y contraseña requeridos"}, status=400)

    # Buscar por username o correo (case-insensitive)
    try:
        user = Usuario.objects.get(username__iexact=identifier)
    except Usuario.DoesNotExist:
        try:
            user = Usuario.objects.get(email__iexact=identifier)
        except Usuario.DoesNotExist:
            return JsonResponse({"error": "Credenciales inválidas"}, status=401)

    # Validar contraseña (case-sensitive)
    if not check_password(password, user.password):
        return JsonResponse({"error": "Contraseña incorrecta"}, status=401)

    # Verificar que sea admin
    if user.role != "admin":
        return JsonResponse({"error": "Acceso denegado. Solo administradores."}, status=403)

    # Generar tokens JWT
    access  = generate_access_token(user.id, user.role, user.username)
    refresh = generate_refresh_token(user.id)
    
    # Establecer sesión Django para vistas HTML
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    
    return JsonResponse({
        "access": access,
        "refresh": refresh,
        "username": user.username,
        "user_id": user.id
    }, status=200)


# ───────────────────────────────────────────────
# Login Cliente con JWT
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def login_client(request):
    """
    Login de cliente con JWT.
    Permite login con usuario o correo (case-insensitive).
    La contraseña sí es case-sensitive.
    """
    data = json.loads(request.body or "{}")
    identifier = data.get("username", "").strip()  # Puede ser username o correo
    password = data.get("password")

    if not identifier or not password:
        return JsonResponse({"error": "Usuario/correo y contraseña requeridos"}, status=400)

    # Buscar por username o correo (case-insensitive)
    try:
        cliente = Cliente.objects.get(username__iexact=identifier)
    except Cliente.DoesNotExist:
        try:
            cliente = Cliente.objects.get(correo__iexact=identifier)
        except Cliente.DoesNotExist:
            return JsonResponse({"error": "Usuario no registrado"}, status=404)

    # Validar contraseña (case-sensitive)
    if not check_password(password, cliente.password):
        return JsonResponse({"error": "Contraseña incorrecta"}, status=401)

    access  = generate_access_token(cliente.id, "cliente", cliente.username)
    refresh = generate_refresh_token(cliente.id)
    return JsonResponse({
        "access": access, 
        "refresh": refresh, 
        "username": cliente.username,
        "nombre": cliente.nombre or cliente.username,
        "correo": cliente.correo or ""
    }, status=200)


# ───────────────────────────────────────────────
# CRUD Categorías (solo admin con JWT)
# ───────────────────────────────────────────────
@jwt_role_required()
@require_GET
def get_categorias(request):
    categorias = Categoria.objects.all()
    data = [{
        "id": cat.id,
        "nombre": cat.nombre,
        "imagen": cat.imagen.url if cat.imagen else ''
    } for cat in categorias]
    return JsonResponse(data, safe=False)


@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST"])
def create_categoria(request):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        # Soporte para JSON y multipart/form-data
        if request.content_type.startswith("application/json"):
            nombre = json.loads(request.body)["nombre"]
            imagen = None
        else:
            nombre = request.POST.get("nombre")
            imagen = request.FILES.get("imagen")
        
        if not nombre:
            return JsonResponse({"error": "Falta campo 'nombre'"}, status=400)
        
        categoria = Categoria.objects.create(nombre=nombre, imagen=imagen)
        return JsonResponse({
            "id": categoria.id,
            "nombre": categoria.nombre,
            "imagen": categoria.imagen.url if categoria.imagen else ''
        }, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST"])
def update_categoria(request, id):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        categoria = get_object_or_404(Categoria, id=id)
        
        # Soporte para JSON y multipart/form-data
        if request.content_type.startswith("application/json"):
            data = json.loads(request.body)
            categoria.nombre = data.get("nombre", categoria.nombre)
        else:
            categoria.nombre = request.POST.get("nombre", categoria.nombre)
            if 'imagen' in request.FILES:
                categoria.imagen = request.FILES['imagen']
        
        categoria.save()
        return JsonResponse({
            "mensaje": "Categoría actualizada",
            "imagen": categoria.imagen.url if categoria.imagen else ''
        }, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@jwt_role_required()
@require_http_methods(["DELETE"])
def delete_categoria(request, id):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        categoria = get_object_or_404(Categoria, id=id)
        categoria.delete()
        return JsonResponse({"mensaje": "Categoría eliminada"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ───────────────────────────────────────────────
# Refresh Token
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request):
    try:
        data = json.loads(request.body or "{}")
        refresh = data.get("refresh")

        if not refresh:
            return JsonResponse({"error": "Refresh token requerido"}, status=400)

        payload = decode_jwt(refresh)
        if not payload or payload.get("type") != "refresh":
            return JsonResponse({"error": "Refresh token inválido o expirado"}, status=401)

        new_access = generate_access_token(payload["user_id"], payload.get("role", "cliente"))
        return JsonResponse({"access": new_access}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ───────────────────────────────────────────────
# Logout Cliente con invalidación de Refresh Token
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def logout_client(request):
    """
    Logout de clientes con invalidación de refresh token.
    - El cliente debe enviar su refresh token en el body.
    - El token se guarda en la blacklist.
    - El frontend además debe borrar access y refresh de su storage.
    """
    try:
        data = json.loads(request.body or "{}")
        refresh = data.get("refresh")

        if not refresh:
            return JsonResponse({"error": "Refresh token requerido"}, status=400)

        # Decodificar refresh
        payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return JsonResponse({"error": "No es un refresh token"}, status=400)

        # Guardar en blacklist
        BlacklistedToken.objects.create(token=refresh)

        return JsonResponse({"message": "Logout cliente exitoso"}, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({"error": "Refresh token expirado"}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({"error": "Refresh token inválido"}, status=401)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ───────────────────────────────────────────────
# Logout Usuario (admin) con invalidación
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    """
    Logout de usuarios admin con invalidación de refresh token.
    - Igual que logout_client pero para admins/usuarios.
    """
    try:
        data = json.loads(request.body or "{}")
        refresh = data.get("refresh")

        if not refresh:
            return JsonResponse({"error": "Refresh token requerido"}, status=400)

        # Decodificar refresh
        payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return JsonResponse({"error": "No es un refresh token"}, status=400)

        # Guardar en blacklist
        BlacklistedToken.objects.create(token=refresh)

        return JsonResponse({"message": "Logout usuario exitoso"}, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({"error": "Refresh token expirado"}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({"error": "Refresh token inválido"}, status=401)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ───────────────────────────────────────────────
# Dashboard Views
# ───────────────────────────────────────────────
def login_user_page(request):
    """Página de login para el dashboard admin"""
    return render(request, "dashboard/auth/login.html")


@login_required_user
def lista_productos(request):
    """Lista de productos en el dashboard"""
    productos = Producto.objects.select_related("categoria").prefetch_related("variantes").all()
    return render(request, "dashboard/productos/lista.html", {"productos": productos})


@login_required_user
def alta(request):
    """Formulario para crear producto"""
    categorias = Categoria.objects.all()
    return render(request, "dashboard/productos/registro.html", {"categorias": categorias})


@login_required_user
def editar_producto(request, id):
    """Formulario para editar producto"""
    producto = get_object_or_404(Producto.objects.prefetch_related("variantes"), id=id)
    categorias = Categoria.objects.all()
    return render(request, "dashboard/productos/editar.html", {
        "producto": producto,
        "categorias": categorias
    })


@login_required_user
def dashboard_clientes(request):
    """Lista de clientes en el dashboard"""
    clientes = Cliente.objects.all()
    return render(request, "dashboard/clientes/lista.html", {"clientes": clientes})


@login_required_user
def editar_cliente(request, id):
    """Formulario para editar cliente"""
    cliente = get_object_or_404(Cliente, id=id)
    return render(request, "dashboard/clientes/editar.html", {"cliente": cliente})


@login_required_user
def dashboard_categorias(request):
    """Panel de categorías en el dashboard"""
    categorias = Categoria.objects.all()
    return render(request, "dashboard/categorias/lista.html", {"categorias": categorias})
