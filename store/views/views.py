# store/views/views.py
# ==============================================================
from functools import wraps
from random    import sample
import json 

from django.contrib.auth.hashers import check_password, make_password
from django.db                    import transaction
from django.db.models             import Prefetch
from django.http                  import (
    HttpResponseNotFound, JsonResponse
)
from django.shortcuts             import (
    get_object_or_404, redirect, render
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (
    require_GET, require_POST, require_http_methods
)

from ..models import (
    AtributoValor, Categoria, Cliente, ContactoCliente, Producto,
    Usuario, Variante
)


# ───────────────────────────────────────────────────────────────
# Decoradores de acceso
# ───────────────────────────────────────────────────────────────
def login_required_client(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("cliente_id"):
            return redirect("index")
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_user(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login_user")
        try:
            user = Usuario.objects.get(id=user_id)
            if user.role != "admin":
                return redirect("login_user")
        except Usuario.DoesNotExist:
            return redirect("login_user")
        return view_func(request, *args, **kwargs)
    return wrapper


# ───────────────────────────────────────────────────────────────
# Dashboard – auth admin
# ───────────────────────────────────────────────────────────────
@require_http_methods(["GET", "POST"])
def login_user(request):
    if request.method == "GET":
        return render(request, "dashboard/auth/login.html")

    username = request.POST.get("username")
    password = request.POST.get("password")
    if not username or not password:
        return render(request, "dashboard/login.html",
                      {"error": "Campos obligatorios"})

    try:
        user = Usuario.objects.get(username=username)
        if not check_password(password, user.password):
            raise ValueError("Contraseña incorrecta")
    except Exception:
        return render(request, "dashboard/login.html",
                      {"error": "Credenciales inválidas"})

    request.session["user_id"]       = user.id
    request.session["user_username"] = user.username
    return redirect("dashboard_productos")


def logout_user(request):
    request.session.flush()
    return redirect("login_user")


# ───────────────────────────────────────────────────────────────
# Home pública
# ───────────────────────────────────────────────────────────────
def index(request):
    qs_h = (
        Producto.objects
        .filter(genero__iexact="H", variantes__stock__gt=0)
        .distinct()
        .prefetch_related(Prefetch("variantes", Variante.objects.all()))
    )
    qs_m = (
        Producto.objects
        .filter(genero__iexact="M", variantes__stock__gt=0)
        .distinct()
        .prefetch_related(Prefetch("variantes", Variante.objects.all()))
    )

    cab_home  = sample(list(qs_h), min(4, qs_h.count()))
    dama_home = sample(list(qs_m), min(4, qs_m.count()))

    return render(request, "public/home/index.html", {
        "cab_home":  cab_home,
        "dama_home": dama_home,
    })


def registrarse(request):
    if request.session.get("cliente_id"):
        return redirect("index")
    return render(request, "public/registro/registro-usuario.html")


# ───────────────────────────────────────────────────────────────
# Catálogo por género
# ───────────────────────────────────────────────────────────────
def genero_view(request, genero):
    genero_map = {"dama": "M", "caballero": "H"}
    genero_cod = genero_map.get(genero.lower())
    if not genero_cod:
        return HttpResponseNotFound("Género no válido")

    qs = (
        Producto.objects
        .filter(genero__iexact=genero_cod, variantes__stock__gt=0)
        .select_related("categoria")
        .distinct()
    )
    categorias = sorted({p.categoria.nombre for p in qs})
    return render(request, "public/catalogo/productos_genero.html", {
        "seccion"   : genero,
        "titulo"    : "Mujer" if genero == "dama" else "Hombre",
        "categorias": categorias,
        "productos" : qs,
    })


# ───────────────────────────────────────────────────────────────
# CRUD Categorías (backend)
# ───────────────────────────────────────────────────────────────
@require_GET
def get_categorias(request):
    return JsonResponse(
        list(Categoria.objects.all().values("id", "nombre")),
        safe=False
    )


@csrf_exempt
@require_http_methods(["POST"])
def create_categoria(request):
    try:
        nombre = json.loads(request.body)["nombre"]
    except Exception:
        return JsonResponse({"error": "Falta campo 'nombre'"}, status=400)

    categoria = Categoria.objects.create(nombre=nombre)
    return JsonResponse({"id": categoria.id, "nombre": categoria.nombre},
                        status=201)

@csrf_exempt
@require_http_methods(["POST"])
def update_categoria(request, id):
    try:
        data = json.loads(request.body)
        categoria = get_object_or_404(Categoria, id=id)
        categoria.nombre = data.get("nombre", categoria.nombre)
        categoria.save()
        return JsonResponse({"mensaje": "Categoría actualizada"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_categoria(request, id):
    try:
        categoria = get_object_or_404(Categoria, id=id)
        categoria.delete()
        return JsonResponse({"mensaje": "Categoría eliminada"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@login_required_user
def dashboard_categorias(request):
    return render(request, "dashboard/categorias/lista.html")

# ───────────────────────────────────────────────────────────────
# Dashboard: productos
# ───────────────────────────────────────────────────────────────
@login_required_user
def lista_productos(request):
    return render(request, "dashboard/productos/lista.html")


@login_required_user
def alta(request):
    return render(request, "dashboard/productos/registro.html")


@login_required_user
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
@login_required_user
def dashboard_clientes(request):
    return render(request, "dashboard/clientes/lista.html",
                  {"clientes": Cliente.objects.all()})


@login_required_user
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


# ───────────────────────────────────────────────────────────────
# Auth cliente + fusión de carrito
# ───────────────────────────────────────────────────────────────
@require_POST
def login_client(request):
    """
    Inicia sesión de Cliente y fusiona carrito de invitado con el suyo.
    """
    try:
        data = json.loads(request.body or "{}")
        username, password = data.get("username"), data.get("password")
        if not username or not password:
            return JsonResponse({"error": "Faltan campos"}, status=400)

        try:
            cliente = Cliente.objects.get(username=username)
        except Cliente.DoesNotExist:
            return JsonResponse({"error": "Usuario no registrado"}, status=404)

        if not check_password(password, cliente.password):
            return JsonResponse({"error": "Contraseña incorrecta"}, status=401)

        # Sesión
        if not request.session.session_key:
            request.session.save()
        request.session["cliente_id"]       = cliente.id
        request.session["cliente_username"] = cliente.username

        # Fusionar carrito invitado ➜ usuario
        from .carrito import get_carrito_activo_cliente, get_carrito_by_session
        invitado = get_carrito_by_session(request.session.session_key)
        if invitado:
            destino = get_carrito_activo_cliente(cliente)
            with transaction.atomic():
                for linea in invitado.items.select_related("variante"):
                    var = linea.variante
                    dest, _ = destino.items.get_or_create(
                        variante=var,
                        defaults={"cantidad": 0}
                    )
                    dest.cantidad = min(dest.cantidad + linea.cantidad,
                                        var.stock)
                    dest.save(update_fields=["cantidad"])
            invitado.delete()

        return JsonResponse({"message": "Inicio de sesión exitoso"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_http_methods(["POST"])
def logout_client(request):
    request.session.flush()
    return redirect("index")


# ───────────────────────────────────────────────────────────────
# Perfil cliente (protegido)
# ───────────────────────────────────────────────────────────────
@login_required_client
@require_http_methods(["GET", "POST"])
def perfil_cliente(request):
    cliente = get_object_or_404(Cliente, id=request.session["cliente_id"])

    if request.method == "POST":
        cliente.nombre    = request.POST.get("nombre")
        cliente.telefono  = request.POST.get("telefono")
        cliente.direccion = request.POST.get("direccion")
        cliente.save()
        return redirect("perfil_cliente")

    return render(request, "public/cliente/perfil.html",
                  {"cliente": cliente})

