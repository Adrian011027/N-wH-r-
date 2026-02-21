from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class SessionTypeValidator(MiddlewareMixin):
    """Valida que rutas /dashboard/* y /inventario/* tengan sus sesiones respectivas"""
    
    def process_request(self, request):
        path = request.path
        
        # Rutas públicas que NO necesitan validación
        public_routes = [
            '/dashboard/login/',
            '/auth/login/',
            '/auth/login_client/',
            '/registrarse/',
            '/recuperar/',
            '/inventario/login/',
            '/inventario/auth/login/',
        ]
        
        # Si es ruta pública, permitir
        if path in public_routes:
            return None
        
        # Si es ruta /dashboard/*, validar que tenga sesión del DASHBOARD
        if path.startswith('/dashboard/'):
            user_id = request.session.get('dashboard_user_id')
            if not user_id:
                # El decorator login_required_user se encargará de redirigir
                logger.warning(f"Acceso sin autorización del dashboard a {path}")
                return None
        
        # Si es ruta /inventario/*, validar que tenga sesión del INVENTARIO
        if path.startswith('/inventario/'):
            user_id = request.session.get('inventario_user_id')
            if not user_id:
                # El decorator login_required_inventario se encargará de redirigir
                logger.warning(f"Acceso sin sesión del inventario: {path}")
                return None
        
        return None
