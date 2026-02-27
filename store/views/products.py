import json
from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Producto, Categoria, Variante, Subcategoria
from .decorators import login_required_user, login_required_client, jwt_role_required, admin_required, inventory_manager_required
from django.db.models import Prefetch, Q
from django.db import models
from decimal import Decimal, InvalidOperation
import json
from django.views.decorators.csrf import csrf_exempt
from ..utils.serializers import serializar_producto_completo
import os  # Importar os para operaciones de archivo
from store.models import VarianteImagen
import logging
logger = logging.getLogger(__name__)

def detalle_producto(request, id):
    producto = get_object_or_404(
        Producto.objects.prefetch_related("variantes", "variantes__imagenes"),
        id=id
    )

    # ─── 1. Tallas y colores disponibles ───────────────────────────
    tallas = set()
    colores = set()

    variantes_serializadas = []    # para el JS
    for v in producto.variantes.all():
        # Extraer tallas del JSONField
        for talla_key in v.tallas_stock.keys():
            tallas.add(talla_key)
        if v.color:
            colores.add(v.color)

        # Obtener imágenes de la variante
        imagenes_variante = [img.imagen.url for img in v.imagenes.all().order_by('orden') if img.imagen]
        
        variantes_serializadas.append({
            "id"          : v.id,
            "color"       : v.color,
            "precio"      : float(v.precio or producto.precio),
            "tallas_stock": v.tallas_stock,
            "stock_total" : v.stock_total_variante,
            "imagenes"    : imagenes_variante,
        })

    # Obtener imágenes de la variante principal (para cuando no hay variante seleccionada)
    variante_principal = producto.variante_principal
    imagenes_producto = []
    if variante_principal:
        imagenes_producto = [img.imagen.url for img in variante_principal.imagenes.all().order_by('orden') if img.imagen]

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
            "imagenes_producto": imagenes_producto,
            "variantes_json" : variantes_serializadas,
        },
    )



#@jwt_role_required()  # Público - Ver detalles de producto
@require_GET
def get_all_products(request):

    productos = Producto.objects.prefetch_related('variantes', 'variantes__imagenes')
    data = []
    for p in productos:
        variantes = []
        for v in p.variantes.all():
            # Obtener imágenes de la galería de la variante
            imagenes_variante = [img.imagen.url for img in v.imagenes.all().order_by('orden') if img.imagen]
            
            variantes.append({
                'id': v.id,
                'sku': v.sku,
                'color': v.color,
                'tallas_stock': v.tallas_stock or {},
                'otros': v.otros,
                'precio': float(v.precio or p.precio),
                'precio_mayorista': float(v.precio_mayorista or p.precio_mayorista),
                'stock_total': v.stock_total_variante,
                'imagen': imagenes_variante[0] if imagenes_variante else '',
                'imagenes': imagenes_variante,
            })
        
        # Galería de imágenes de la variante principal
        variante_principal = p.variante_principal
        galeria = []
        if variante_principal:
            galeria = [img.imagen.url for img in variante_principal.imagenes.all().order_by('orden') if img.imagen]
        
        # La imagen principal siempre es la primera de la galería
        # Esto asegura consistencia: no hay imágenes duplicadas
        imagen_principal = galeria[0] if galeria else ''

        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'categoria': p.categoria.nombre,
            'categoria_id': p.categoria.id,
            'genero': p.genero,
            'en_oferta': p.en_oferta,
            'bodega': p.bodega,  # Campo para verificar visibilidad
            'imagen': imagen_principal,
            'imagenes': galeria,
            'created_at': p.created_at.isoformat(),
            'stock_total': p.stock_total,
            'variantes': variantes,
        })

    return JsonResponse(data, safe=False)

