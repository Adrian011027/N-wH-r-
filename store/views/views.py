from random import sample
import json
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

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
    return JsonResponse({"access": access, "refresh": refresh, "username": username}, status=200)


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



#@jwt_role_required()
def dashboard_categorias(request):
    return render(request, "dashboard/categorias/lista.html")

# ───────────────────────────────────────────────────────────────
# Dashboard: productos
# ───────────────────────────────────────────────────────────────
#@jwt_role_required()
def lista_productos(request):
    return render(request, "dashboard/productos/lista.html")


#@jwt_role_required()
def alta(request):
    return render(request, "dashboard/productos/registro.html")


#@jwt_role_required()
def editar_producto(request, id):
    producto   = get_object_or_404(Producto, id=id)
    categorias = Categoria.objects.all()
    variantes  = (
        producto.variantes
        .prefetch_related("attrs__atributo_valor")
        .all()
    )

    variantes_data = []
    for v in variantes:
        talla = next(
            (
                av.atributo_valor.valor
                for av in v.attrs.all()
                if av.atributo_valor.atributo.nombre.lower() == "talla"
            ),
            "—",
        )
        variantes_data.append({
            "id"    : v.id,
            "talla" : talla,
            "precio": v.precio,
            "stock" : v.stock,
        })

    return render(request, "dashboard/productos/editar.html", {
        "producto"  : producto,
        "categorias": categorias,
        "variantes" : variantes_data,
    })


# ───────────────────────────────────────────────────────────────
# Dashboard: clientes
# ───────────────────────────────────────────────────────────────

def dashboard_clientes(request):
    return render(request, "dashboard/clientes/lista.html",
                  {"clientes": Cliente.objects.all()})


#@jwt_role_required()
def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == "GET":
        return render(request, "dashboard/clientes/editar.html",
                      {"cliente": cliente})

    # POST
    cliente.username  = request.POST.get("username")
    cliente.correo    = request.POST.get("correo")
    cliente.nombre    = request.POST.get("nombre")
    cliente.telefono  = request.POST.get("telefono")
    cliente.direccion = request.POST.get("direccion")
    cliente.save()
    return redirect("dashboard_clientes")



def login_user_page(request):
    return render(request, "dashboard/auth/login.html")