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
        Producto.objects.prefetch_related("variantes", "variantes__imagenes", "imagenes"),
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

    # Obtener imágenes del producto base (para cuando no hay variante seleccionada)
    imagenes_producto = [img.imagen.url for img in producto.imagenes.all().order_by('orden') if img.imagen]

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
        galeria = [img.imagen.url for img in p.imagenes.all().order_by('orden') if img.imagen]
        
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

    # Crear producto (sin imagen - usará la primera de ProductoImagen)
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
            )
            # Capturar precio de la primera variante
            if idx == 0:
                primera_variante_precio = variante.precio
            
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
        )
        primera_variante_precio = variante.precio

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

    # 🖼️ PROCESAR IMÁGENES DE GALERÍA (máximo 5)
    # El frontend envía múltiples imágenes con el campo 'imagen_galeria_upload'
    imagen_contador = 0
    
    try:
        from store.models import ProductoImagen
        import os
        
        # Obtener TODAS las imágenes (usar getlist para campos múltiples)
        imagenes_galeria = request.FILES.getlist('imagen_galeria_upload')
        
        if imagenes_galeria:
            print(f"[IMAGES] Total de imágenes recibidas: {len(imagenes_galeria)}")
            
            for idx, imagen_file in enumerate(imagenes_galeria, start=1):
                if imagen_contador >= 5:  # Máximo 5 imágenes por producto
                    print(f"[SKIP] Se alcanzó máximo de 5 imágenes")
                    break
                
                try:
                    print(f"[PROCESSING] Procesando imagen {idx}: {imagen_file.name}, tamaño: {imagen_file.size} bytes")
                    
                    # Generar nombre del archivo: imagen-{numero}.{ext}
                    ext = os.path.splitext(imagen_file.name)[1]
                    numero_imagen = idx  # Usar el índice (1, 2, 3, 4, 5)
                    nombre_canonico = f'imagen-{numero_imagen}{ext}'
                    imagen_file.name = nombre_canonico
                    
                    print(f"[NAMING] Nombre canónico: {nombre_canonico}, orden: {numero_imagen}")
                    
                    # Crear instancia
                    producto_imagen = ProductoImagen(
                        producto=producto,
                        imagen=imagen_file,
                        orden=numero_imagen
                    )
                    
                    # Guardar
                    producto_imagen.save()
                    print(f"[SUCCESS] Imagen guardada en orden {numero_imagen} en: {producto_imagen.imagen.url}")
                    imagen_contador += 1
                    
                except Exception as e:
                    print(f"[ERROR] Error al procesar imagen {idx}: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"[INFO] No hay imágenes en request.FILES.getlist('imagen_galeria_upload')")
            
    except Exception as e:
        print(f"[ERROR] Error general al procesar imágenes: {e}")
        import traceback
        traceback.print_exc()

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

    # No procesar imagen principal - usar siempre la primera de ProductoImagen
    
    producto.save()

    # PROCESAR IMAGEN PRINCIPAL (imagen campo - tanto del API como del dashboard)
    # Puede venir como 'imagen' (API test) o 'imagen_galeria_upload' (dashboard edición)
    # En dashboard puede haber múltiples, se toma la primera
    imagen_files = []
    
    if 'imagen' in request.FILES:
        img = request.FILES['imagen']
        imagen_files.append(img)
        print("[UPLOAD] Imagen principal detectada (nombre de campo: 'imagen'): {}".format(img.name))
    
    if 'imagen_galeria_upload' in request.FILES:
        # Puede haber múltiples archivos con el mismo nombre
        imgs = request.FILES.getlist('imagen_galeria_upload')
        if imgs:
            print("[UPLOAD] {} imagen(es) de galería detectada(s) (nombre de campo: 'imagen_galeria_upload')".format(len(imgs)))
            imagen_files.extend(imgs)
    
    if imagen_files:
        print("[UPLOAD] Procesando imagen principal del producto {}".format(producto.id))
        # Usar solo la PRIMERA imagen como imagen principal (orden=1)
        imagen = imagen_files[0]
        print("[SIZE] Tamaño de imagen: {} bytes".format(imagen.size))
        
        try:
            from store.models import ProductoImagen
            
            # Eliminar la imagen anterior (orden=1) si existe
            ProductoImagen.objects.filter(producto=producto, orden=1).delete()
            print("[DELETE] Imagen anterior (orden=1) eliminada si existía")
            
            # Crear nueva ProductoImagen con orden=1 (imagen principal)
            producto_imagen = ProductoImagen(
                producto=producto,
                imagen=imagen,
                orden=1
            )
            print("[SAVE] Guardando nueva ProductoImagen para producto {}".format(producto.id))
            producto_imagen.save()
            print("[SUCCESS] Imagen guardada en: {}".format(producto_imagen.imagen.url))
            
            # Si hay más imágenes, procesarlas en orden (orden=2, 3, 4, 5)
            if len(imagen_files) > 1:
                print("[UPLOAD] Procesando {} imagen(es) adicionale(s) de galería".format(len(imagen_files) - 1))
                for idx, img_adicional in enumerate(imagen_files[1:], start=2):
                    try:
                        # Verificar que no excedamos el máximo (5 imágenes por producto)
                        existentes = ProductoImagen.objects.filter(producto=producto).count()
                        if existentes >= 5:
                            print("[SKIP] Se alcanzó máximo de 5 imágenes. Imagen {} no procesada".format(img_adicional.name))
                            break
                        
                        # Eliminar la anterior en esa posición si existe
                        ProductoImagen.objects.filter(producto=producto, orden=idx).delete()
                        
                        # Crear ProductoImagen con orden incrementado
                        producto_imagen_adicional = ProductoImagen(
                            producto=producto,
                            imagen=img_adicional,
                            orden=idx
                        )
                        producto_imagen_adicional.save()
                        print("[SUCCESS] Imagen adicional guardada en orden {} en: {}".format(idx, producto_imagen_adicional.imagen.url))
                    except Exception as e:
                        print("[ERROR] Error al procesar imagen adicional {}: {}".format(img_adicional.name, str(e)))
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            import traceback
            print("[ERROR] Error al guardar imagen principal: {}".format(str(e)))
            traceback.print_exc()
    else:
        print("[INFO] No hay imágenes en request.FILES")

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
        )

    # Eliminar imágenes marcadas para eliminación
    imagenes_a_eliminar = request.POST.get('imagenes_a_eliminar', '')
    if imagenes_a_eliminar:
        try:
            import json
            # imagenes_a_eliminar viene como JSON serializado desde el frontend
            ids_a_eliminar = json.loads(imagenes_a_eliminar)
            if not isinstance(ids_a_eliminar, list):
                ids_a_eliminar = []
        except (json.JSONDecodeError, ValueError):
            # Si no es JSON válido, intentar parsear como lista separada por comas
            ids_a_eliminar = [int(id_str) for id_str in imagenes_a_eliminar.split(',') if id_str.strip().isdigit()]
        
        if ids_a_eliminar:
            from store.models import ProductoImagen
            
            # IMPORTANTE: Eliminar una por una para que se dispare el método delete() del modelo
            # Esto es necesario para que funcione el sincronismo con VarianteImagen
            imagenes_a_borrar = ProductoImagen.objects.filter(id__in=ids_a_eliminar, producto=producto)
            for img in imagenes_a_borrar:
                # El método delete() del modelo se encarga del sincronismo con variantes
                img.delete()

    # 🖼️ PROCESAR IMÁGENES DE GALERÍA (máximo 5)
    # El frontend envía múltiples imágenes con el campo 'imagen_galeria_upload'
    try:
        from store.models import ProductoImagen
        import os
        
        # Obtener TODAS las imágenes (usar getlist para campos múltiples)
        imagenes_galeria = request.FILES.getlist('imagen_galeria_upload')
        
        if imagenes_galeria:
            print(f"[IMAGES] Total de imágenes recibidas para update: {len(imagenes_galeria)}")
            
            # Obtener el máximo orden actual
            max_orden = ProductoImagen.objects.filter(producto=producto).aggregate(
                max=models.Max('orden')
            )['max'] or 0
            
            for idx, imagen_file in enumerate(imagenes_galeria, start=1):
                if (max_orden + idx) > 5:  # Máximo 5 imágenes por producto
                    print(f"[SKIP] Se alcanzó máximo de 5 imágenes")
                    break
                
                try:
                    print(f"[PROCESSING] Procesando imagen {idx}: {imagen_file.name}, tamaño: {imagen_file.size} bytes")
                    
                    # Generar nombre del archivo: imagen-{numero}.{ext}
                    ext = os.path.splitext(imagen_file.name)[1]
                    numero_imagen = max_orden + idx  # Continuar desde el último orden
                    nombre_canonico = f'imagen-{numero_imagen}{ext}'
                    imagen_file.name = nombre_canonico
                    
                    print(f"[NAMING] Nombre canónico: {nombre_canonico}, orden: {numero_imagen}")
                    
                    # Crear instancia
                    producto_imagen = ProductoImagen(
                        producto=producto,
                        imagen=imagen_file,
                        orden=numero_imagen
                    )
                    
                    # Guardar
                    producto_imagen.save()
                    print(f"[SUCCESS] Imagen guardada en orden {numero_imagen} en: {producto_imagen.imagen.url}")
                    
                except Exception as e:
                    print(f"[ERROR] Error al procesar imagen {idx}: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"[INFO] No hay imágenes en request.FILES.getlist('imagen_galeria_upload')")
            
    except Exception as e:
        print(f"[ERROR] Error general al procesar imágenes: {e}")
        import traceback
        traceback.print_exc()

    # ─────── PROCESAR IMÁGENES DE VARIANTES ───────
    from store.models import VarianteImagen
    
    # Eliminar imágenes de variantes marcadas para eliminación
    variante_imagenes_a_eliminar = request.POST.get('variante_imagenes_a_eliminar', '')
    if variante_imagenes_a_eliminar:
        try:
            import json
            # variante_imagenes_a_eliminar viene como JSON serializado desde el frontend
            ids_a_eliminar = json.loads(variante_imagenes_a_eliminar)
            if not isinstance(ids_a_eliminar, list):
                ids_a_eliminar = []
        except (json.JSONDecodeError, ValueError):
            # Si no es JSON válido, intentar parsear como lista separada por comas
            ids_a_eliminar = [int(id_str) for id_str in variante_imagenes_a_eliminar.split(',') if id_str.strip().isdigit()]
        
        if ids_a_eliminar:
            # IMPORTANTE: Eliminar una por una para que se dispare el método delete() del modelo
            # Esto es necesario para que funcione el sincronismo con ProductoImagen
            imagenes_a_borrar = VarianteImagen.objects.filter(id__in=ids_a_eliminar)
            for img in imagenes_a_borrar:
                # El método delete() del modelo se encarga del sincronismo con producto
                img.delete()
    
    # Procesar nuevas imágenes de variantes
    for key in request.FILES:
        if key.startswith('variante_imagen_'):
            try:
                # Formato: variante_imagen_{variante_id}_{idx}
                parts = key.split('_')
                if len(parts) >= 4:
                    variante_id = int(parts[2])
                    variante = producto.variantes.get(id=variante_id)
                    imagen_file = request.FILES[key]
                    
                    # Contar imágenes existentes de esta variante
                    existing_count = variante.imagenes.count()
                    if existing_count >= 5:
                        continue
                    
                    # Generar nombre canonico
                    import os
                    ext = os.path.splitext(imagen_file.name)[1]
                    numero_imagen = existing_count + 1
                    nombre_canonico = f'imagen-{numero_imagen}{ext}'
                    imagen_file.name = nombre_canonico
                    
                    # Crear instancia
                    variante_imagen = VarianteImagen(
                        variante=variante,
                        imagen=imagen_file,
                        orden=numero_imagen
                    )
                    variante_imagen.save()
            except Exception as e:
                print(f"Error al guardar imagen de variante: {e}")

    return JsonResponse(
        {'mensaje': f'Producto {producto.id} actualizado correctamente'},
        status=200
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