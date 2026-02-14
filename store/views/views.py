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
from .decorators import jwt_role_required, login_required_user, admin_required, admin_required_hybrid


# ───────────────────────────────────────────────
# Home pública
# ───────────────────────────────────────────────
def index(request):
    # Productos Hombre (incluye Unisex)
    qs_h = Producto.objects.filter(genero__in=["Hombre", "Unisex"], variantes__stock__gt=0) \
        .distinct().prefetch_related(Prefetch("variantes", Variante.objects.all())) \
        .prefetch_related("variantes__imagenes")
    
    # Productos Mujer (incluye Unisex)
    qs_m = Producto.objects.filter(genero__in=["Mujer", "Unisex"], variantes__stock__gt=0) \
        .distinct().prefetch_related(Prefetch("variantes", Variante.objects.all())) \
        .prefetch_related("variantes__imagenes")

    cab_home  = sample(list(qs_h), min(4, qs_h.count()))
    dama_home = sample(list(qs_m), min(4, qs_m.count()))
    
    # Agregar primera imagen (galería) a cada producto desde variante principal
    for p in cab_home + dama_home:
        variante_principal = p.variante_principal
        if variante_principal:
            primera_img = variante_principal.imagenes.all().order_by('orden').first()
            p.imagen = primera_img.imagen if primera_img else None
        else:
            p.imagen = None

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
    """
    Vista de colección por género con filtros completos.
    URL: /coleccion/<genero>/?categoria=<id>&subcategoria=<id>&tallas=7,8&precio_min=500&...
    
    Soporta filtros de:
    - Categoría y Subcategoría
    - Tallas (múltiples)
    - Colores (múltiples)
    - Marcas (múltiples)
    - Rango de precio
    - En oferta
    - Ordenamiento
    - Paginación
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    genero_map = {"dama": "Mujer", "mujer": "Mujer", "caballero": "Hombre", "hombre": "Hombre"}
    genero_cod = genero_map.get(genero.lower())
    if not genero_cod:
        return HttpResponseNotFound("Género no válido")

    # Obtener filtros de query params
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    
    # Parsear tallas (pueden venir como "39,40" o como múltiples params "tallas=39&tallas=40")
    tallas_raw = request.GET.get('tallas', '')
    tallas = [t.strip() for t in tallas_raw.split(',') if t.strip()] if tallas_raw else []
    
    # Parsear colores
    colores_raw = request.GET.get('colores', '')
    colores = [c.strip() for c in colores_raw.split(',') if c.strip()] if colores_raw else []
    
    # Parsear marcas
    marcas_raw = request.GET.get('marcas', '')
    marcas = [m.strip() for m in marcas_raw.split(',') if m.strip()] if marcas_raw else []
    
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    en_oferta = request.GET.get('en_oferta') == '1'
    busqueda = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'nuevo')
    pagina = request.GET.get('pagina', 1)

    # Base query: productos del género (+ Unisex)
    qs = Producto.objects.filter(genero__in=[genero_cod, "Unisex"]) \
        .select_related("categoria").prefetch_related("subcategorias", "variantes__imagenes", "variantes")
    
    # Debug: verificar cuántos productos hay con este género
    print(f"[DEBUG FILTRO GÉNERO] Género solicitado: {genero} -> Código: {genero_cod}")
    print(f"[DEBUG] Total productos con género '{genero_cod}' o 'Unisex': {qs.count()}")
    
    # Filtrar por categoría
    if categoria_id:
        try:
            qs = qs.filter(categoria_id=int(categoria_id))
        except ValueError:
            pass
    
    # Filtrar por subcategoría
    if subcategoria_id:
        try:
            qs = qs.filter(subcategorias__id=int(subcategoria_id))
        except ValueError:
            pass
    
    # Filtrar por tallas (productos que tienen variantes con esas tallas)
    if tallas:
        qs = qs.filter(variantes__talla__in=tallas, variantes__stock__gt=0)
    
    # Filtrar por colores
    if colores:
        qs = qs.filter(variantes__color__in=colores, variantes__stock__gt=0)
    
    # Filtrar por marcas
    if marcas:
        qs = qs.filter(marca__in=marcas)
    
    # Filtrar por precio
    if precio_min:
        try:
            qs = qs.filter(precio__gte=float(precio_min))
        except (ValueError, TypeError):
            pass
    
    if precio_max:
        try:
            qs = qs.filter(precio__lte=float(precio_max))
        except (ValueError, TypeError):
            pass
    
    # Filtrar por oferta
    if en_oferta:
        qs = qs.filter(en_oferta=True)
    
    # Búsqueda por nombre/descripción/marca
    if busqueda:
        qs = qs.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(marca__icontains=busqueda)
        )
    
    # Solo productos con stock (por defecto)
    qs = qs.filter(variantes__stock__gt=0).distinct()
    print(f"[DEBUG] Productos después de filtrar por stock > 0: {qs.count()}")
    
    # Ordenamiento
    orden_map = {
        'precio_asc': 'precio',
        'precio_desc': '-precio',
        'nuevo': '-created_at',
        'nombre': 'nombre',
    }
    qs = qs.order_by(orden_map.get(orden, '-created_at'))
    
    # Paginación (24 productos por página)
    paginator = Paginator(qs, 24)
    try:
        productos_pag = paginator.get_page(pagina)
    except:
        productos_pag = paginator.get_page(1)
    
    # Agregar primera imagen a cada producto de la página actual
    for p in productos_pag:
        variante_principal = p.variante_principal
        if variante_principal:
            primera_img = variante_principal.imagenes.all().order_by('orden').first()
            p.imagen = primera_img.imagen if primera_img else None
        else:
            p.imagen = None
    
    # Obtener categorías únicas (solo de la página actual para eficiencia)
    categorias = sorted({p.categoria.nombre for p in productos_pag if p.categoria})
    
    # Determinar título según filtros
    titulo = "Mujer" if genero_cod == "M" else "Hombre"
    if subcategoria_id:
        try:
            from ..models import Subcategoria
            subcat = Subcategoria.objects.get(id=subcategoria_id)
            titulo = f"{titulo} - {subcat.nombre}"
        except:
            pass
    
    # Pasar parámetros actuales al template para mantener filtros
    filtros_activos = {
        'categoria': categoria_id,
        'subcategoria': subcategoria_id,
        'tallas': ','.join(tallas) if tallas else '',
        'colores': ','.join(colores) if colores else '',
        'marcas': ','.join(marcas) if marcas else '',
        'precio_min': precio_min or '',
        'precio_max': precio_max or '',
        'en_oferta': '1' if en_oferta else '',
        'q': busqueda,
        'orden': orden
    }
    
    # Si es petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        productos_data = []
        for p in productos_pag:
            # Obtener URL de imagen (ya está asignada en el for anterior)
            imagen_url = p.imagen.url if hasattr(p, 'imagen') and p.imagen else None
            
            productos_data.append({
                'id': p.id,
                'nombre': p.nombre,
                'precio': str(p.precio),
                'precio_mayorista': str(p.precio_mayorista) if p.precio_mayorista else None,
                'en_oferta': p.en_oferta,
                'imagen': imagen_url,
                'marca': p.marca or ''
            })
        
        return JsonResponse({
            'success': True,
            'productos': productos_data,
            'total': paginator.count,
            'paginacion': {
                'pagina_actual': productos_pag.number,
                'total_paginas': paginator.num_pages,
                'tiene_siguiente': productos_pag.has_next(),
                'tiene_anterior': productos_pag.has_previous()
            }
        })
    
    # Renderizado HTML normal
    return render(request, "public/catalogo/productos_genero.html", {
        "seccion": genero,
        "titulo": titulo,
        "genero_cod": genero_cod,
        "categorias": categorias,
        "productos": productos_pag,
        "filtros_activos": filtros_activos,
        "total_productos": paginator.count,
    })


# ───────────────────────────────────────────────
# Catálogo con filtros dinámicos
# ───────────────────────────────────────────────
def catalogo_view(request):
    """
    Vista de catálogo que acepta filtros por query params:
    - genero: Hombre, Mujer, Unisex
    - categoria: ID de categoría
    - subcategoria: ID de subcategoría
    """
    from ..models import Subcategoria
    
    genero = request.GET.get('genero', '').strip()
    categoria_id = request.GET.get('categoria')
    subcategoria_id = request.GET.get('subcategoria')
    
    # Mapeo de género (acepta versiones antiguas y nuevas)
    genero_map = {
        'hombre': 'Hombre',
        'mujer': 'Mujer',
        'unisex': 'Unisex',
        'h': 'Hombre',
        'm': 'Mujer',
        'u': 'Unisex',
    }
    genero_normalizado = genero_map.get(genero.lower(), None)
    
    # Base query
    qs = Producto.objects.select_related("categoria").prefetch_related("subcategorias", "variantes", "variantes__imagenes")
    
    # Determinar género desde subcategoría si no viene en params
    seccion = "caballero"  # Default
    genero_filtro = None
    
    # Si hay subcategoría, obtener el género de los productos
    if subcategoria_id:
        try:
            subcat = Subcategoria.objects.get(id=subcategoria_id)
            # Buscar el género predominante de los productos con esta subcategoría
            producto_ejemplo = Producto.objects.filter(subcategorias__id=subcategoria_id).first()
            if producto_ejemplo:
                if producto_ejemplo.genero in ['M']:
                    seccion = "dama"
                    genero_filtro = ['M', 'U']
                else:
                    seccion = "caballero"
                    genero_filtro = ['H', 'U']
        except Subcategoria.DoesNotExist:
            pass
    
    # Filtrar por género desde params
    genero_map = {
        'hombre': (['Hombre', 'Unisex'], 'caballero'),
        'mujer': (['Mujer', 'Unisex'], 'dama'),
    }
    if genero in genero_map:
        genero_filtro, seccion = genero_map[genero]
    
    if genero_filtro:
        qs = qs.filter(genero__in=genero_filtro)
    
    # Filtrar por categoría
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    
    # Filtrar por subcategoría
    if subcategoria_id:
        qs = qs.filter(subcategorias__id=subcategoria_id)
    
    # Solo productos con stock
    qs = qs.filter(variantes__stock__gt=0).distinct()
    
    # Obtener info para el título
    titulo = "Catálogo"
    
    if subcategoria_id:
        try:
            subcat = Subcategoria.objects.get(id=subcategoria_id)
            titulo = subcat.nombre
        except Subcategoria.DoesNotExist:
            pass
    elif categoria_id:
        try:
            cat = Categoria.objects.get(id=categoria_id)
            titulo = cat.nombre
        except Categoria.DoesNotExist:
            pass
    elif genero_normalizado:
        titulo = genero_normalizado if genero_normalizado in ['Hombre', 'Mujer', 'Unisex'] else 'Todas'
    
    # Obtener categorías únicas de los productos filtrados
    categorias = sorted({p.categoria.nombre for p in qs if p.categoria})
    
    # Agregar primera imagen (galería) a cada producto
    for p in qs:
        variante_principal = p.variante_principal
        if variante_principal:
            primera_img = variante_principal.imagenes.all().order_by('orden').first()
            p.imagen = primera_img.imagen if primera_img else None
        else:
            p.imagen = None
    
    return render(request, "public/catalogo/productos_genero.html", {
        "seccion": seccion,
        "titulo": titulo,
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
    Incluye rate limiting para protección contra fuerza bruta.
    """
    from ..utils.security import (
        login_limiter, 
        get_client_ip, 
        record_failed_login, 
        record_successful_login,
        is_login_allowed
    )
    
    data = json.loads(request.body or "{}")
    identifier = data.get("username", "").strip()  # Puede ser username o correo
    password = data.get("password")

    if not identifier or not password:
        return JsonResponse({"error": "Usuario/correo y contraseña requeridos"}, status=400)
    
    # Rate limiting check
    ip = get_client_ip(request)
    allowed, remaining_time = is_login_allowed(identifier, ip)
    
    if not allowed:
        minutes = remaining_time // 60 if remaining_time else 15
        return JsonResponse({
            "error": f"Demasiados intentos fallidos. Espera {minutes} minutos.",
            "blocked": True,
            "retry_after": remaining_time
        }, status=429)

    # Buscar por username (case-insensitive)
    # Nota: Usuario solo tiene el campo 'username', no 'email'
    try:
        user = Usuario.objects.get(username__iexact=identifier)
    except Usuario.DoesNotExist:
        record_failed_login(identifier, ip)
        return JsonResponse({"error": "Credenciales inválidas"}, status=401)

    # Validar contraseña (case-sensitive)
    if not check_password(password, user.password):
        record_failed_login(identifier, ip)
        return JsonResponse({"error": "Contraseña incorrecta"}, status=401)

    # Verificar que sea admin
    if user.role != "admin":
        return JsonResponse({"error": "Acceso denegado. Solo administradores."}, status=403)

    # Login exitoso
    record_successful_login(identifier, ip)

    # Generar tokens JWT
    access  = generate_access_token(user.id, user.role, user.username)
    refresh = generate_refresh_token(user.id)
    
    # Establecer sesión Django para vistas HTML
    request.session.set_expiry(60 * 60 * 4)  # 4 horas timeout
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    request.session.save()  # ← CRÍTICO: Guardar en RDS
    
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
    Incluye rate limiting y verificación de email.
    """
    from ..utils.security import (
        login_limiter, 
        get_client_ip, 
        record_failed_login, 
        record_successful_login,
        is_login_allowed
    )
    
    data = json.loads(request.body or "{}")
    identifier = data.get("username", "").strip()  # Puede ser username o correo
    password = data.get("password")

    if not identifier or not password:
        return JsonResponse({"error": "Usuario/correo y contraseña requeridos"}, status=400)
    
    # Rate limiting check
    ip = get_client_ip(request)
    allowed, remaining_time = is_login_allowed(identifier, ip)
    
    if not allowed:
        minutes = remaining_time // 60 if remaining_time else 15
        return JsonResponse({
            "error": f"Demasiados intentos fallidos. Espera {minutes} minutos.",
            "blocked": True,
            "retry_after": remaining_time
        }, status=429)

    # Buscar por username o correo (case-insensitive)
    try:
        cliente = Cliente.objects.get(username__iexact=identifier)
    except Cliente.DoesNotExist:
        try:
            cliente = Cliente.objects.get(correo__iexact=identifier)
        except Cliente.DoesNotExist:
            record_failed_login(identifier, ip)
            return JsonResponse({"error": "Usuario no registrado"}, status=404)

    # Validar contraseña (case-sensitive)
    if not check_password(password, cliente.password):
        record_failed_login(identifier, ip)
        return JsonResponse({"error": "Contraseña incorrecta"}, status=401)
    
    # Verificar si el correo está verificado
    if not cliente.email_verified:
        # Permitir login pero indicar que necesita verificar
        access  = generate_access_token(cliente.id, "cliente", cliente.username)
        refresh = generate_refresh_token(cliente.id)
        
        # Crear sesión Django para vistas web
        request.session['cliente_id'] = cliente.id
        request.session['cliente_username'] = cliente.username
        
        record_successful_login(identifier, ip)
        
        return JsonResponse({
            "access": access, 
            "refresh": refresh, 
            "username": cliente.username,
            "nombre": cliente.nombre or cliente.username,
            "correo": cliente.correo or "",
            "email_verified": False,
            "warning": "Tu correo aún no está verificado. Revisa tu bandeja de entrada."
        }, status=200)

    # Login exitoso
    record_successful_login(identifier, ip)
    
    # Crear sesión Django para vistas web
    request.session['cliente_id'] = cliente.id
    request.session['cliente_username'] = cliente.username
    
    access  = generate_access_token(cliente.id, "cliente", cliente.username)
    refresh = generate_refresh_token(cliente.id)
    return JsonResponse({
        "access": access, 
        "refresh": refresh, 
        "username": cliente.username,
        "nombre": cliente.nombre or cliente.username,
        "correo": cliente.correo or "",
        "email_verified": True
    }, status=200)


# ───────────────────────────────────────────────
# API Pública: Categorías por género (sin autenticación)
# ───────────────────────────────────────────────
@require_GET
def categorias_por_genero(request):
    """
    Devuelve las categorías que tienen productos del género especificado.
    Endpoint público para el navbar dinámico.
    
    GET /api/categorias-por-genero/?genero=hombre|mujer|unisex
    """
    genero_param = request.GET.get('genero', '').lower()
    
    # Mapear parámetro a valores de BD
    genero_map = {
        'hombre': ['Hombre', 'Unisex'],  # Hombre + Unisex
        'mujer': ['Mujer', 'Unisex'],    # Mujer + Unisex
        'unisex': ['Unisex'],             # Solo unisex
        'ambos': [],                       # Todos los géneros
        'h': ['Hombre', 'Unisex'],
        'm': ['Mujer', 'Unisex'],
        'u': ['Unisex'],
    }
    
    generos = genero_map.get(genero_param, [])
    
    if not generos:
        # Sin filtro, devolver todas las categorías
        categorias = Categoria.objects.all()
    else:
        # Categorías que tienen productos del género especificado
        categorias = Categoria.objects.filter(
            producto__genero__in=generos
        ).distinct()
    
    data = {
        "categorias": [{
            "id": cat.id,
            "nombre": cat.nombre,
            "imagen": cat.imagen.url if cat.imagen else ''
        } for cat in categorias]
    }
    
    return JsonResponse(data)


@require_GET
def producto_aleatorio_subcategoria(request):
    """
    Devuelve un producto aleatorio de una subcategoría específica.
    Usado para mostrar imágenes en el menú de navegación.
    
    GET /api/producto-aleatorio-subcategoria/?subcategoria_id=X
    """
    subcategoria_id = request.GET.get('subcategoria_id')
    
    if not subcategoria_id:
        return JsonResponse({"error": "subcategoria_id requerido"}, status=400)
    
    try:
        from random import randint
        from django.db.models import Count
        
        # Obtener productos con stock de esta subcategoría específica
        productos = Producto.objects.filter(
            subcategorias__id=subcategoria_id,
            variantes__stock__gt=0
        ).distinct().prefetch_related('variantes__imagenes')
        
        if not productos.exists():
            return JsonResponse({"producto": None})
        
        # Contar productos para selección aleatoria más eficiente
        count = productos.count()
        
        # Seleccionar uno verdaderamente aleatorio
        if count > 1:
            random_index = randint(0, count - 1)
            producto = productos[random_index]
        else:
            producto = productos.first()
        
        # Obtener la primera imagen de la galería de la variante principal
        imagen_url = None
        variante_principal = producto.variante_principal
        if variante_principal and variante_principal.imagenes.exists():
            imagen_url = variante_principal.imagenes.first().imagen.url
        
        data = {
            "producto": {
                "id": producto.id,
                "nombre": producto.nombre,
                "imagen": imagen_url,
                "precio": float(producto.precio) if producto.precio else None
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        import traceback
        print(f"Error en producto_aleatorio_subcategoria: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


# ───────────────────────────────────────────────
# CRUD Categorías (solo admin)
# ───────────────────────────────────────────────
@admin_required_hybrid()
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
@admin_required()
@require_http_methods(["POST"])
def create_categoria(request):
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
@admin_required()
@require_http_methods(["POST"])
def update_categoria(request, id):
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
@admin_required()
@require_http_methods(["DELETE"])
def delete_categoria(request, id):
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
        
        # SEGURIDAD: Verificar si el token está en la blacklist
        if BlacklistedToken.objects.filter(token=refresh).exists():
            return JsonResponse({
                "error": "Token inválido",
                "detail": "Este token ha sido revocado. Por favor, inicia sesión nuevamente."
            }, status=401)

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
        
        # Limpiar sesión Django también
        request.session.flush()

        return JsonResponse({"message": "Logout cliente exitoso"}, status=200)

    except jwt.ExpiredSignatureError:
        # Limpiar sesión aunque el token esté expirado
        request.session.flush()
        return JsonResponse({"error": "Refresh token expirado"}, status=401)
    except jwt.InvalidTokenError:
        request.session.flush()
        return JsonResponse({"error": "Refresh token inválido"}, status=401)
    except Exception as e:
        request.session.flush()
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
    from store.models import Variante
    
    producto = get_object_or_404(Producto.objects.prefetch_related("variantes", "variantes__imagenes"), id=id)
    
    # Validación: Si el producto no tiene variantes, crear una variante por defecto
    if not producto.variantes.exists():
        Variante.objects.create(
            producto=producto,
            talla='UNICA',
            color='N/A',
            precio=producto.precio,
            precio_mayorista=producto.precio_mayorista,
            stock=0,
            es_variante_principal=True,
        )
        # Recargar las variantes
        producto = Producto.objects.prefetch_related("variantes", "variantes__imagenes").get(id=id)
    
    categorias = Categoria.objects.all()
    
    return render(request, "dashboard/productos/editar.html", {
        "producto": producto,
        "categorias": categorias,
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


@login_required_user
def dashboard_subcategorias(request):
    """Panel de subcategorías en el dashboard"""
    from ..models import Subcategoria
    subcategorias = Subcategoria.objects.all().select_related('categoria')
    return render(request, "dashboard/categorias/subcategorias.html", {"subcategorias": subcategorias})
