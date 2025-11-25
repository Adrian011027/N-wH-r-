from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Cliente, ContactoCliente
from .decorators import login_required_user, login_required_client, jwt_role_required, admin_required, auth_required_hybrid
from django.db.models import Prefetch
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password 
import json, re
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

# Regex simple y seguro para validar correos
EMAIL_REGEX = r"(^[^@\s]+@[^@\s]+\.[^@\s]+$)"

# ========= EDITAR PERFIL (VISTA) ========= #
@auth_required_hybrid()
def editar_perfil(request, id):
    """Vista para editar el perfil del cliente"""
    cliente = get_object_or_404(Cliente, id=id)
    
    if request.method == 'GET':
        return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
    
    elif request.method == 'POST':
        try:
            # Información personal
            cliente.nombre = request.POST.get('nombre', '').strip()
            correo = request.POST.get('correo', '').strip().lower()
            
            # Validar correo
            if correo != cliente.correo:
                if not re.match(EMAIL_REGEX, correo):
                    messages.error(request, 'Correo electrónico inválido')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
                if Cliente.objects.filter(correo=correo).exclude(id=id).exists():
                    messages.error(request, 'Este correo ya está registrado')
                    return render(request, 'public/cliente/perfil.html', {'cliente': cliente})
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

    cliente = get_object_or_404(Cliente, id=id)
    return JsonResponse({
        'id': cliente.id,
        'username': cliente.username,
        'nombre': cliente.nombre,
        'email': cliente.correo,
        'telefono': cliente.telefono,
        'direccion': cliente.direccion
    })

# ========= CREATE CLIENT ========= #
@csrf_exempt
@require_http_methods(["POST"])
def create_client(request):
    try:
        data = json.loads(request.body)
        username  = data.get('username', '').strip().lower()
        password  = data.get('password')
        correo    = data.get('correo', '').strip().lower()
        nombre    = data.get('nombre', '').strip()
        telefono  = data.get('telefono', '').strip()
        direccion = data.get('direccion', '').strip()

        if not username or not password or not correo:
            return JsonResponse({'error': 'Username, password y correo son obligatorios'}, status=400)

        if not re.match(EMAIL_REGEX, correo):
            return JsonResponse({'error': 'Correo inválido'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'La contraseña debe tener al menos 8 caracteres'}, status=400)

        if Cliente.objects.filter(username=username).exists():
            return JsonResponse({'error': 'El nombre de usuario ya existe'}, status=409)

        if Cliente.objects.filter(correo=correo).exists():
            return JsonResponse({'error': 'El correo ya está registrado'}, status=409)

        if telefono and not telefono.isdigit():
            return JsonResponse({'error': 'El teléfono debe contener solo dígitos'}, status=400)

        cliente = Cliente.objects.create(
            username=username,
            password=make_password(password),
            correo=correo,
            nombre=nombre,
            telefono=telefono,
            direccion=direccion
        )
        return JsonResponse({'username': cliente.username, 'message': 'Cliente creado con éxito'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ========= UPDATE CLIENT ========= #
@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST", "PUT"])
def update_client(request, id):
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