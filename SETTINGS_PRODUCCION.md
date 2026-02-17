# ============================================================
# CONFIGURACIÓN DE DJANGO PARA PRODUCCIÓN
# Agregar/modificar estos valores en ecommerce/settings.py
# ============================================================

# 1. ALLOWED_HOSTS - Permitir tu dominio
ALLOWED_HOSTS = ['nowheremx.com', 'www.nowheremx.com', '127.0.0.1']

# 2. DEBUG - Desactivar en producción
DEBUG = False

# 3. SEGURIDAD SSL/TLS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 4. HSTS (Force HTTPS por 1 año)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 5. Encabezados de seguridad
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net"),
    'style-src': ("'self'", "'unsafe-inline'"),
    'img-src': ("'self'", "data:", "https:"),
    'font-src': ("'self'", "data:", "fonts.googleapis.com"),
}

# 6. Cookies
SECURE_COOKIE_HTTPONLY = True
SECURE_COOKIE_SAMESITE = 'Lax'

# 7. Permitir frames (si lo necesitas para pagos)
# X_FRAME_OPTIONS = 'ALLOWALL'  # Para Stripe, Conekta, etc.

# 8. CORS (Asegúrate de que sea específico)
CORS_ALLOWED_ORIGINS = [
    "https://nowheremx.com",
    "https://www.nowheremx.com",
]

# 9. Static files en producción
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# 10. Media files (para S3, así que esto casi no se usa)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ============================================================
# VERIFICAR EN SETTINGS.PY
# ============================================================
# Asegúrate de que tengas:
# - USE_S3 = True  (si usas AWS S3)
# - SECRET_KEY está en variables de entorno (nunca hardcodeado)
# - DEBUG viene de variables de entorno, no está hardcodeado a True
# - DATABASES configurada con PostgreSQL en producción
