# store/views/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from ..models import Usuario, Cliente
import jwt
from django.conf import settings
from store.utils.jwt_helpers import _get_jwt_secret
import logging

logger = logging.getLogger(__name__)


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
    Asegura que haya un usuario admin logueado en sesión DEL DASHBOARD.
    Si no existe sesión o el rol no es 'admin', redirige al login de dashboard.
    Usa claves de sesión específicas del dashboard (independientes del inventario).
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_id = request.session.get("dashboard_user_id")
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
                # Usar la misma clave JWT centralizada
                jwt_secret = _get_jwt_secret()
                
                # Decodificar token
                payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
                
                # Verificar que sea un access token
                if payload.get('type') != 'access':
                    return JsonResponse({
                        'error': 'Tipo de token inválido',
                        'detail': 'Debe usar un access token'
                    }, status=401)
                
                # Verificar que el usuario o cliente existe según el role
                user_role = payload.get('role', 'cliente')
                user_id = payload['user_id']
                
                if user_role == 'cliente':
                    try:
                        user = Cliente.objects.get(id=user_id)
                        request.jwt_cliente = user
                    except Cliente.DoesNotExist:
                        return JsonResponse({
                            'error': 'Cliente no encontrado',
                            'detail': 'El cliente del token no existe'
                        }, status=404)
                else:
                    try:
                        user = Usuario.objects.get(id=user_id)
                        request.jwt_user = user
                    except Usuario.DoesNotExist:
                        return JsonResponse({
                            'error': 'Usuario no encontrado',
                            'detail': 'El usuario del token no existe'
                        }, status=404)
                
                # Agregar información del usuario al request
                request.user_id = user_id
                request.user_role = user_role
                request.username = payload.get('username', '')
                
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
                    'detail': 'El token proporcionado no es válido'
                }, status=401)
            except Exception as e:
                return JsonResponse({
                    'error': 'Error de autenticación',
                    'detail': 'No se pudo verificar la autenticación'
                }, status=401)
        
        return wrapped_view
    return decorator


def admin_required():
    """Decorador específico para rutas solo de administradores"""
    return jwt_role_required(['admin'])


def admin_required_hybrid():
    """
    Decorador híbrido para APIs de admin que acepta:
    1. JWT en header Authorization
    2. Sesión Django (para el dashboard)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            # Intento 1: JWT
            if auth_header:
                try:
                    parts = auth_header.split(' ')
                    if len(parts) == 2 and parts[0].lower() == 'bearer':
                        token = parts[1]
                        payload = jwt.decode(token, _get_jwt_secret(), algorithms=['HS256'])
                        
                        if payload.get('type') != 'access':
                            return JsonResponse({'error': 'Tipo de token inválido'}, status=401)
                        
                        user_role = payload.get('role', 'cliente')
                        if user_role != 'admin':
                            return JsonResponse({'error': 'Solo administradores'}, status=403)
                        
                        user_id = payload['user_id']
                        try:
                            user = Usuario.objects.get(id=user_id)
                            request.jwt_user = user
                        except Usuario.DoesNotExist:
                            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
                        
                        request.user_id = user_id
                        request.user_role = user_role
                        request.username = payload.get('username', '')
                        
                        return view_func(request, *args, **kwargs)
                        
                except jwt.ExpiredSignatureError:
                    return JsonResponse({'error': 'Token expirado'}, status=401)
                except jwt.InvalidTokenError as e:
                    return JsonResponse({'error': 'Token inválido', 'detail': 'El token proporcionado no es válido'}, status=401)
            
            # Intento 2: Sesión Django del DASHBOARD
            user_id = request.session.get("dashboard_user_id")
            if user_id:
                try:
                    user = Usuario.objects.get(id=user_id)
                    if user.role == 'admin':
                        request.user_id = user_id
                        request.user_role = 'admin'
                        request.username = user.username
                        request.jwt_user = user
                        return view_func(request, *args, **kwargs)
                except Usuario.DoesNotExist:
                    pass
            
            # No autenticado
            return JsonResponse({
                'error': 'Autenticación requerida',
                'detail': 'Inicie sesión como administrador'
            }, status=401)
        
        return wrapped_view
    return decorator


def inventory_manager_required():
    """
    Decorador híbrido para APIs de gestión de inventario que acepta:
    1. JWT en header Authorization con roles 'admin' o 'inventario'
    2. Sesión Django con roles 'admin' o 'inventario'
    
    Usado por el módulo de inventario para permitir editar productos/variantes.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            # Intento 1: JWT
            if auth_header:
                try:
                    parts = auth_header.split(' ')
                    if len(parts) == 2 and parts[0].lower() == 'bearer':
                        token = parts[1]
                        payload = jwt.decode(token, _get_jwt_secret(), algorithms=['HS256'])
                        
                        if payload.get('type') != 'access':
                            return JsonResponse({'error': 'Tipo de token inválido'}, status=401)
                        
                        user_role = payload.get('role', 'cliente')
                        # Permitir 'admin' o 'inventario'
                        if user_role not in ['admin', 'inventario']:
                            return JsonResponse({'error': 'Se requiere rol de administrador o inventario'}, status=403)
                        
                        user_id = payload['user_id']
                        try:
                            user = Usuario.objects.get(id=user_id)
                            request.jwt_user = user
                        except Usuario.DoesNotExist:
                            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
                        except Exception as db_err:
                            # Manejo de errores de BD (timeout, conexión perdida, etc.)
                            logger.error(f"Error de BD al verificar usuario en inventory_manager: {db_err}")
                            return JsonResponse({
                                'error': 'Error de conexión a la base de datos',
                                'detail': 'Por favor, intente nuevamente'
                            }, status=503)
                        
                        request.user_id = user_id
                        request.user_role = user_role
                        request.username = payload.get('username', '')
                        
                        return view_func(request, *args, **kwargs)
                        
                except jwt.ExpiredSignatureError:
                    return JsonResponse({'error': 'Token expirado'}, status=401)
                except jwt.InvalidTokenError as e:
                    return JsonResponse({'error': 'Token inválido', 'detail': 'El token proporcionado no es válido'}, status=401)
            
            # Intento 2: Sesión Django del INVENTARIO
            user_id = request.session.get("inventario_user_id")
            if user_id:
                try:
                    user = Usuario.objects.get(id=user_id)
                    if user.role in ['admin', 'inventario']:
                        request.user_id = user_id
                        request.user_role = user.role
                        request.username = user.username
                        request.jwt_user = user
                        return view_func(request, *args, **kwargs)
                except Usuario.DoesNotExist:
                    pass
                except Exception as db_err:
                    logger.error(f"Error de BD al verificar sesión en inventory_manager: {db_err}")
                    return JsonResponse({
                        'error': 'Error de conexión a la base de datos',
                        'detail': 'Por favor, intente nuevamente'
                    }, status=503)
            
            # No autenticado
            return JsonResponse({
                'error': 'Autenticación requerida',
                'detail': 'Inicie sesión como administrador o gestor de inventario'
            }, status=401)
        
        return wrapped_view
    return decorator


