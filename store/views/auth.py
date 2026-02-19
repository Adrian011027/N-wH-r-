from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from ..models import Usuario, Cliente
import json
import logging
import jwt
from django.conf import settings
from store.utils.jwt_helpers import generate_access_token, generate_refresh_token, _get_jwt_secret
from store.utils.security import login_limiter, get_client_ip, rate_limit

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit(login_limiter)
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

        # Generar tokens usando jwt_helpers
        access_token = generate_access_token(user.id, user.role, user.username)
        refresh_token = generate_refresh_token(user.id, role=user.role)

        return JsonResponse({
            'access': access_token,
            'refresh': refresh_token,
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
        logger.error(f'Error en login: {e}', exc_info=True)
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request):
    """Renovar access token usando refresh token (soporta Usuario y Cliente)"""
    from ..models import BlacklistedToken
    
    try:
        data = json.loads(request.body)
        # Soportar tanto 'refresh' como 'refresh_token' para compatibilidad
        refresh_token_str = data.get("refresh") or data.get("refresh_token")

        if not refresh_token_str:
            return JsonResponse({'error': 'Refresh token requerido'}, status=400)
        
        # SEGURIDAD: Verificar si el token está en la blacklist
        if BlacklistedToken.objects.filter(token=refresh_token_str).exists():
            return JsonResponse({
                'error': 'Token inválido',
                'detail': 'Este token ha sido revocado. Por favor, inicia sesión nuevamente.'
            }, status=401)

        # Verificar refresh token usando JWT_SECRET_KEY
        payload = jwt.decode(refresh_token_str, _get_jwt_secret(), algorithms=['HS256'])
        
        # Verificar que sea un refresh token
        if payload.get('type') != 'refresh':
            return JsonResponse({'error': 'Token inválido'}, status=401)
        
        user_id = payload['user_id']
        
        # Intentar obtener el role del payload o asumir según la tabla
        role = payload.get('role', 'cliente')
        username = payload.get('username', '')
        
        # Verificar que el usuario o cliente existe
        if role == 'cliente':
            from ..models import Cliente
            try:
                user = Cliente.objects.get(id=user_id)
                username = user.username
            except Cliente.DoesNotExist:
                return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
        else:
            try:
                user = Usuario.objects.get(id=user_id)
                role = user.role
                username = user.username
            except Usuario.DoesNotExist:
                return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        # Generar nuevo access token usando jwt_helpers
        from store.utils.jwt_helpers import generate_access_token
        access_token = generate_access_token(user_id, role, username)

        return JsonResponse({
            'access': access_token,
            'message': 'Token renovado exitosamente'
        }, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Refresh token expirado. Por favor, inicia sesión nuevamente'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Refresh token inválido'}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.exception(f'Error en refresh_token: {e}')
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    """Cerrar sesión - invalidar refresh token en blacklist"""
    try:
        data = json.loads(request.body or "{}")
        refresh = data.get("refresh")

        if refresh:
            from ..models import BlacklistedToken
            # Decodificar para verificar que es válido antes de añadir a blacklist
            try:
                payload = jwt.decode(refresh, _get_jwt_secret(), algorithms=["HS256"])
                if payload.get("type") == "refresh":
                    BlacklistedToken.objects.create(token=refresh)
            except jwt.InvalidTokenError:
                pass  # Token inválido, no hace falta añadir a blacklist
        
        return JsonResponse({
            'message': 'Sesión cerrada exitosamente.'
        }, status=200)
    except Exception as e:
        logger.exception(f'Error en logout: {e}')
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_token(request):
    """Verificar si un token es válido (soporta Usuario y Cliente)"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return JsonResponse({'valid': False, 'error': 'Token no proporcionado'}, status=401)
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=['HS256'])
        
        if payload.get('type') != 'access':
            return JsonResponse({'valid': False, 'error': 'Token inválido'}, status=401)
        
        user_id = payload['user_id']
        role = payload.get('role', 'cliente')
        
        # Verificar según el role
        if role == 'cliente':
            user = Cliente.objects.get(id=user_id)
        else:
            user = Usuario.objects.get(id=user_id)
        
        return JsonResponse({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username if hasattr(user, 'username') else user.nombre,
                'role': role
            }
        }, status=200)
        
    except jwt.ExpiredSignatureError:
        return JsonResponse({'valid': False, 'error': 'Token expirado'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'valid': False, 'error': 'Token inválido'}, status=401)
    except (Usuario.DoesNotExist, Cliente.DoesNotExist):
        return JsonResponse({'valid': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        logger.exception(f'Error en verify_token: {e}')
        return JsonResponse({'valid': False, 'error': 'Error interno del servidor'}, status=500)
