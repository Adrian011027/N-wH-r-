from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Producto, Categoria, Variante
from .decorators import login_required_user, login_required_client, jwt_role_required, admin_required
from django.db.models import Prefetch
from decimal import Decimal
from .decorators import jwt_role_required
import json
from django.views.decorators.csrf import csrf_exempt
from ..utils.serializers import serializar_producto_completo


def detalle_producto(request, id):
    producto = get_object_or_404(
        Producto.objects.prefetch_related("variantes"),
        id=id
    )

    # ─── 1. Tallas y colores disponibles ───────────────────────────
    tallas = set()
    colores = set()

    variantes_serializadas = []    # para el JS
    for v in producto.variantes.all():
        if v.talla:
            tallas.add(v.talla)
        if v.color:
            colores.add(v.color)

        variantes_serializadas.append({
            "id"    : v.id,
            "talla" : v.talla,
            "color" : v.color,
            "precio": float(v.precio or producto.precio),
            "stock" : v.stock,
        })

    # lee el origen para el <a volver>
    origen_raw = request.GET.get("from", "")
    origen = origen_raw.lower() if origen_raw.lower() in ["dama", "caballero"] else "caballero"

    return render(
        request,
        "public/producto/detalles.html",
        {
            "producto"       : producto,
            "origen"         : origen,
            "tallas"         : sorted(tallas, key=lambda x: (len(x), x)),
            "colores"        : sorted(colores),
            "variantes_json" : json.dumps(variantes_serializadas),
        },
    )



#@jwt_role_required()  # Público - Ver detalles de producto
@require_GET
def get_all_products(request):

    productos = Producto.objects.prefetch_related('variantes', 'imagenes')
    data = []
    for p in productos:
        variantes = []
        for v in p.variantes.all():
            variantes.append({
                'id': v.id,
                'sku': v.sku,
                'talla': v.talla,
                'color': v.color,
                'otros': v.otros,
                'precio': float(v.precio or p.precio),
                'precio_mayorista': float(v.precio_mayorista or p.precio_mayorista),
                'stock': v.stock,
                'imagen': v.imagen.url if v.imagen else '',
            })
        
        # Galería de imágenes del producto
        galeria = [img.imagen.url for img in p.imagenes.all() if img.imagen]

        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'categoria': p.categoria.nombre,
            'categoria_id': p.categoria.id,
            'genero': p.genero,
            'en_oferta': p.en_oferta,
            'imagen': p.imagen.url if p.imagen else '',
            'imagenes': galeria,
            'created_at': p.created_at.isoformat(),
            'stock_total': p.stock_total,
            'variantes': variantes,
        })

    return JsonResponse(data, safe=False)

@csrf_exempt
@admin_required()
@require_http_methods(["POST"])
def create_product(request):

    # Detecta si el request viene en JSON o multipart/form-data
    if request.content_type.startswith("application/json"):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        nombre      = data.get("nombre")
        descripcion = data.get("descripcion")
        precio      = data.get("precio")
        precio_mayorista = data.get("precio_mayorista", precio)
        categoria_id= data.get("categoria_id")
        genero      = data.get("genero")
        en_oferta   = data.get("en_oferta", False)
        imagen      = None  # No hay archivos en JSON

        tallas = data.get("tallas", [])
        stocks = data.get("stocks", [])

    else:  # multipart/form-data
        nombre      = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio      = request.POST.get("precio")
        precio_mayorista = request.POST.get("precio_mayorista", precio)
        categoria_id= request.POST.get("categoria_id")
        genero      = request.POST.get("genero")
        en_oferta   = request.POST.get("en_oferta") == "on"
        imagen      = request.FILES.get("imagen")

        tallas = request.POST.getlist("tallas")
        stocks = request.POST.getlist("stocks")

    # Validaciones mínimas
    if not nombre: return JsonResponse({"error": "Falta campo 'nombre'"}, status=400)
    if not descripcion: return JsonResponse({"error": "Falta campo 'descripcion'"}, status=400)
    if precio is None: return JsonResponse({"error": "Falta campo 'precio'"}, status=400)
    if not categoria_id: return JsonResponse({"error": "Falta campo 'categoria_id'"}, status=400)
    if not genero: return JsonResponse({"error": "Falta campo 'genero'"}, status=400)

    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        return JsonResponse({"error": "Categoría no encontrada"}, status=404)

    try:
        precio = float(precio)
        precio_mayorista = float(precio_mayorista)
    except ValueError:
        return JsonResponse({"error": "precio y precio_mayorista deben ser numéricos"}, status=400)

    # Crear producto
    producto = Producto.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        precio_mayorista=precio_mayorista,
        categoria=categoria,
        genero=genero,
        en_oferta=en_oferta,
        imagen=imagen,
    )

    # Sistema nuevo: Variantes con talla y color directos
    # Variantes múltiples (tallas + stocks)
    primera_variante_precio = None
    if tallas and stocks and len(tallas) == len(stocks):
        try:
            stocks = [int(s) for s in stocks]
        except:
            return JsonResponse({"error": "Stock debe ser numérico"}, status=400)

        for idx, (talla, stock) in enumerate(zip(tallas, stocks)):
            variante = Variante.objects.create(
                producto=producto,
                talla=talla,
                color=data.get("color", "N/A") if request.content_type.startswith("application/json") else request.POST.get("color", "N/A"),
                precio=precio,
                precio_mayorista=precio_mayorista,
                stock=stock,
            )
            # Capturar precio de la primera variante
            if idx == 0:
                primera_variante_precio = variante.precio

    # Variante simple (stock único)
    else:
        stock_unico = data.get("stock") if request.content_type.startswith("application/json") else request.POST.get("stock")
        talla_unica = data.get("talla", "UNICA") if request.content_type.startswith("application/json") else request.POST.get("talla", "UNICA")
        color_unico = data.get("color", "N/A") if request.content_type.startswith("application/json") else request.POST.get("color", "N/A")

        if stock_unico is None:
            return JsonResponse({"error": "Falta campo 'stock'"}, status=400)

        try:
            stock_unico = int(stock_unico)
        except:
            return JsonResponse({"error": "stock debe ser numérico"}, status=400)

        variante = Variante.objects.create(
            producto=producto,
            talla=talla_unica,
            color=color_unico,
            precio=precio,
            precio_mayorista=precio_mayorista,
            stock=stock_unico,
        )
        primera_variante_precio = variante.precio

    # Sincronizar el precio del producto con la primera variante
    if primera_variante_precio is not None:
        producto.precio = primera_variante_precio
        producto.save()

    return JsonResponse(
        {"id": producto.id, "message": "Producto y variantes creados"},
        status=201
    )