# ───────────────────────────────────────────────
# Decorador híbrido: JWT o Cookie
# ───────────────────────────────────────────────
def auth_required_hybrid(allowed_roles=None):
    """
    Decorador que acepta tanto JWT (API) como cookies de sesión (vistas HTML).
    Útil para vistas que pueden ser accedidas desde el navegador o desde APIs.
    
    Args:
        allowed_roles: Lista de roles permitidos. Si es None, permite todos los roles autenticados.
    
    Intenta primero JWT, si no hay token intenta cookie de sesión.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            # Intento 1: Autenticación JWT
            if auth_header:
                try:
                    parts = auth_header.split(' ')
                    if len(parts) == 2 and parts[0].lower() == 'bearer':
                        token = parts[1]
                        payload = jwt.decode(token, _get_jwt_secret(), algorithms=['HS256'])
                        
                        if payload.get('type') != 'access':
                            return JsonResponse({'error': 'Tipo de token inválido'}, status=401)
                        
                        user_role = payload.get('role', 'cliente')
                        user_id = payload['user_id']
                        
                        if user_role == 'cliente':
                            try:
                                user = Cliente.objects.get(id=user_id)
                                request.cliente = user
                                request.jwt_cliente = user
                            except Cliente.DoesNotExist:
                                return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
                        else:
                            try:
                                user = Usuario.objects.get(id=user_id)
                                request.usuario = user
                                request.jwt_user = user
                            except Usuario.DoesNotExist:
                                return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
                        
                        request.user_id = user_id
                        request.user_role = user_role
                        request.username = payload.get('username', '')
                        
                        if allowed_roles and request.user_role not in allowed_roles:
                            return JsonResponse({
                                'error': 'Permisos insuficientes',
                                'detail': f'Se requiere uno de los siguientes roles: {", ".join(allowed_roles)}'
                            }, status=403)
                        
                        # SEGURIDAD: Verificar autorización horizontal (JWT)
                        # El cliente solo puede acceder a su propio recurso
                        if user_role == 'cliente':
                            url_id = kwargs.get('id')
                            if url_id and int(url_id) != user_id:
                                return JsonResponse({'error': 'No autorizado'}, status=403)
                        
                        return view_func(request, *args, **kwargs)
                        
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                    pass  # Intentar con cookie si JWT falla
            
            # Intento 2: Autenticación por Cookie de sesión Django
            cliente_id_session = request.session.get('cliente_id')
            cliente_id_url = kwargs.get('id')  # El ID viene en la URL
            
            # Verificar que hay una sesión activa
            if cliente_id_session:
                try:
                    cliente = Cliente.objects.get(id=cliente_id_session)
                    
                    # SEGURIDAD: Verificar que el cliente solo acceda a SU perfil
                    if cliente_id_url and int(cliente_id_url) != cliente_id_session:
                        # Está intentando ver el perfil de otro usuario
                        if request.content_type == 'application/json' or auth_header:
                            return JsonResponse({
                                'error': 'Acceso denegado',
                                'detail': 'No tienes permiso para ver este perfil'
                            }, status=403)
                        else:
                            return redirect('index')
                    
                    request.cliente = cliente
                    request.user_id = cliente.id
                    request.user_role = 'cliente'
                    request.username = cliente.username
                    
                    if allowed_roles and 'cliente' not in allowed_roles:
                        return redirect('index')
                    
                    return view_func(request, *args, **kwargs)
                except Cliente.DoesNotExist:
                    # Sesión inválida, limpiar
                    request.session.flush()
                    return redirect('index')
            
            # Si llegamos aquí, no hay autenticación válida
            # Si es una petición JSON, devolver JSON
            if request.content_type == 'application/json' or auth_header:
                return JsonResponse({
                    'error': 'Autenticación requerida',
                    'detail': 'Debe iniciar sesión para acceder a esta página'
                }, status=401)
            else:
                # Si es navegador, redirigir al home
                return redirect('index')
        
        return wrapped_view
    return decorator

