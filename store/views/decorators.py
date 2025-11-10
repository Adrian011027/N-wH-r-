# store/views/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from ..models import Usuario
import jwt
from django.conf import settings


# ───────────────────────────────────────────────
# Sesión clásica (Django Session)
# ───────────────────────────────────────────────
def login_required_client(view_func):
    """
    Asegura que haya un cliente logueado en sesión.
    Si no, redirige al home público.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("cliente_id"):
            return redirect("index")
        return view_func(request, *args, **kwargs)
    return _wrapped


def login_required_user(view_func):
    """
    Asegura que haya un usuario admin logueado en sesión.
    Si no existe sesión o el rol no es 'admin', redirige al login de dashboard.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login_user")

        try:
            user = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            return redirect("login_user")

        if user.role != "admin":
            return redirect("login_user")

        return view_func(request, *args, **kwargs)
    return _wrapped


# ───────────────────────────────────────────────
# Nuevo: JWT para APIs (React / React Native)
# ───────────────────────────────────────────────
def jwt_role_required(allowed_roles=None):
    """
    Decorador para proteger rutas con JWT y validar roles
    
    Args:
        allowed_roles: Lista de roles permitidos. Si es None, permite todos los roles autenticados.
                      Ejemplo: ['admin'], ['admin', 'user']
    
    Uso:
        @jwt_role_required()  # Solo requiere autenticación
        @jwt_role_required(['admin'])  # Solo admin
        @jwt_role_required(['admin', 'user'])  # Admin o user
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return JsonResponse({
                    'error': 'Token de autenticación requerido',
                    'detail': 'Debe incluir el header: Authorization: Bearer <token>'
                }, status=401)
            
            try:
                # Extraer token del header "Bearer <token>"
                parts = auth_header.split(' ')
                if len(parts) != 2 or parts[0].lower() != 'bearer':
                    return JsonResponse({
                        'error': 'Formato de token inválido',
                        'detail': 'Use: Authorization: Bearer <token>'
                    }, status=401)
                
                token = parts[1]
                SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', 'tu-clave-secura-cambiar-en-produccion')
                
                # Decodificar token
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                
                # Verificar que sea un access token
                if payload.get('type') != 'access':
                    return JsonResponse({
                        'error': 'Tipo de token inválido',
                        'detail': 'Debe usar un access token'
                    }, status=401)
                
                # Verificar que el usuario existe
                try:
                    user = Usuario.objects.get(id=payload['user_id'])
                except Usuario.DoesNotExist:
                    return JsonResponse({
                        'error': 'Usuario no encontrado',
                        'detail': 'El usuario del token no existe'
                    }, status=404)
                
                # Agregar información del usuario al request
                request.user_id = payload['user_id']
                request.user_role = payload['role']
                request.username = payload['username']
                request.jwt_user = user
                
                # Verificar roles si se especificaron
                if allowed_roles and request.user_role not in allowed_roles:
                    return JsonResponse({
                        'error': 'Permisos insuficientes',
                        'detail': f'Se requiere uno de los siguientes roles: {", ".join(allowed_roles)}',
                        'your_role': request.user_role
                    }, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return JsonResponse({
                    'error': 'Token expirado',
                    'detail': 'Por favor, renueva tu token o inicia sesión nuevamente'
                }, status=401)
            except jwt.InvalidTokenError as e:
                return JsonResponse({
                    'error': 'Token inválido',
                    'detail': str(e)
                }, status=401)
            except Exception as e:
                return JsonResponse({
                    'error': 'Error de autenticación',
                    'detail': str(e)
                }, status=401)
        
        return wrapped_view
    return decorator


def admin_required():
    """Decorador específico para rutas solo de administradores"""
    return jwt_role_required(['admin'])