@csrf_exempt
@admin_required()
@require_http_methods(["POST", "PUT"])
def update_productos(request, id):
    producto = get_object_or_404(Producto, id=id)

    # Campos del Producto
    from decimal import Decimal  # asegúrate de tener esta importación al inicio del archivo

    # Campos del Producto
    campos = ('nombre', 'descripcion', 'precio', 'precio_mayorista', 'genero')
    for field in campos:
        if field in request.POST:
            valor = request.POST[field]
            if field in ['precio', 'precio_mayorista']:
                try:
                    valor = Decimal(valor)
                except:
                    return JsonResponse({'error': f'Formato inválido en {field}'}, status=400)
            setattr(producto, field, valor)


    if 'en_oferta' in request.POST:
        producto.en_oferta = request.POST.get('en_oferta') == 'on'

    if 'categoria_id' in request.POST:
        try:
            producto.categoria = Categoria.objects.get(id=request.POST['categoria_id'])
        except Categoria.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)

    if 'imagen' in request.FILES:
        imagen_file = request.FILES['imagen']
        # Usar la función canónica para generar el nombre
        nombre_canonico = producto._generate_image_key(imagen_file.name)
        imagen_file.name = nombre_canonico
        producto.imagen = imagen_file

    producto.save()
    return JsonResponse(
        {'mensaje': f'Producto {producto.id} actualizado correctamente'},
        status=200
    )

@csrf_exempt
@admin_required()
@require_http_methods(["POST", "PUT"])
def update_variant(request, variante_id):

    variante = get_object_or_404(Variante, id=variante_id)
    precio_actualizado = False

    if 'stock' in request.POST:
        variante.stock = int(request.POST['stock'])
    if 'precio' in request.POST:
        variante.precio = request.POST['precio']
        precio_actualizado = True
    if 'precio_mayorista' in request.POST:
        variante.precio_mayorista = request.POST['precio_mayorista']
    if 'sku' in request.POST:
        variante.sku = request.POST['sku']
    if 'talla' in request.POST:
        variante.talla = request.POST['talla']
    if 'color' in request.POST:
        variante.color = request.POST['color']
    
    # Manejo de imagen de variante
    if 'imagen' in request.FILES:
        imagen_file = request.FILES['imagen']
        # Usar la función canónica para generar el nombre
        nombre_canonico = variante._generate_image_key(imagen_file.name)
        imagen_file.name = nombre_canonico
        variante.imagen = imagen_file

    variante.save()
    
    # Si esta es la primera variante y se actualizó el precio, sincronizar con el producto
    if precio_actualizado:
        primera_variante = variante.producto.variantes.order_by('id').first()
        if primera_variante and primera_variante.id == variante.id:
            variante.producto.precio = variante.precio
            variante.producto.save()
    
    return JsonResponse(
        {'message': f'Variante {variante.id} actualizada correctamente'},
        status=200
    )

@csrf_exempt
@admin_required()
@require_http_methods(["DELETE", "POST"])
def delete_productos(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return JsonResponse({'mensaje': f'Producto {producto.nombre} y sus variantes eliminados'}, status=200)

@csrf_exempt
@admin_required()
@require_http_methods(["DELETE"])
def delete_all_productos(request):
    # Contamos cuántos productos hay antes de borrarlos
    total = Producto.objects.count()
    # Eliminamos todos los productos
    Producto.objects.all().delete()
    return JsonResponse(
        {'mensaje': f'Se eliminaron {total} productos y sus variantes'},
        status=200
    )