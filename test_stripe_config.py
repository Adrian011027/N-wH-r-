import os, django, re
os.environ['DJANGO_SETTINGS_MODULE'] = 'ecommerce.settings'
django.setup()

from django.conf import settings

# Verificar claves en settings
print("=" * 60)
print("CONFIGURACIÓN DE STRIPE EN SETTINGS.PY:")
print("=" * 60)
print(f"STRIPE_PUBLIC_KEY: {settings.STRIPE_PUBLIC_KEY[:30]}..." if len(settings.STRIPE_PUBLIC_KEY) > 30 else settings.STRIPE_PUBLIC_KEY)
print(f"  Longitud: {len(settings.STRIPE_PUBLIC_KEY)}")
print(f"  Vacía: {not settings.STRIPE_PUBLIC_KEY}")
print()
print(f"STRIPE_SECRET_KEY: {settings.STRIPE_SECRET_KEY[:30]}..." if len(settings.STRIPE_SECRET_KEY) > 30 else settings.STRIPE_SECRET_KEY)
print(f"  Longitud: {len(settings.STRIPE_SECRET_KEY)}")
print(f"  Vacía: {not settings.STRIPE_SECRET_KEY}")
print()

# Verificar que stripe.api_key está configurado
import stripe
print("=" * 60)
print("CONFIGURACIÓN DE STRIPE EN EL MÓDULO:")
print("=" * 60)
print(f"stripe.api_key: {stripe.api_key[:30] if stripe.api_key else 'None'}..." if stripe.api_key and len(stripe.api_key) > 30 else str(stripe.api_key))
print()
