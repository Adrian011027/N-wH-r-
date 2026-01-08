"""
Vistas de verificación de correo electrónico
=============================================
"""
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Cliente
from ..utils.security import (
    verify_email_token,
    send_verification_email,
    resend_verification_email,
    email_verify_limiter,
    get_client_ip,
    rate_limit
)


@csrf_exempt
@require_http_methods(["GET"])
def verificar_email(request, token):
    """
    Verifica el correo electrónico del cliente usando el token
    GET /verificar-email/<token>/
    """
    success, result = verify_email_token(token)
    
    if success:
        # Renderizar página de éxito
        return render(request, 'public/verificacion/exito.html', {
            'cliente': result,
            'message': '¡Tu correo ha sido verificado exitosamente!'
        })
    else:
        # Renderizar página de error
        return render(request, 'public/verificacion/error.html', {
            'error': result
        })


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit(email_verify_limiter)
def reenviar_verificacion(request):
    """
    Reenvía el correo de verificación
    POST /api/auth/reenviar-verificacion/
    Body: {"correo": "email@ejemplo.com"}
    """
    try:
        data = json.loads(request.body)
        correo = data.get('correo', '').strip().lower()
        
        if not correo:
            return JsonResponse({'error': 'El correo es requerido'}, status=400)
        
        success, message = resend_verification_email(correo, request)
        
        if success:
            return JsonResponse({'message': message}, status=200)
        else:
            return JsonResponse({'error': message}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def estado_verificacion(request):
    """
    Verifica si el usuario actual tiene su correo verificado
    GET /api/auth/estado-verificacion/
    Requiere JWT token
    """
    import jwt
    from django.conf import settings
    
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Token requerido'}, status=401)
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        cliente_id = payload.get('user_id')
        if not cliente_id:
            return JsonResponse({'error': 'Token inválido'}, status=401)
        
        cliente = Cliente.objects.get(id=cliente_id)
        
        return JsonResponse({
            'email_verified': cliente.email_verified,
            'correo': cliente.correo
        })
    
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expirado'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Token inválido'}, status=401)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)


def pagina_verificacion_pendiente(request):
    """
    Página que muestra al usuario que debe verificar su correo
    GET /verificacion-pendiente/
    """
    return render(request, 'public/verificacion/pendiente.html')
