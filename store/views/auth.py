from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from ..models import Usuario
import json
import jwt
from datetime import datetime, timedelta
from django.conf import settings

# Clave secreta para JWT (agrégala en settings.py)
SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', 'tu-clave-secreta-segura-cambiar-en-produccion')


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """Autenticación de usuario y generación de tokens JWT"""
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return JsonResponse({'error': 'Username y password son requeridos'}, status=400)

        # Buscar usuario
        try:
            user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            return JsonResponse({'error': 'Credenciales inválidas'}, status=401)

        # Verificar contraseña
        if not check_password(password, user.password):
            return JsonResponse({'error': 'Credenciales inválidas'}, status=401)

        # Generar tokens
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        return JsonResponse({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            },
            'message': 'Login exitoso'
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request):
    """Renovar access token usando refresh token"""
    try:
        data = json.loads(request.body)
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return JsonResponse({'error': 'Refresh token requerido'}, status=400)

        # Verificar refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        
        # Verificar que sea un refresh token
        if payload.get('type') != 'refresh':
            return JsonResponse({'error': 'Token inválido'}, status=401)
        
        user = Usuario.objects.get(id=payload['user_id'])
        access_token = generate_access_token(user)

        return JsonResponse({
            'access_token': access_token,
            'message': 'Token renovado exitosamente'
        }, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Refresh token expirado. Por favor, inicia sesión nuevamente'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Refresh token inválido'}, status=401)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    """Cerrar sesión (el frontend debe eliminar los tokens)"""
    return JsonResponse({
        'message': 'Sesión cerrada exitosamente. Por favor elimina los tokens del cliente.'
    }, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def verify_token(request):
    """Verificar si un token es válido"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return JsonResponse({'valid': False, 'error': 'Token no proporcionado'}, status=401)
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        if payload.get('type') != 'access':
            return JsonResponse({'valid': False, 'error': 'Token inválido'}, status=401)
        
        user = Usuario.objects.get(id=payload['user_id'])
        
        return JsonResponse({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }, status=200)
        
    except jwt.ExpiredSignatureError:
        return JsonResponse({'valid': False, 'error': 'Token expirado'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'valid': False, 'error': 'Token inválido'}, status=401)
    except Usuario.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)}, status=500)


def generate_access_token(user):
    """Generar access token con expiración de 1 hora"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def generate_refresh_token(user):
    """Generar refresh token con expiración de 7 días"""
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
