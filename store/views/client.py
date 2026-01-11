from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Cliente, ContactoCliente, Orden, OrdenDetalle
from .decorators import login_required_user, login_required_client, jwt_role_required, admin_required, auth_required_hybrid
from django.db.models import Prefetch
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password 
import json, re
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

# Importar utilidades de seguridad
from ..utils.security import (
    register_limiter, 
    rate_limit, 
    get_client_ip,
    send_verification_email
)

# Regex simple y seguro para validar correos
EMAIL_REGEX = r"(^[^@\s]+@[^@\s]+\.[^@\s]+$)"


# ========= MIS PEDIDOS (VISTA HTML) ========= #
@login_required_client
def mis_pedidos(request):
    """Vista protegida para mostrar el historial de pedidos del cliente"""
    return render(request, 'public/cliente/mis_pedidos.html')


# ========= API: OBTENER ÓRDENES DEL CLIENTE ========= #
@csrf_exempt
@jwt_role_required()
@require_GET
def get_ordenes_cliente(request):
    """API para obtener las órdenes del cliente autenticado"""
    try:
        cliente_id = request.user_id
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        ordenes = Orden.objects.filter(cliente=cliente).order_by('-created_at').prefetch_related(
            'detalles__variante__producto'
        )
        
        data = []
        for orden in ordenes:
            items = []
            for detalle in orden.detalles.all():
                variante = detalle.variante
                producto = variante.producto
                
                items.append({
                    'producto_id': producto.id,
                    'producto_nombre': producto.nombre,
                    'producto_imagen': producto.imagen.url if producto.imagen else None,
                    'variante_id': variante.id,
                    'talla': variante.talla,
                    'color': variante.color,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.precio_unitario * detalle.cantidad)
                })
            
            data.append({
                'id': orden.id,
                'status': orden.status,
                'status_display': get_status_display(orden.status),
                'total_amount': float(orden.total_amount),
                'payment_method': orden.payment_method,
                'created_at': orden.created_at.strftime('%d/%m/%Y %H:%M'),
                'items': items,
                'total_items': sum(item['cantidad'] for item in items)
            })
        
        return JsonResponse({
            'success': True,
            'ordenes': data,
            'total': len(data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_status_display(status):
    """Convierte el código de estado a texto legible"""
    status_map = {
        'pendiente': {'text': 'Pendiente', 'color': '#f59e0b', 'icon': 'clock'},
        'procesando': {'text': 'Procesando', 'color': '#3b82f6', 'icon': 'settings'},
        'proces': {'text': 'Procesando', 'color': '#3b82f6', 'icon': 'settings'},
        'enviado': {'text': 'Enviado', 'color': '#8b5cf6', 'icon': 'truck'},
        'entregado': {'text': 'Entregado', 'color': '#10b981', 'icon': 'check'},
        'cancelado': {'text': 'Cancelado', 'color': '#ef4444', 'icon': 'x'},
    }
    return status_map.get(status.lower(), {'text': status.capitalize(), 'color': '#6b7280', 'icon': 'info'})


# ========= EDITAR PERFIL (VISTA) ========= #
@auth_required_hybrid()
def editar_perfil(request, id):
    """Vista para editar el perfil del cliente"""
    cliente = get_object_or_404(Cliente, id=id)
    
    # Calcular si puede cambiar username
    puede_cambiar_username = True
    dias_restantes = 0
    
    if cliente.ultima_modificacion_username:
        tiempo_transcurrido = timezone.now() - cliente.ultima_modificacion_username
        if tiempo_transcurrido < timedelta(days=30):
            puede_cambiar_username = False
            dias_restantes = 30 - tiempo_transcurrido.days
    
    if request.method == 'GET':
        return render(request, 'public/cliente/perfil.html', {
            'cliente': cliente,
            'puede_cambiar_username': puede_cambiar_username,
            'dias_restantes': dias_restantes,
            'email_verified': cliente.email_verified,
        })
    
    elif request.method == 'POST':
        try:
            # Información personal
            cliente.nombre = request.POST.get('nombre', '').strip()
            correo = request.POST.get('correo', '').strip().lower()
            
            # Validar y cambiar username
            nuevo_username = request.POST.get('username', '').strip()
            if nuevo_username and nuevo_username != cliente.username:
                # Verificar si puede cambiar
                if not puede_cambiar_username:
                    messages.error(request, f'Solo puedes cambiar tu nombre de usuario una vez al mes. Faltan {dias_restantes} días.')
                    return render(request, 'public/cliente/perfil.html', {
                        'cliente': cliente,
                        'puede_cambiar_username': puede_cambiar_username,
                        'dias_restantes': dias_restantes
                    })
                
                # Validar que no exista
                if Cliente.objects.filter(username=nuevo_username).exclude(id=id).exists():
                    messages.error(request, 'Este nombre de usuario ya está en uso')
                    return render(request, 'public/cliente/perfil.html', {
                        'cliente': cliente,
                        'puede_cambiar_username': puede_cambiar_username,
                        'dias_restantes': dias_restantes
                    })
                
                # Validar formato (alfanumérico, puntos, guiones bajos)
                if not re.match(r'^[a-zA-Z0-9._]+$', nuevo_username):
                    messages.error(request, 'El nombre de usuario solo puede contener letras, números, puntos y guiones bajos')
                    return render(request, 'public/cliente/perfil.html', {
                        'cliente': cliente,
                        'puede_cambiar_username': puede_cambiar_username,
                        'dias_restantes': dias_restantes
                    })
                
                if len(nuevo_username) < 3:
                    messages.error(request, 'El nombre de usuario debe tener al menos 3 caracteres')
                    return render(request, 'public/cliente/perfil.html', {
                        'cliente': cliente,
                        'puede_cambiar_username': puede_cambiar_username,
                        'dias_restantes': dias_restantes
                    })
                
                cliente.username = nuevo_username
                cliente.ultima_modificacion_username = timezone.now()
            
            # Validar correo
            if correo != cliente.correo:
                if not re.match(EMAIL_REGEX, correo):
                    messages.error(request, 'Correo electrónico inválido')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente, 'puede_cambiar_username': puede_cambiar_username, 'dias_restantes': dias_restantes})
                if Cliente.objects.filter(correo=correo).exclude(id=id).exists():
                    messages.error(request, 'Este correo ya está registrado')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente, 'puede_cambiar_username': puede_cambiar_username, 'dias_restantes': dias_restantes})
                cliente.correo = correo
            
            cliente.telefono = request.POST.get('telefono', '').strip()
            cliente.telefono_alternativo = request.POST.get('telefono_alternativo', '').strip()
            
            # Dirección de envío
            cliente.calle = request.POST.get('calle', '').strip()
            cliente.colonia = request.POST.get('colonia', '').strip()
            cliente.codigo_postal = request.POST.get('codigo_postal', '').strip()
            cliente.ciudad = request.POST.get('ciudad', '').strip()
            cliente.estado = request.POST.get('estado', '').strip()
            cliente.referencias = request.POST.get('referencias', '').strip()
            
            # Actualizar dirección completa (legacy)
            if cliente.calle and cliente.colonia:
                cliente.direccion = f"{cliente.calle}, {cliente.colonia}, {cliente.ciudad}, {cliente.estado}"
            
            # Información fiscal
            cliente.tipo_cliente = request.POST.get('tipo_cliente', 'menudeo')
            cliente.rfc = request.POST.get('rfc', '').strip().upper()
            cliente.razon_social = request.POST.get('razon_social', '').strip()
            cliente.direccion_fiscal = request.POST.get('direccion_fiscal', '').strip()
            
            # Cambio de contraseña
            password_actual = request.POST.get('password_actual', '')
            password_nueva = request.POST.get('password_nueva', '')
            password_confirmar = request.POST.get('password_confirmar', '')
            
            if password_actual or password_nueva or password_confirmar:
                if not password_actual:
                    messages.error(request, 'Debes ingresar tu contraseña actual')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
                
                if not check_password(password_actual, cliente.password):
                    messages.error(request, 'La contraseña actual es incorrecta')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
                
                if not password_nueva:
                    messages.error(request, 'Debes ingresar una nueva contraseña')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
                
                if len(password_nueva) < 8:
                    messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
                
                if password_nueva != password_confirmar:
                    messages.error(request, 'Las contraseñas no coinciden')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
                
                cliente.password = make_password(password_nueva)
            
            cliente.save()
            messages.success(request, '¡Perfil actualizado exitosamente!')
            return redirect('editar_perfil', id=id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
            return render(request, 'public/cliente/perfil.html', {'cliente': cliente})

# ========= GET ALL CLIENTS ========= #
@admin_required()
@require_GET
def get_all_clients(request):
    try:
        clientes = Cliente.objects.all()
        data = [{
            'id': c.id,
            'username': c.username,
            'nombre': c.nombre,
            'email': c.correo,
        } for c in clientes]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ========= GET CLIENT BY ID ========= #
@jwt_role_required()
def detalle_client(request, id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # SEGURIDAD: Solo el propio cliente o admin puede ver los datos
    if request.user_role != 'admin' and request.user_id != id:
        return JsonResponse({
            'error': 'No autorizado',
            'detail': 'Solo puedes ver tu propia información'
        }, status=403)

    cliente = get_object_or_404(Cliente, id=id)
    return JsonResponse({
        'id': cliente.id,
        'username': cliente.username,
        'nombre': cliente.nombre,
        'correo': cliente.correo,
        'telefono': cliente.telefono,
        'email_verified': cliente.email_verified,
        # Campos de dirección
        'calle': cliente.calle,
        'colonia': cliente.colonia,
        'codigo_postal': cliente.codigo_postal,
        'ciudad': cliente.ciudad,
        'estado': cliente.estado,
        'referencias': cliente.referencias,
    })

# ========= CREATE CLIENT ========= #
@csrf_exempt
@rate_limit(register_limiter)
@require_http_methods(["POST"])
def create_client(request):
    """
    Registro simplificado: solo requiere correo y contraseña.
    El username se genera automáticamente desde el correo.
    """
    try:
        data = json.loads(request.body)
        password  = data.get('password')
        correo    = data.get('correo', '').strip().lower()
        
        # Campos opcionales
        username_custom = data.get('username', '').strip().lower()
        nombre    = data.get('nombre', '').strip()
        telefono  = data.get('telefono', '').strip()
        direccion = data.get('direccion', '').strip()

        # Validaciones mínimas
        if not password or not correo:
            return JsonResponse({'error': 'Correo y contraseña son obligatorios'}, status=400)

        if not re.match(EMAIL_REGEX, correo):
            return JsonResponse({'error': 'Correo electrónico inválido'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'La contraseña debe tener al menos 8 caracteres'}, status=400)

        if Cliente.objects.filter(correo=correo).exists():
            return JsonResponse({'error': 'Este correo ya está registrado. ¿Quieres iniciar sesión?'}, status=409)

        # Generar username desde el correo si no se proporciona
        if username_custom:
            username = username_custom
        else:
            # Extraer parte antes del @ y sanitizar
            base_username = correo.split('@')[0]
            # Remover caracteres especiales, solo letras, números, puntos y guiones bajos
            base_username = re.sub(r'[^a-z0-9._]', '', base_username)
            
            # Asegurar mínimo 3 caracteres
            if len(base_username) < 3:
                base_username = base_username + 'user'
            
            # Verificar si ya existe y agregar sufijo si es necesario
            username = base_username
            counter = 1
            while Cliente.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

        # Validar longitud de username
        if len(username) < 3:
            return JsonResponse({'error': 'El nombre de usuario es demasiado corto'}, status=400)

        # Validar formato de teléfono si se proporciona
        if telefono:
            telefono_limpio = ''.join(filter(str.isdigit, telefono))
            if telefono_limpio and len(telefono_limpio) < 10:
                return JsonResponse({'error': 'El teléfono debe tener al menos 10 dígitos'}, status=400)
            telefono = telefono_limpio if telefono_limpio else None

        cliente = Cliente.objects.create(
            username=username,
            password=make_password(password),
            correo=correo,
            nombre=nombre or None,  # Guardar None si está vacío
            telefono=telefono,
            direccion=direccion or None,
            email_verified=False
        )
        
        # Enviar correo de verificación
        email_sent = send_verification_email(cliente, request)
        
        # Registrar intento exitoso
        ip = get_client_ip(request)
        register_limiter.record_attempt(f"ip:{ip}", success=True)
        
        return JsonResponse({
            'username': cliente.username,
            'correo': cliente.correo,
            'message': '¡Cuenta creada! Revisa tu correo para verificar tu cuenta.',
            'email_verification_sent': email_sent,
            'requires_verification': True
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato de datos inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Error al crear la cuenta. Intenta de nuevo.'}, status=500)

# ========= UPDATE CLIENT ========= #
@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST", "PUT"])
def update_client(request, id):
    # SEGURIDAD: Solo el propio cliente o admin puede modificar
    if request.user_role != 'admin' and request.user_id != id:
        return JsonResponse({
            'error': 'No autorizado',
            'detail': 'Solo puedes modificar tu propia información'
        }, status=403)
    
    try:
        cliente = Cliente.objects.get(id=id)
        data = json.loads(request.body)

        username  = data.get('username', '').strip().lower()
        password  = data.get('password')
        correo    = data.get('correo', '').strip().lower()
        nombre    = data.get('nombre', '').strip()
        telefono  = data.get('telefono', '').strip()
        direccion = data.get('direccion', '').strip()

        if username and username != cliente.username:
            if Cliente.objects.filter(username=username).exists():
                return JsonResponse({'error': 'El nuevo nombre de usuario ya está en uso'}, status=409)
            cliente.username = username

        if correo and correo != cliente.correo:
            if not re.match(EMAIL_REGEX, correo):
                return JsonResponse({'error': 'Correo inválido'}, status=400)
            if Cliente.objects.filter(correo=correo).exists():
                return JsonResponse({'error': 'El nuevo correo ya está registrado'}, status=409)
            cliente.correo = correo

        if password:
            if len(password) < 8:
                return JsonResponse({'error': 'La nueva contraseña debe tener al menos 8 caracteres'}, status=400)
            cliente.password = make_password(password)

        if nombre:
            cliente.nombre = nombre

        if telefono:
            if not telefono.isdigit():
                return JsonResponse({'error': 'El teléfono debe contener solo dígitos'}, status=400)
            cliente.telefono = telefono

        if direccion:
            cliente.direccion = direccion

        cliente.save()
        return JsonResponse({'message': f'Cliente {id} actualizado correctamente'}, status=200)

    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as err:
        return JsonResponse({'error': str(err)}, status=500)

# ========= DELETE CLIENT ========= #
@csrf_exempt
@admin_required()
@require_http_methods(["POST", "DELETE"])
def delete_client(request, id):
    try:
        cliente = Cliente.objects.get(id=id)
        nombre = cliente.nombre
        cliente.delete()

        if request.method == "POST":
            return redirect('dashboard_clientes')

        return JsonResponse({'message': f'Cliente {nombre} eliminado correctamente'}, status=200)

    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ========= SEND CONTACT ========= #
@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST"])
def send_contact(request, id):
    # SEGURIDAD: Solo el propio cliente puede enviar contactos desde su cuenta
    if request.user_role != 'admin' and request.user_id != id:
        return JsonResponse({
            'error': 'No autorizado',
            'detail': 'Solo puedes enviar contactos desde tu propia cuenta'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        cliente = Cliente.objects.get(id=id)
        email   = data.get('email', '').strip()
        mensaje = data.get('mensaje', '').strip()

        if not email or not mensaje:
            return JsonResponse({'error': 'Email y mensaje son obligatorios'}, status=400)
        if not re.match(EMAIL_REGEX, email):
            return JsonResponse({'error': 'Correo inválido'}, status=400)

        contacto = ContactoCliente.objects.create(
            cliente=cliente,
            email=email,
            mensaje=mensaje
        )
        return JsonResponse({'message': 'Mensaje enviado con éxito'}, status=201)

    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========= API CONTACTO (Panel Cliente) ========= #
@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST"])
def api_contacto(request):
    """
    Endpoint para enviar mensaje de contacto desde el panel del cliente.
    Usa el user_id del JWT para identificar al cliente.
    """
    try:
        data = json.loads(request.body)
        asunto = data.get('asunto', '').strip()
        mensaje = data.get('mensaje', '').strip()

        if not asunto or not mensaje:
            return JsonResponse({'error': 'Asunto y mensaje son obligatorios'}, status=400)

        # Obtener cliente del JWT
        cliente = Cliente.objects.get(id=request.user_id)
        
        # Crear registro de contacto (usando email del cliente)
        # Como ContactoCliente es OneToOne, usamos update_or_create
        ContactoCliente.objects.update_or_create(
            cliente=cliente,
            defaults={
                'nombre': cliente.nombre or cliente.username,
                'email': cliente.correo,
                'mensaje': f"[{asunto.upper()}] {mensaje}"
            }
        )
        
        return JsonResponse({
            'message': 'Mensaje enviado con éxito',
            'detail': 'Te responderemos a tu correo lo antes posible'
        }, status=201)

    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)