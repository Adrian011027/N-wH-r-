"""
Manejadores de errores HTTP personalizados
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings


def custom_404(request, exception=None):
    """
    Vista personalizada para manejar errores 404
    No expone las rutas disponibles por razones de seguridad
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'No encontrado',
            'status': 404,
            'message': 'El recurso solicitado no existe.'
        }, status=404)
    
    return render(request, '404.html', {
        'message': 'La página que buscas no existe.'
    }, status=404)


def custom_500(request):
    """
    Vista personalizada para manejar errores 500
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Error interno del servidor',
            'status': 500,
            'message': 'Algo salió mal. Por favor intenta más tarde.'
        }, status=500)
    
    return render(request, '500.html', {
        'message': 'Algo salió mal. Por favor intenta más tarde.'
    }, status=500)
