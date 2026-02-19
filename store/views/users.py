from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Usuario
from .decorators import jwt_role_required, admin_required
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
import logging

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# Obtener todos los usuarios (solo admin)
# ───────────────────────────────────────────────
@admin_required()
@require_GET
def get_user(request):
    """Obtener lista de todos los usuarios - Solo administradores"""
    try:
        usuarios = Usuario.objects.all()
        
        # Implementar búsqueda segura (usando ORM parametrizado)
        search = request.GET.get('search', '').strip()
        if search:
            # Django ORM parametriza automáticamente - SEGURO contra SQL injection
            usuarios = usuarios.filter(
                Q(username__icontains=search) | 
                Q(role__icontains=search)
            )
        
        # SEGURIDAD: NUNCA exponer hash de contraseña, ni siquiera a admins
        data = [{
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "created_at": u.date_joined.isoformat() if hasattr(u, 'date_joined') and u.date_joined else None
        } for u in usuarios]
        
        return JsonResponse({
            'usuarios': data,
            'total': len(data)
        }, safe=False)
    except Exception as e:
        logger.exception(f'Error en get_user: {e}')
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


# ───────────────────────────────────────────────
# Crear usuario (solo admin)
# ───────────────────────────────────────────────
@csrf_exempt
@admin_required()
@require_http_methods(["POST"])
def create_user(request):
    """Crear un nuevo usuario - Solo administradores"""
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")

        if not username or not password or not role:
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)

        # Verificar si el usuario ya existe
        if Usuario.objects.filter(username=username).exists():
            return JsonResponse({'error': 'El usuario ya existe'}, status=400)

        user = Usuario.objects.create(
            username=username,
            password=make_password(password),
            role=role
        )
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'message': 'Usuario creado con éxito'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.exception(f'Error en create_user: {e}')
        return JsonResponse({'error': 'Error al crear usuario'}, status=500)
# ───────────────────────────────────────────────
@csrf_exempt
@admin_required()
@require_http_methods(["POST", "PUT"])
def update_user(request, id):
    """Actualizar usuario - Solo administradores"""
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")

        user = Usuario.objects.get(id=id)
        
        if username:
            user.username = username
        if password:
            user.password = make_password(password)
        if role:
            user.role = role
            
        user.save()

        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'mensaje': f'Usuario {id} actualizado correctamente'
        }, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as err:
        logger.exception(f'Error en update_user: {err}')
        return JsonResponse({'error': 'Error al actualizar usuario'}, status=500)


# ───────────────────────────────────────────────
# Eliminar usuario (solo admin)
# ───────────────────────────────────────────────
@csrf_exempt
@admin_required()
@require_http_methods(["DELETE"])
def delete_user(request, id):
    """Eliminar usuario - Solo administradores"""
    try:
        usuario = Usuario.objects.get(id=id)
        username = usuario.username
        usuario.delete()
        return JsonResponse({'mensaje': f'Usuario {username} eliminado correctamente'}, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        logger.exception(f'Error en delete_user: {e}')
        return JsonResponse({'error': 'Error al eliminar usuario'}, status=500)

