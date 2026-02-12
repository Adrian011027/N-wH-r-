import json
from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Producto, Categoria, Variante, Subcategoria
from .decorators import login_required_user, login_required_client, jwt_role_required, admin_required
from django.db.models import Prefetch, Q
from django.db import models
from decimal import Decimal
from .decorators import jwt_role_required
import json
from django.views.decorators.csrf import csrf_exempt
from ..utils.serializers import serializar_producto_completo


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
        if v.talla:
            tallas.add(v.talla)
        if v.color:
            colores.add(v.color)

        # Obtener imágenes de la variante
        imagenes_variante = [img.imagen.url for img in v.imagenes.all().order_by('orden') if img.imagen]
        
        variantes_serializadas.append({
            "id"    : v.id,
            "talla" : v.talla,
            "color" : v.color,
            "precio": float(v.precio or producto.precio),
            "stock" : v.stock,
            "imagenes": imagenes_variante,  # Imágenes específicas de la variante
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
            "imagenes_producto": imagenes_producto,  # Imágenes del producto base
            "variantes_json" : json.dumps(variantes_serializadas),
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
            'imagen': imagen_principal,
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
        imagen      = None  # No hay archivos en JSON

        tallas = data.get("tallas", [])
        stocks = data.get("stocks", [])
        subcategorias_ids = data.get("subcategorias", [])

    else:  # multipart/form-data (con imagen)
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
    producto = Producto.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        precio_mayorista=precio_mayorista,
        categoria=categoria,
        genero=genero,
        en_oferta=en_oferta,
    )

    # Sistema nuevo: Variantes con talla y color directos
    # Variantes múltiples (tallas + stocks)
    primera_variante_precio = None
    primera_variante_creada = False
    if tallas and stocks and len(tallas) == len(stocks):
        try:
            stocks = [int(s) for s in stocks]
        except:
            return JsonResponse({"error": "Stock debe ser numérico"}, status=400)

        # Obtener colores, precios, precios_mayorista (pueden estar vacíos)
        colores = request.POST.getlist("colores") if request.method == "POST" else []
        precios_var = request.POST.getlist("precios") if request.method == "POST" else []
        precios_mayorista_var = request.POST.getlist("precios_mayorista") if request.method == "POST" else []

        for idx, (talla, stock) in enumerate(zip(tallas, stocks)):
            # Obtener color de esta variante (o usar N/A)
            color = colores[idx] if idx < len(colores) and colores[idx] else "N/A"
            
            # Obtener precio de esta variante (o usar el del producto)
            precio_var = precio
            if idx < len(precios_var) and precios_var[idx]:
                try:
                    precio_var = float(precios_var[idx])
                except ValueError:
                    precio_var = precio
            
            # Obtener precio mayorista de esta variante (o usar el del producto)
            precio_mayorista_var = precio_mayorista
            if idx < len(precios_mayorista_var) and precios_mayorista_var[idx]:
                try:
                    precio_mayorista_var = float(precios_mayorista_var[idx])
                except ValueError:
                    precio_mayorista_var = precio_mayorista
            
            variante = Variante.objects.create(
                producto=producto,
                talla=talla,
                color=color,
                precio=precio_var,
                precio_mayorista=precio_mayorista_var,
                stock=stock,
                es_variante_principal=(idx == 0),  # Marcar la primera como principal
            )
            # Capturar precio de la primera variante
            if idx == 0:
                primera_variante_precio = variante.precio
                primera_variante_creada = True
            
            # 🖼️ PROCESAR IMÁGENES DE ESTA VARIANTE
            try:
                from store.models import VarianteImagen
                import os
                
                # Obtener imágenes para esta variante específica (formato: variante_imagen_temp_{idx})
                imagenes_variante = request.FILES.getlist(f'variante_imagen_temp_{idx}')
                
                if imagenes_variante:
                    print(f"[VARIANTE {idx}] Procesando {len(imagenes_variante)} imagen(es)")
                    
                    for img_idx, imagen_file in enumerate(imagenes_variante, start=1):
                        if img_idx > 5:  # Máximo 5 imágenes por variante
                            break
                        
                        try:
                            # Generar nombre canonico
                            ext = os.path.splitext(imagen_file.name)[1]
                            nombre_canonico = f'imagen-{img_idx}{ext}'
                            imagen_file.name = nombre_canonico
                            
                            # Crear VarianteImagen
                            variante_imagen = VarianteImagen(
                                variante=variante,
                                imagen=imagen_file,
                                orden=img_idx
                            )
                            variante_imagen.save()
                            print(f"[VARIANTE {idx}] Imagen guardada en orden {img_idx}")
                        except Exception as e:
                            print(f"[VARIANTE {idx}] Error guardando imagen {img_idx}: {e}")
            except Exception as e:
                print(f"[VARIANTE {idx}] Error general procesando imágenes: {e}")

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
        except:
            return JsonResponse({"error": "stock debe ser numérico"}, status=400)

        variante = Variante.objects.create(
            producto=producto,
            talla=talla_unica,
            color=color_unico,
            precio=precio,
            precio_mayorista=precio_mayorista,
            stock=stock_unico,
            es_variante_principal=True,  # Variante única es siempre la principal
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
            print(f"Error al guardar subcategorías: {e}")

    return JsonResponse(
        {"id": producto.id, "message": "Producto y variantes creados"},
        status=201
    )

@csrf_exempt
@admin_required()
@require_http_methods(["POST", "PUT"])
def update_productos(request, id):
    try:
        producto = get_object_or_404(Producto, id=id)

        # Campos del Producto
        from decimal import Decimal  # asegúrate de tener esta importación al inicio del archivo
        import json  # Importar json para procesamiento de datos del frontend
        import os  # Importar os para operaciones de archivo

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
        
        producto.save()

        # Procesar subcategorías si se enviaron
        subcategorias_ids = request.POST.getlist('subcategorias')
        if subcategorias_ids:
            try:
                subcategorias = Subcategoria.objects.filter(id__in=subcategorias_ids)
                producto.subcategorias.set(subcategorias)
            except Exception as e:
                print(f"Error al guardar subcategorías: {e}")
        
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

        # ─────── PROCESAR IMÁGENES DE VARIANTES ───────
        from store.models import VarianteImagen
        
        
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
                            print(f"[DELETE] Variante {variante_id}: IDs recibidos del frontend: {ids_a_eliminar}")
                            
                            if isinstance(ids_a_eliminar, list) and ids_a_eliminar:
                                print(f"[DELETE] Variante {variante_id}: Procesando eliminación de {len(ids_a_eliminar)} imagen(es)")
                                # Eliminar cada imagen
                                for img_id in ids_a_eliminar:
                                    try:
                                        # Asegurar que img_id es un entero
                                        img_id_int = int(img_id) if not isinstance(img_id, int) else img_id
                                        print(f"[DELETE] Buscando imagen {img_id_int} para variante {variante_id}")
                                        
                                        img = VarianteImagen.objects.get(id=img_id_int, variante__producto=producto)
                                        img.delete()
                                        print(f"[DELETE] ✓ Imagen {img_id_int} eliminada exitosamente")
                                    except VarianteImagen.DoesNotExist:
                                        print(f"[SKIP] Imagen {img_id} no encontrada o no pertenece al producto")
                                    except ValueError as ve:
                                        print(f"[ERROR] ID inválido {img_id}: {ve}")
                                    except Exception as e:
                                        print(f"[ERROR] Error eliminando imagen {img_id}: {e}")
                                        import traceback
                                        traceback.print_exc()
                            else:
                                print(f"[SKIP] Array vacío o inválido para variante {variante_id}")
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"[ERROR] Error parseando JSON para {key}: {e}")
                            print(f"[ERROR] Contenido recibido: {ids_json}")
                except (ValueError, IndexError) as e:
                    print(f"[ERROR] Error extrayendo variante_id de {key}: {e}")
    
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
                        print(f"[GROUP] Imagen agregada al grupo de variante {variante_id}")
                except (ValueError, IndexError) as e:
                    print(f"[ERROR] Error parseando clave: {key} - {e}")
        
        # Procesar cada grupo de imágenes por variante
        for variante_id, imagenes_list in variante_imagenes.items():
            try:
                variante = producto.variantes.get(id=variante_id)
                print(f"[PROCESS] Procesando {len(imagenes_list)} imagen(es) para variante {variante_id}")
                
                for imagen_file in imagenes_list:
                    # Contar imágenes actuales (se recalcula cada vez para estar seguro)
                    current_count = variante.imagenes.count()
                    
                    if current_count >= 5:
                        print(f"[SKIP] Variante {variante_id}: límite de 5 imágenes alcanzado")
                        break
                    
                    # Generar nombre canónico
                    ext = os.path.splitext(imagen_file.name)[1]
                    numero_orden = current_count + 1
                    nombre_canonico = f'imagen-{numero_orden}{ext}'
                    imagen_file.name = nombre_canonico
                    
                    # Crear VarianteImagen
                    variante_imagen = VarianteImagen(
                        variante=variante,
                        imagen=imagen_file,
                        orden=numero_orden
                    )
                    variante_imagen.save()
                    print(f"[SUCCESS] Imagen guardada para variante {variante_id} en orden {numero_orden}: {variante_imagen.imagen.url}")
                    
            except Variante.DoesNotExist:
                print(f"[ERROR] Variante {variante_id} no encontrada para producto {producto.id}")
            except Exception as e:
                print(f"[ERROR] Error procesando imágenes para variante {variante_id}: {e}")
                import traceback
                traceback.print_exc()

        return JsonResponse(
            {'mensaje': f'Producto {producto.id} actualizado correctamente'},
            status=200
        )
    
    except Exception as e:
        print(f"[ERROR CRÍTICO] Error en update_productos: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse(
            {'error': f'Error al actualizar producto: {str(e)}'},
            status=500
        )

@csrf_exempt
@admin_required()
@require_http_methods(["POST"])
def create_variant(request):
    """
    POST /api/variantes/create/
    Crea una nueva variante para un producto existente.
    
    Parámetros:
    - producto_id: ID del producto
    - talla: Talla de la variante
    - color: Color de la variante
    - precio: Precio (opcional, usa el del producto si no se especifica)
    - precio_mayorista: Precio mayorista (opcional)
    - stock: Stock disponible
    """
    from decimal import Decimal
    
    try:
        producto_id = request.POST.get('producto_id')
        if not producto_id:
            return JsonResponse({'error': 'Falta producto_id'}, status=400)
        
        producto = get_object_or_404(Producto, id=producto_id)
        
        talla = request.POST.get('talla', 'UNICA')
        color = request.POST.get('color', 'N/A')
        precio_str = request.POST.get('precio', str(producto.precio))
        precio_mayorista_str = request.POST.get('precio_mayorista', str(producto.precio_mayorista))
        stock = request.POST.get('stock', 0)
        
        try:
            precio = Decimal(precio_str)
            precio_mayorista = Decimal(precio_mayorista_str)
            stock = int(stock)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Valores numéricos inválidos'}, status=400)
        
        # Crear la variante
        variante = Variante.objects.create(
            producto=producto,
            talla=talla,
            color=color,
            precio=precio,
            precio_mayorista=precio_mayorista,
            stock=stock
        )
        
        return JsonResponse({
            'id': variante.id,
            'mensaje': f'Variante {variante.id} creada correctamente'
        }, status=201)
    
    except Exception as e:
        print(f"Error al crear variante: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@admin_required()
@require_http_methods(["POST"])
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