from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Cliente, ContactoCliente
from .decorators import login_required_user, login_required_client, jwt_role_required
from django.db.models import Prefetch
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password 
import json, re
from django.views.decorators.csrf import csrf_exempt

# Regex simple y seguro para validar correos
EMAIL_REGEX = r"(^[^@\s]+@[^@\s]+\.[^@\s]+$)"

# ========= GET ALL CLIENTS ========= #
#@jwt_role_required()
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
@require_http_methods(["POST"])
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