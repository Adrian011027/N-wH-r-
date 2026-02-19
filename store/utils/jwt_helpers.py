import jwt
import datetime
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_jwt_secret():
    """Obtiene el secreto JWT. Usa JWT_SECRET_KEY si existe, sino SECRET_KEY."""
    secret = getattr(settings, 'JWT_SECRET_KEY', None)
    if secret and secret != settings.SECRET_KEY:
        return secret
    return settings.SECRET_KEY


def generate_access_token(user_id, role, username=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "type": "access",
        "exp": now + datetime.timedelta(minutes=30),
        "iat": now
    }
    if username:
        payload["username"] = username
    return jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")


def generate_refresh_token(user_id, role=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": now + datetime.timedelta(days=7),
        "iat": now
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")


def decode_jwt(token):
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
