# store/views/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from ..models import Usuario
from store.utils.jwt_helpers import decode_jwt


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
# store/views/decorators.py
from functools import wraps
from django.http import JsonResponse
from store.utils.jwt_helpers import decode_jwt

def jwt_role_required(allowed_roles=None, allow_self=True):
    """
    Valida JWT + rol (Usuario/Admin) + dueño del recurso (Cliente).
    - allowed_roles: lista de roles permitidos (ej: ['admin', 'seller'])
    - allow_self: si True, permite que un usuario/cliente acceda solo a su propio recurso
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JsonResponse({"error": "Token requerido"}, status=401)

            token = auth_header.split(" ", 1)[1]
            payload = decode_jwt(token)
            if not payload:
                return JsonResponse({"error": "Token inválido o expirado"}, status=401)

            request.user_id = payload.get("user_id")
            request.user_role = payload.get("role")

            # 1) Admin siempre pasa
            if request.user_role == "admin":
                return view_func(request, *args, **kwargs)

            # 2) Si el rol está permitido explícitamente
            if request.user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # 3) Si allow_self=True → solo su propio recurso
            if allow_self:
                target_id = kwargs.get("id") or kwargs.get("cliente_id") or kwargs.get("user_id")
                if target_id and str(target_id) != str(request.user_id):
                    return JsonResponse({"error": "No tienes permiso para acceder a este recurso"}, status=403)
                return view_func(request, *args, **kwargs)

            return JsonResponse({"error": "Acceso denegado"}, status=403)
        return _wrapped
    return decorator
