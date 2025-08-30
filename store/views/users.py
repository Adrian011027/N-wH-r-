from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from ..models import Usuario
from .decorators import jwt_role_required
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
import json


# ───────────────────────────────────────────────
# Obtener todos los usuarios (solo admin)
# ───────────────────────────────────────────────
@jwt_role_required()
@require_GET
def get_user(request):
    #if request.user_role != "admin":
    #    return JsonResponse({"error": "Solo administradores"}, status=403)

    usuarios = Usuario.objects.all()
    data = [{"id": u.id, "username": u.username, "role": u.role} for u in usuarios]
    return JsonResponse(data, safe=False)


# ───────────────────────────────────────────────
# Crear usuario (solo admin)
# ───────────────────────────────────────────────
@csrf_exempt
@jwt_role_required()
@require_http_methods(["POST"])
def create_user(request):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        role     = data.get("role")

        if not username or not password or not role:
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)

        user = Usuario.objects.create(
            username=username,
            password=make_password(password),
            role=role
        )
        return JsonResponse({'username': user.username, 'message': 'Usuario creado con éxito'}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ───────────────────────────────────────────────
# Actualizar usuario (solo admin)
# ───────────────────────────────────────────────
@jwt_role_required()
@require_http_methods(["POST"])
def update_user(request, id):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = Usuario.objects.get(id=id)
        if username:
            user.username = username
        if password:
            user.password = make_password(password)
        user.save()

        return JsonResponse({'mensaje': f'user {id} actualizado correctamente'}, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as err:
        return JsonResponse({'error': str(err)}, status=400)


# ───────────────────────────────────────────────
# Eliminar usuario (solo admin)
# ───────────────────────────────────────────────
@jwt_role_required()
@require_http_methods(["DELETE"])
def delete_user(request, id):
    if request.user_role != "admin":
        return JsonResponse({"error": "Solo administradores"}, status=403)

    try:
        usuario = Usuario.objects.get(id=id)
        username = usuario.username
        usuario.delete()
        return JsonResponse({'mensaje': f'Usuario {username} eliminado correctamente'}, status=200)

    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
