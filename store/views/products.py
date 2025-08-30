from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Atributo, AtributoValor, Producto, Categoria, Variante
from .decorators import login_required_user, login_required_client
from django.db.models import Prefetch
from decimal import Decimal
from .decorators import jwt_role_required
import json

from django.views.decorators.csrf import csrf_exempt


def detalle_producto(request, id):
    producto = get_object_or_404(
        Producto.objects.prefetch_related(
            Prefetch(
                "variantes__attrs__atributo_valor__atributo",
                # solo cargamos los atributos vinculados
            )
        ),
        id=id,
    )

    # ─── 1. Lista de tallas disponibles ───────────────────────────
    atributo_talla = Atributo.objects.filter(nombre__iexact="Talla").first()
    tallas = set()

    variantes_serializadas = []    # para el JS
    for v in producto.variantes.all():
        attrs = {av.atributo_valor.atributo.nombre: av.atributo_valor.valor
                 for av in v.attrs.all()}

        talla = attrs.get("Talla")
        if talla:
            tallas.add(talla)

        variantes_serializadas.append({
            "id"    : v.id,
            "talla" : talla,
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
            "tallas"         : sorted(tallas, key=lambda x: float(x)),
            "variantes_json" : json.dumps(variantes_serializadas),
        },
    )



#@login_required_user          # (opcional, según tu negocio)
#@require_GET
def get_all_products(request):

    productos = Producto.objects.prefetch_related('variantes__attrs__atributo_valor__atributo')
    data = []
    for p in productos:
        variantes = []
        for v in p.variantes.all():
            # recoger los atributos de la variante (talla, color…)
            attrs = {
                attr.atributo_valor.atributo.nombre: attr.atributo_valor.valor
                for attr in v.attrs.all()
            }
            variantes.append({
                'id': v.id,
                'sku': v.sku,
                'precio': float(v.precio or p.precio),
                'precio_mayorista': float(v.precio_mayorista or p.precio_mayorista),
                'stock': v.stock,
                'atributos': attrs,
            })

        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'categoria': p.categoria.nombre,
            'genero': p.genero,
            'en_oferta': p.en_oferta,
            'imagen': p.imagen.url if p.imagen else '',
            'created_at': p.created_at.isoformat(),
            'stock_total': p.stock_total,
            'variantes': variantes,
        })

    return JsonResponse(data, safe=False)
#@login_required_user
@csrf_exempt

@require_http_methods(["POST"])
def create_product(request):
    try:
        # ─── Datos básicos del producto ─────────────────────────────
        nombre      = request.POST['nombre']
        descripcion = request.POST['descripcion']
        precio      = request.POST['precio']
        precio_mayorista = request.POST['precio_mayorista']
        categoria   = Categoria.objects.get(id=request.POST['categoria_id'])
        genero      = request.POST['genero']
        en_oferta   = request.POST.get('en_oferta') == 'on'
        imagen      = request.FILES.get('imagen')

        # ─── Arrays de tallas y stocks (si existen) ─────────────────
        tallas = request.POST.getlist('tallas')
        stocks = request.POST.getlist('stocks')

        # Normaliza a ints
        stocks = [int(s) for s in stocks]

    except KeyError as ke:
        return JsonResponse({'error': f'Falta campo {ke}'}, status=400)
    except Categoria.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=404)

    # ─── Crea el producto ──────────────────────────────────────────
    producto = Producto.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        precio_mayorista= precio_mayorista,
        categoria=categoria,
        genero=genero,
        en_oferta=en_oferta,
        imagen=imagen,
    )

    # ─── Atributo “Talla” (solo se crea/obtiene una vez) ───────────
    atributo_talla, _ = Atributo.objects.get_or_create(nombre='Talla')

    # ────────────────────────────────────────────────────────────────
    # CASO A) Arrays tallas+stocks recibidos y longitudes iguales
    # ────────────────────────────────────────────────────────────────
    if tallas and len(tallas) == len(stocks):
        for talla, stock in zip(tallas, stocks):
            valor_talla, _ = AtributoValor.objects.get_or_create(
                atributo=atributo_talla,
                valor=talla
            )
            variante = Variante.objects.create(
                producto=producto,
                precio=precio,
                precio_mayorista=precio_mayorista,
                stock=stock,
            )
            variante.attrs.create(atributo_valor=valor_talla)

    # ────────────────────────────────────────────────────────────────
    # CASO B) Formulario simple: solo llega “stock” (y opcionalmente “talla”)
    # ────────────────────────────────────────────────────────────────
    else:
        try:
            stock_unico = int(request.POST['stock'])
        except (KeyError, ValueError):
            return JsonResponse({'error': 'Falta campo stock'}, status=400)

        talla_unica = request.POST.get('talla', 'Única')
        valor_talla, _ = AtributoValor.objects.get_or_create(
            atributo=atributo_talla,
            valor=talla_unica
        )
        variante = Variante.objects.create(
            producto=producto,
            precio=precio,
            precio_mayorista=precio_mayorista,
            stock=stock_unico,
        )
        variante.attrs.create(atributo_valor=valor_talla)

    return JsonResponse(
        {'id': producto.id, 'message': 'Producto y variantes creados'}, 
        status=201
    )

@login_required_user
@require_http_methods(["POST"])
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
        producto.imagen = request.FILES['imagen']

    producto.save()
    return JsonResponse(
        {'mensaje': f'Producto {producto.id} actualizado correctamente'},
        status=200
    )

@login_required_user 
@require_http_methods(["POST"])
def update_variant(request, variante_id):

    variante = get_object_or_404(Variante, id=variante_id)

    if 'stock' in request.POST:
        variante.stock = int(request.POST['stock'])
    if 'precio' in request.POST:
        variante.precio = request.POST['precio']

    if 'precio_mayorista' in request.POST:
        variante.precio_mayorista = request.POST['precio_mayorista']
    if 'sku' in request.POST:
        variante.sku = request.POST['sku']

    variante.save()
    return JsonResponse(
        {'message': f'Variante {variante.id} actualizada correctamente'},
        status=200
    )

@login_required_user
@require_http_methods(["POST"])
def delete_productos(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return JsonResponse({'mensaje': f'Producto {producto.nombre} y sus variantes eliminados'}, status=200)

@csrf_exempt
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