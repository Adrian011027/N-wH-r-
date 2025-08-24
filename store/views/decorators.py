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
def jwt_required(view_func):
    """
    Valida que la request traiga un JWT válido en el header Authorization.
    Devuelve JSON 401 si no es válido o está expirado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Token requerido"}, status=401)

        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)
        if not payload:
            return JsonResponse({"error": "Token inválido o expirado"}, status=401)

        # Inyectar en request para que las views lo usen
        request.user_id = payload["user_id"]
        request.user_role = payload.get("role", "cliente")

        return view_func(request, *args, **kwargs)
    return wrapper
