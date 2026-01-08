"""
Utilidades de seguridad: Rate Limiting y Verificación de Correo
===============================================================
"""
import time
import secrets
import hashlib
from datetime import timedelta
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone


# ═══════════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request):
    """Obtiene la IP real del cliente, considerando proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_rate_limit_key(prefix, identifier):
    """Genera una clave única para rate limiting"""
    return f"ratelimit:{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"


class RateLimiter:
    """
    Sistema de rate limiting usando Django cache
    
    Uso:
        limiter = RateLimiter('login', max_attempts=5, window_seconds=300)
        if not limiter.is_allowed(identifier):
            return JsonResponse({'error': 'Demasiados intentos'}, status=429)
        limiter.record_attempt(identifier)
    """
    
    def __init__(self, action, max_attempts=5, window_seconds=300, block_seconds=900):
        """
        Args:
            action: Nombre de la acción (login, register, etc.)
            max_attempts: Máximo de intentos permitidos
            window_seconds: Ventana de tiempo en segundos (default: 5 minutos)
            block_seconds: Tiempo de bloqueo después de exceder límite (default: 15 minutos)
        """
        self.action = action
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
    
    def _get_key(self, identifier):
        return get_rate_limit_key(self.action, identifier)
    
    def _get_block_key(self, identifier):
        return f"{self._get_key(identifier)}:blocked"
    
    def is_blocked(self, identifier):
        """Verifica si el identificador está bloqueado"""
        return cache.get(self._get_block_key(identifier)) is not None
    
    def get_attempts(self, identifier):
        """Obtiene el número de intentos actuales"""
        data = cache.get(self._get_key(identifier), {'attempts': 0, 'first_attempt': None})
        return data.get('attempts', 0)
    
    def is_allowed(self, identifier):
        """Verifica si se permite otro intento"""
        if self.is_blocked(identifier):
            return False
        
        return self.get_attempts(identifier) < self.max_attempts
    
    def record_attempt(self, identifier, success=False):
        """
        Registra un intento
        
        Args:
            identifier: IP o username
            success: Si fue exitoso, resetea el contador
        """
        key = self._get_key(identifier)
        
        if success:
            # Login exitoso: resetear contador
            cache.delete(key)
            cache.delete(self._get_block_key(identifier))
            return
        
        data = cache.get(key, {'attempts': 0, 'first_attempt': time.time()})
        
        # Verificar si la ventana expiró
        if data['first_attempt'] and (time.time() - data['first_attempt']) > self.window_seconds:
            data = {'attempts': 0, 'first_attempt': time.time()}
        
        data['attempts'] += 1
        
        # Guardar en cache
        cache.set(key, data, self.window_seconds)
        
        # Si excede el límite, bloquear
        if data['attempts'] >= self.max_attempts:
            cache.set(self._get_block_key(identifier), True, self.block_seconds)
    
    def get_remaining_time(self, identifier):
        """Obtiene el tiempo restante de bloqueo en segundos"""
        block_key = self._get_block_key(identifier)
        ttl = cache.ttl(block_key) if hasattr(cache, 'ttl') else None
        
        if ttl is None:
            # Fallback: intentar obtener del cache
            if cache.get(block_key):
                return self.block_seconds
        return ttl or 0


# Instancias pre-configuradas de rate limiters
login_limiter = RateLimiter('login', max_attempts=5, window_seconds=300, block_seconds=900)
register_limiter = RateLimiter('register', max_attempts=3, window_seconds=3600, block_seconds=1800)
password_reset_limiter = RateLimiter('password_reset', max_attempts=3, window_seconds=3600, block_seconds=3600)
email_verify_limiter = RateLimiter('email_verify', max_attempts=5, window_seconds=3600, block_seconds=1800)


def rate_limit(limiter, use_ip=True, use_identifier=None):
    """
    Decorador para aplicar rate limiting a una vista
    
    Args:
        limiter: Instancia de RateLimiter
        use_ip: Usar IP del cliente como identificador
        use_identifier: Función que extrae identificador del request (ej: lambda r: r.POST.get('username'))
    
    Ejemplo:
        @rate_limit(login_limiter)
        def login_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            identifiers = []
            
            if use_ip:
                identifiers.append(f"ip:{get_client_ip(request)}")
            
            if use_identifier:
                try:
                    custom_id = use_identifier(request)
                    if custom_id:
                        identifiers.append(f"id:{custom_id}")
                except:
                    pass
            
            # Verificar todos los identificadores
            for identifier in identifiers:
                if not limiter.is_allowed(identifier):
                    remaining = limiter.get_remaining_time(identifier)
                    minutes = remaining // 60 if remaining else limiter.block_seconds // 60
                    
                    return JsonResponse({
                        'error': f'Demasiados intentos. Por favor espera {minutes} minutos.',
                        'retry_after': remaining or limiter.block_seconds,
                        'blocked': True
                    }, status=429)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# VERIFICACIÓN DE CORREO ELECTRÓNICO
# ═══════════════════════════════════════════════════════════════

def generate_verification_token():
    """Genera un token seguro para verificación de email"""
    return secrets.token_urlsafe(32)