@csrf_exempt
@inventory_manager_required()
@require_http_methods(["POST"])
def create_product(request):

    # Detecta si el request viene en JSON o multipart/form-data ( si trae una imagen o no)
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
        bodega      = data.get("bodega", True)  # Default True para inventario
        imagen      = None  # No hay archivos en JSON

        tallas = data.get("tallas", [])
        stocks = data.get("stocks", [])
        subcategorias_ids = data.get("subcategorias", [])

    else:  # multipart/form-data (con imagen desde dashboard)
        logger.info(f"[CREATE_PRODUCT] FormData recibido - Content-Type: {request.content_type}")
        logger.info(f"[CREATE_PRODUCT] POST data: {dict(request.POST)}")
        
        nombre      = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio      = request.POST.get("precio")
        precio_mayorista = request.POST.get("precio_mayorista", precio)
        categoria_id= request.POST.get("categoria_id")
        genero      = request.POST.get("genero")
        en_oferta   = request.POST.get("en_oferta") == "on"
        
        # Verificar campo bodega
        bodega_value = request.POST.get("bodega")
        logger.info(f"[CREATE_PRODUCT] Campo bodega recibido: '{bodega_value}' (type: {type(bodega_value)})")
        bodega = bodega_value == "on"
        logger.info(f"[CREATE_PRODUCT] bodega final: {bodega}")
        
        imagen      = request.FILES.get("imagen")

        tallas = request.POST.getlist("tallas")
        stocks = request.POST.getlist("stocks")
        subcategorias_ids = request.POST.getlist("subcategorias")

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
    # bodega: viene del request (True desde inventario, variable desde dashboard)
    producto = Producto.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        precio_mayorista=precio_mayorista,
        categoria=categoria,
        genero=genero,
        en_oferta=en_oferta,
        bodega=bodega,
    )

    # Sistema nuevo: 1 variante = 1 color, con tallas_stock JSONField
    # Variantes múltiples (tallas + stocks → agrupadas por color)
    primera_variante_precio = None
    primera_variante_creada = False
    if tallas and stocks and len(tallas) == len(stocks):
        try:
            stocks = [int(s) for s in stocks]
        except (ValueError, TypeError):
            return JsonResponse({"error": "Stock debe ser numérico"}, status=400)

        # Obtener colores, precios, precios_mayorista (pueden estar vacíos)
        colores = request.POST.getlist("colores") if request.method == "POST" else []
        precios_var = request.POST.getlist("precios") if request.method == "POST" else []
        precios_mayorista_var = request.POST.getlist("precios_mayorista") if request.method == "POST" else []

        # Agrupar tallas por color para crear 1 variante por color
        color_variants = {}  # {color: {tallas_stock: {}, precio: X, precio_mayorista: Y, idx: 0}}
        for idx, (talla, stock) in enumerate(zip(tallas, stocks)):
            color = colores[idx] if idx < len(colores) and colores[idx] else "N/A"
            
            precio_var = precio
            if idx < len(precios_var) and precios_var[idx]:
                try:
                    precio_var = float(precios_var[idx])
                except ValueError:
                    precio_var = precio
            
            pmay = precio_mayorista
            if idx < len(precios_mayorista_var) and precios_mayorista_var[idx]:
                try:
                    pmay = float(precios_mayorista_var[idx])
                except ValueError:
                    pmay = precio_mayorista
            
            if color not in color_variants:
                color_variants[color] = {
                    'tallas_stock': {},
                    'precio': precio_var,
                    'precio_mayorista': pmay,
                    'idx': idx,  # Para buscar imágenes
                }
            color_variants[color]['tallas_stock'][talla] = stock

        # Crear una variante por color
        is_first = True
        for color, cv_data in color_variants.items():
            variante = Variante.objects.create(
                producto=producto,
                color=color,
                tallas_stock=cv_data['tallas_stock'],
                precio=cv_data['precio'],
                precio_mayorista=cv_data['precio_mayorista'],
                es_variante_principal=is_first,
            )
            if is_first:
                primera_variante_precio = variante.precio
                primera_variante_creada = True
            
            # 🖼️ PROCESAR IMÁGENES DE ESTA VARIANTE
            # Buscar imágenes por el índice original de la primera talla de este color
            try:
                from store.models import VarianteImagen
                import os
                
                img_idx = cv_data['idx']
                imagenes_variante = request.FILES.getlist(f'variante_imagen_temp_{img_idx}')
                
                if imagenes_variante:
                    
                    for img_order, imagen_file in enumerate(imagenes_variante, start=1):
                        if img_order > 5:
                            break
                        try:
                            ext = os.path.splitext(imagen_file.name)[1]
                            nombre_canonico = f'imagen-{img_order}{ext}'
                            imagen_file.name = nombre_canonico
                            
                            variante_imagen = VarianteImagen(
                                variante=variante,
                                imagen=imagen_file,
                                orden=img_order
                            )
                            variante_imagen.save()
                        except Exception as e:
                            pass
            except Exception as e:
                pass
            is_first = False

    # Variante simple (stock único)
    else:
        stock_unico = data.get("stock") if request.content_type.startswith("application/json") else request.POST.get("stock")
        talla_unica = data.get("talla", "UNICA") if request.content_type.startswith("application/json") else request.POST.get("talla", "UNICA")
        color_unico = data.get("color", "N/A") if request.content_type.startswith("application/json") else request.POST.get("color", "N/A")

        # Si no hay stock, usar 0 como valor por defecto
        if stock_unico is None:
            stock_unico = 0

        try:
            stock_unico = int(stock_unico)
        except (ValueError, TypeError):
            return JsonResponse({"error": "stock debe ser numérico"}, status=400)

        variante = Variante.objects.create(
            producto=producto,
            color=color_unico,
            tallas_stock={talla_unica: stock_unico},
            precio=precio,
            precio_mayorista=precio_mayorista,
            es_variante_principal=True,
        )
        primera_variante_precio = variante.precio
        primera_variante_creada = True

    # Sincronizar el precio del producto con la primera variante
    if primera_variante_precio is not None:
        producto.precio = primera_variante_precio
        producto.save()

    # Procesar subcategorías si se enviaron
    if subcategorias_ids:
        try:
            subcategorias = Subcategoria.objects.filter(id__in=subcategorias_ids)
            producto.subcategorias.set(subcategorias)
        except Exception as e:
            logger.warning(f"Error al guardar subcategorías: {e}")

    return JsonResponse(
        {"id": producto.id, "message": "Producto y variantes creados"},
        status=201
    )

