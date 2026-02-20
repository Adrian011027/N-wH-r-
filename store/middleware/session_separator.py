from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class SessionTypeValidator(MiddlewareMixin):
    """Valida que rutas /dashboard/* tengan sesión de admin"""
    
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
        
        # Si es ruta /dashboard/*, validar que tenga user_id
        if path.startswith('/dashboard/'):
            user_id = request.session.get('user_id')
            if not user_id:
                # El decorator login_required_user se encargará de redirigir
                logger.warning(f"Acceso sin autorización a {path}")
                return None
        
        # Si es ruta /inventario/*, validar que tenga user_id
        if path.startswith('/inventario/'):
            user_id = request.session.get('user_id')
            if not user_id:
                # El decorator login_required_inventario se encargará de redirigir
                logger.warning(f"Acceso sin sesión a inventario: {path}")
                return None
        
        return None