def send_verification_email(cliente, request=None):
    """
    Envía email de verificación al cliente
    
    Args:
        cliente: Instancia del modelo Cliente
        request: HttpRequest para construir URLs absolutas
    
    Returns:
        bool: True si se envió correctamente
    """
    from store.models import Cliente
    
    # Generar nuevo token
    token = generate_verification_token()
    
    # Guardar token en el cliente
    cliente.email_verification_token = token
    cliente.email_verification_sent_at = timezone.now()
    cliente.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    
    # Construir URL de verificación
    if request:
        base_url = request.build_absolute_uri('/')[:-1]  # Quitar trailing slash
    else:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    verification_url = f"{base_url}/verificar-email/{token}/"
    
    # Preparar contenido del email
    context = {
        'nombre': cliente.nombre or cliente.username,
        'verification_url': verification_url,
        'expiry_hours': 24,
    }
    
    # HTML del email
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .logo {{ font-size: 28px; font-weight: 800; color: #1a1a2e; letter-spacing: -1px; }}
            .content {{ background: #fff; border-radius: 16px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ font-size: 24px; color: #1a1a2e; margin: 0 0 20px 0; }}
            p {{ margin: 0 0 16px 0; color: #4b5563; }}
            .btn {{ display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff !important; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 40px; color: #9ca3af; font-size: 14px; }}
            .expiry {{ background: #fef3c7; border-radius: 8px; padding: 12px 16px; color: #92400e; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NOWHERE</div>
            </div>
            <div class="content">
                <h1>¡Hola, {context['nombre']}!</h1>
                <p>Gracias por registrarte. Para activar tu cuenta y comenzar a comprar, necesitas verificar tu correo electrónico.</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="btn">Verificar mi correo</a>
                </p>
                <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                <p style="word-break: break-all; color: #667eea; font-size: 14px;">{verification_url}</p>
                <div class="expiry">
                    ⏰ Este enlace expira en {context['expiry_hours']} horas.
                </div>
            </div>
            <div class="footer">
                <p>Si no creaste esta cuenta, ignora este correo.</p>
                <p>&copy; 2026 NOWHERE. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    ¡Hola, {context['nombre']}!
    
    Gracias por registrarte en NOWHERE. Para activar tu cuenta, visita el siguiente enlace:
    
    {verification_url}
    
    Este enlace expira en {context['expiry_hours']} horas.
    
    Si no creaste esta cuenta, ignora este correo.
    
    © 2026 NOWHERE
    """
    
    try:
        send_mail(
            subject='Verifica tu correo - NOWHERE',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cliente.correo],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error enviando email de verificación: {e}")
        return False


def verify_email_token(token):
    """
    Verifica un token de email
    
    Args:
        token: Token de verificación
    
    Returns:
        tuple: (success: bool, cliente_or_error: Cliente|str)
    """
    from store.models import Cliente
    
    if not token:
        return False, "Token inválido"
    
    try:
        cliente = Cliente.objects.get(email_verification_token=token)
    except Cliente.DoesNotExist:
        return False, "Token inválido o expirado"
    
    # Verificar expiración (24 horas)
    if cliente.email_verification_sent_at:
        expiry_time = cliente.email_verification_sent_at + timedelta(hours=24)
        if timezone.now() > expiry_time:
            return False, "El enlace de verificación ha expirado. Solicita uno nuevo."
    
    # Marcar como verificado
    cliente.email_verified = True
    cliente.email_verification_token = None
    cliente.save(update_fields=['email_verified', 'email_verification_token'])
    
    return True, cliente


def resend_verification_email(email, request=None):
    """
    Reenvía el email de verificación
    
    Args:
        email: Correo del cliente
        request: HttpRequest
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from store.models import Cliente
    
    try:
        cliente = Cliente.objects.get(correo=email)
    except Cliente.DoesNotExist:
        # Por seguridad, no revelamos si el correo existe
        return True, "Si el correo está registrado, recibirás un enlace de verificación."
    
    if cliente.email_verified:
        return False, "Este correo ya está verificado."
    
    # Verificar cooldown (no más de 1 email cada 2 minutos)
    if cliente.email_verification_sent_at:
        cooldown = cliente.email_verification_sent_at + timedelta(minutes=2)
        if timezone.now() < cooldown:
            remaining = (cooldown - timezone.now()).seconds
            return False, f"Espera {remaining} segundos antes de solicitar otro correo."
    
    # Enviar email
    if send_verification_email(cliente, request):
        return True, "Se ha enviado un nuevo correo de verificación."
    else:
        return False, "Error al enviar el correo. Intenta más tarde."


# ═══════════════════════════════════════════════════════════════
# HELPERS ADICIONALES
# ═══════════════════════════════════════════════════════════════

def record_failed_login(identifier, ip=None):
    """Registra un intento de login fallido"""
    login_limiter.record_attempt(f"id:{identifier}")
    if ip:
        login_limiter.record_attempt(f"ip:{ip}")


def record_successful_login(identifier, ip=None):
    """Registra un login exitoso (resetea contadores)"""
    login_limiter.record_attempt(f"id:{identifier}", success=True)
    if ip:
        login_limiter.record_attempt(f"ip:{ip}", success=True)


def is_login_allowed(identifier, ip=None):
    """Verifica si se permite un intento de login"""
    if not login_limiter.is_allowed(f"id:{identifier}"):
        return False, login_limiter.get_remaining_time(f"id:{identifier}")
    if ip and not login_limiter.is_allowed(f"ip:{ip}"):
        return False, login_limiter.get_remaining_time(f"ip:{ip}")
    return True, 0