@csrf_exempt
@inventory_manager_required()
@require_http_methods(["POST", "PUT"])
def update_productos(request, id):
    try:
        producto = get_object_or_404(Producto, id=id)
        campos = ('nombre', 'descripcion', 'precio', 'precio_mayorista', 'genero')
        for field in campos:
            if field in request.POST:
                valor = request.POST[field]
                if field in ['precio', 'precio_mayorista']:
                    try:
                        valor = Decimal(valor)
                    except (ValueError, TypeError, InvalidOperation):
                        return JsonResponse({'error': f'Formato inválido en {field}'}, status=400)
                setattr(producto, field, valor)


        if 'en_oferta' in request.POST:
            producto.en_oferta = request.POST.get('en_oferta') == 'on'
        
        # Campo bodega (solo editable desde dashboard)
        if 'bodega' in request.POST:
            producto.bodega = request.POST.get('bodega') == 'on'

        if 'categoria_id' in request.POST:
            try:
                producto.categoria = Categoria.objects.get(id=request.POST['categoria_id'])
            except Categoria.DoesNotExist:
                return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        
        producto.save()

        # Procesar subcategorías si se enviaron
        subcategorias_ids = request.POST.getlist('subcategorias')
        if subcategorias_ids:
            try:
                subcategorias = Subcategoria.objects.filter(id__in=subcategorias_ids)
                producto.subcategorias.set(subcategorias)
            except Exception as e:
                logger.warning(f"Error al guardar subcategorías: {e}")
        
        # Validación: Si el producto no tiene variantes, crear una variante por defecto
        if not producto.variantes.exists():
            Variante.objects.create(
                producto=producto,
                color='N/A',
                tallas_stock={'UNICA': 0},
                precio=producto.precio,
                precio_mayorista=producto.precio_mayorista,
                es_variante_principal=True,
            )

        # 1. ELIMINAR IMÁGENES DE VARIANTES MARCADAS PARA ELIMINACIÓN
        # Buscar todas las claves con formato: variante_imagenes_a_eliminar_{variante_id}
        for key in request.POST:
            if key.startswith('variante_imagenes_a_eliminar_'):
                try:
                    # Extraer variante_id del nombre de la clave
                    variante_id_str = key.replace('variante_imagenes_a_eliminar_', '')
                    variante_id = int(variante_id_str)
                    
                    # Obtener el JSON con los IDs de imágenes a eliminar
                    ids_json = request.POST.get(key, '')
                    if ids_json:
                        try:
                            ids_a_eliminar = json.loads(ids_json)
                            if isinstance(ids_a_eliminar, list) and ids_a_eliminar:
                                # Eliminar cada imagen
                                for img_id in ids_a_eliminar:
                                    try:
                                        # Asegurar que img_id es un entero
                                        img_id_int = int(img_id) if not isinstance(img_id, int) else img_id
                                        img = VarianteImagen.objects.get(id=img_id_int, variante__producto=producto)
                                        img.delete()
                                    except VarianteImagen.DoesNotExist:
                                        pass
                                    except ValueError:
                                        pass
                                    except Exception:
                                        pass
                        except (json.JSONDecodeError, ValueError):
                            pass
                except (ValueError, IndexError):
                    pass
    
        # 2. PROCESAR NUEVAS IMÁGENES DE VARIANTES
        # Agrupar imágenes por variante_id para procesarlas de forma correcta
        variante_imagenes = {}
        
        for key in request.FILES:
            if key.startswith('variante_imagen_'):
                try:
                    # Formato: variante_imagen_{variante_id}_{idx}
                    parts = key.split('_')
                    if len(parts) >= 4:
                        variante_id = int(parts[2])
                        if variante_id not in variante_imagenes:
                            variante_imagenes[variante_id] = []
                        variante_imagenes[variante_id].append(request.FILES[key])
                except (ValueError, IndexError):
                    pass
        
        # Procesar cada grupo de imágenes por variante
        for variante_id, imagenes_list in variante_imagenes.items():
            try:
                variante = producto.variantes.get(id=variante_id)
                
                # IMPORTANTE: Después de las eliminaciones, recompactar los órdenes de las imágenes restantes
                # para evitar huecos en la numeración (1, 2, 3... en vez de 1, 3, 5...)
                imagenes_existentes = list(variante.imagenes.all().order_by('orden'))
                
                # Renumerar las imágenes existentes secuencialmente
                for nuevo_orden, img_existente in enumerate(imagenes_existentes, start=1):
                    if img_existente.orden != nuevo_orden:
                        img_existente.orden = nuevo_orden
                        img_existente.save()
                
                # Ahora calcular cuántas imágenes tenemos y cuántas podemos agregar
                current_count = len(imagenes_existentes)
                espacios_disponibles = 5 - current_count
                
                if current_count + len(imagenes_list) > 5:
                    continue
                
                # Agregar las nuevas imágenes en orden secuencial
                next_orden = current_count + 1
                
                for idx, imagen_file in enumerate(imagenes_list):
                    numero_orden = next_orden + idx
                    
                    # Generar nombre canónico
                    ext = os.path.splitext(imagen_file.name)[1]
                    nombre_canonico = f'imagen-{numero_orden}{ext}'
                    imagen_file.name = nombre_canonico
                    
                    # Crear VarianteImagen
                    variante_imagen = VarianteImagen(
                        variante=variante,
                        imagen=imagen_file,
                        orden=numero_orden
                    )
                    variante_imagen.save()
            except Variante.DoesNotExist:
                pass
            except Exception:
                pass

        return JsonResponse(
            {'mensaje': f'Producto {producto.id} actualizado correctamente'},
            status=200
        )
    
    except Exception as e:
        return JsonResponse(
            {'error': f'Error al actualizar producto: {str(e)}'},
            status=500
        )

