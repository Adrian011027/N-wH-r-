from random import sample
import json
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

import jwt
from django.conf import settings
from store.models import BlacklistedToken

from ..models import Categoria, Cliente, Producto, Usuario, Variante
from store.utils.jwt_helpers import generate_access_token, generate_refresh_token
from .decorators import jwt_role_required


# ───────────────────────────────────────────────
# Home pública
# ───────────────────────────────────────────────
def index(request):
    qs_h = Producto.objects.filter(genero__iexact="H", variantes__stock__gt=0) \
        .distinct().prefetch_related(Prefetch("variantes", Variante.objects.all()))
    qs_m = Producto.objects.filter(genero__iexact="M", variantes__stock__gt=0) \
        .distinct().prefetch_related(Prefetch("variantes", Variante.objects.all()))

    cab_home  = sample(list(qs_h), min(4, qs_h.count()))
    dama_home = sample(list(qs_m), min(4, qs_m.count()))

    return render(request, "public/home/index.html", {
        "cab_home": cab_home,
        "dama_home": dama_home,
    })


def registrarse(request):
    return render(request, "public/registro/registro-usuario.html")


# ───────────────────────────────────────────────
# Catálogo por género
# ───────────────────────────────────────────────
def genero_view(request, genero):
    genero_map = {"dama": "M", "caballero": "H"}
    genero_cod = genero_map.get(genero.lower())
    if not genero_cod:
        return HttpResponseNotFound("Género no válido")

    qs = Producto.objects.filter(genero__iexact=genero_cod, variantes__stock__gt=0) \
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
    data = json.loads(request.body or "{}")
    username = data.get("username")
    password = data.get("password")

    try:
        user = Usuario.objects.get(username=username)
        if not check_password(password, user.password):
            return JsonResponse({"error": "Contraseña incorrecta"}, status=401)
    except Usuario.DoesNotExist:
        return JsonResponse({"error": "Credenciales inválidas"}, status=401)

    access  = generate_access_token(user.id, user.role)
    refresh = generate_refresh_token(user.id)
    return JsonResponse({"access": access, "refresh": refresh}, status=200)


# ───────────────────────────────────────────────
# Login Cliente con JWT
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def login_client(request):
    data = json.loads(request.body or "{}")
    username = data.get("username")
    password = data.get("password")

    try:
        cliente = Cliente.objects.get(username=username)
        if not check_password(password, cliente.password):
            return JsonResponse({"error": "Contraseña incorrecta"}, status=401)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Usuario no registrado"}, status=404)

    access  = generate_access_token(cliente.id, "cliente")
    refresh = generate_refresh_token(cliente.id)
    return JsonResponse({"access": access, "refresh": refresh}, status=200)


# ───────────────────────────────────────────────
# CRUD Categorías (solo admin con JWT)
# ───────────────────────────────────────────────
@jwt_role_required
@require_GET
def get_categorias(request):
    return JsonResponse(
        list(Categoria.objects.all().values("id", "nombre")),
        safe=False
    )


@csrf_exempt
@jwt_role_required
@require_http_methods(["POST"])
def create_categoria(request):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        nombre = json.loads(request.body)["nombre"]
        categoria = Categoria.objects.create(nombre=nombre)
        return JsonResponse({"id": categoria.id, "nombre": categoria.nombre}, status=201)
    except Exception:
        return JsonResponse({"error": "Falta campo 'nombre'"}, status=400)


@csrf_exempt
@jwt_role_required
@require_http_methods(["POST"])
def update_categoria(request, id):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        data = json.loads(request.body)
        categoria = get_object_or_404(Categoria, id=id)
        categoria.nombre = data.get("nombre", categoria.nombre)
        categoria.save()
        return JsonResponse({"mensaje": "Categoría actualizada"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@jwt_role_required
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