@csrf_exempt
@inventory_manager_required()
@require_http_methods(["POST"])
def create_variant(request):
    """
    POST /api/variantes/create/
    Crea una nueva variante para un producto existente.
    
    Parámetros:
    - producto_id: ID del producto (requerido)
    - color: Color de la variante
    - tallas_stock: JSON con tallas y stock {'38': 5, '39': 10} (preferido)
    - talla + stock: Talla y stock individual (backward compatibility)
    - precio: Precio (opcional, usa el del producto si no se especifica)
    - precio_mayorista: Precio mayorista (opcional)
    - imagenes_*: Imágenes de la variante (múltiples archivos soportados)
    """
    from decimal import Decimal
    import json
    
    try:
        producto_id = request.POST.get('producto_id')
        if not producto_id:
            return JsonResponse({'error': 'Falta producto_id'}, status=400)
        
        producto = get_object_or_404(Producto, id=producto_id)
        
        color = request.POST.get('color', 'N/A')
        precio_str = request.POST.get('precio', str(producto.precio))
        precio_mayorista_str = request.POST.get('precio_mayorista', str(producto.precio_mayorista))
        
        # Parsear tallas_stock como JSON o usar talla+stock individual
        tallas_stock = {}
        if 'tallas_stock' in request.POST:
            try:
                ts = json.loads(request.POST['tallas_stock'])
                if isinstance(ts, dict):
                    tallas_stock = {k: int(v) for k, v in ts.items()}
            except (json.JSONDecodeError, ValueError) as e:
                return JsonResponse({'error': f'tallas_stock inválido: {str(e)}'}, status=400)
        elif 'talla' in request.POST and 'stock' in request.POST:
            # Backward compatibility
            talla = request.POST.get('talla', 'UNICA')
            stock = int(request.POST.get('stock', 0))
            tallas_stock = {talla: stock}
        else:
            return JsonResponse({'error': 'Falta tallas_stock o talla+stock'}, status=400)
        
        try:
            precio = Decimal(precio_str)
            precio_mayorista = Decimal(precio_mayorista_str)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Precio inválido'}, status=400)
        
        # Crear la variante
        variante = Variante.objects.create(
            producto=producto,
            color=color,
            tallas_stock=tallas_stock,
            precio=precio,
            precio_mayorista=precio_mayorista,
        )
        
        # Manejar imágenes de la variante (formato: imagenes_0, imagenes_1, etc.)
        imagenes_guardadas = 0
        for key in request.FILES.keys():
            if key.startswith('imagenes_'):
                imagen_file = request.FILES[key]
                try:
                    # Generar nombre canónico
                    nombre_canonico = variante._generate_image_key(imagen_file.name)
                    
                    # Crear VarianteImagen
                    variante_imagen = VarianteImagen(
                        variante=variante,
                        imagen=imagen_file,
                        orden=imagenes_guardadas
                    )
                    variante_imagen.imagen.name = nombre_canonico
                    variante_imagen.save()
                    imagenes_guardadas += 1
                except Exception as e:
                    logger.warning(f"Error al guardar imagen para variante {variante.id}: {e}")
        
        return JsonResponse({
            'id': variante.id,
            'mensaje': f'Variante {variante.id} creada correctamente',
            'imagenes_guardadas': imagenes_guardadas
        }, status=201)
    
    except Exception as e:
        logger.warning(f"Error al crear variante: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@inventory_manager_required()
@require_http_methods(["POST"])
def update_variant(request, variante_id):

    variante = get_object_or_404(Variante, id=variante_id)
    precio_actualizado = False

    # Manejar tallas_stock como JSON
    if 'tallas_stock' in request.POST:
        try:
            import json
            ts = json.loads(request.POST['tallas_stock'])
            if isinstance(ts, dict):
                variante.tallas_stock = {k: int(v) for k, v in ts.items()}
        except (json.JSONDecodeError, ValueError):
            pass
    # Backward compat: si envían talla+stock individuales, actualizar en tallas_stock
    elif 'stock' in request.POST:
        talla_key = request.POST.get('talla', '')
        stock_val = int(request.POST['stock'])
        if talla_key:
            variante.tallas_stock[talla_key] = stock_val
        else:
            # Si solo hay una talla, actualizar esa
            if len(variante.tallas_stock) == 1:
                key = next(iter(variante.tallas_stock))
                variante.tallas_stock[key] = stock_val
            else:
                variante.tallas_stock['UNICA'] = stock_val

    if 'precio' in request.POST:
        variante.precio = request.POST['precio']
        precio_actualizado = True
    if 'precio_mayorista' in request.POST:
        variante.precio_mayorista = request.POST['precio_mayorista']
    if 'sku' in request.POST:
        variante.sku = request.POST['sku']
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
@inventory_manager_required()
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
