"""
Script de prueba: Rate Limiting y Verificación de Email
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()

from django.test import Client
import json

c = Client()

print('='*60)
print('TEST 1: Rate Limiting en Registro')
print('='*60)

# Hacer múltiples intentos de registro
for i in range(5):
    r = c.post('/clientes/crear/', 
        json.dumps({'username': f'testrl{i}', 'password': 'pass1234', 'correo': f'testrl{i}@test.com'}),
        content_type='application/json')
    print(f'Intento {i+1}: Status {r.status_code}')
    data = json.loads(r.content)
    if r.status_code == 429:
        print(f'  -> BLOQUEADO: {data.get("error", "")}')
        break
    elif r.status_code == 201:
        print(f'  -> OK: {data.get("message", "")}')
        print(f'     Email verification sent: {data.get("email_verification_sent", False)}')
    else:
        print(f'  -> Error: {data.get("error", "")}')

print()
print('='*60)
print('TEST 2: Login con Rate Limiting')
print('='*60)

# Intentos de login fallidos
for i in range(7):
    r = c.post('/auth/login_client/', 
        json.dumps({'username': 'noexiste', 'password': 'wrongpass'}),
        content_type='application/json')
    data = json.loads(r.content)
    print(f'Intento {i+1}: Status {r.status_code}')
    if r.status_code == 429:
        print(f'  -> BLOQUEADO: {data.get("error", "")}')
        break
    else:
        print(f'  -> {data.get("error", "")}')

print()
print('='*60)
print('TEST 3: Verificación de campos nuevos')
print('='*60)

from store.models import Cliente
cliente = Cliente.objects.first()
if cliente:
    print(f'Cliente: {cliente.username}')
    print(f'Email verificado: {cliente.email_verified}')
    print(f'Token: {cliente.email_verification_token or "N/A"}')
    print(f'Enviado: {cliente.email_verification_sent_at or "N/A"}')
else:
    print('No hay clientes en la base de datos')

print()
print('='*60)
print('TEST 4: Login exitoso devuelve estado de verificación')
print('='*60)

# Crear cliente de prueba
from django.contrib.auth.hashers import make_password
test_client, created = Cliente.objects.get_or_create(
    username='test_verify',
    defaults={
        'password': make_password('testpass123'),
        'correo': 'test_verify@test.com',
        'email_verified': False
    }
)

# Login con ese cliente
r = c.post('/auth/login_client/', 
    json.dumps({'username': 'test_verify', 'password': 'testpass123'}),
    content_type='application/json')
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = json.loads(r.content)
    print(f'Username: {data.get("username")}')
    print(f'Email verified: {data.get("email_verified")}')
    print(f'Warning: {data.get("warning", "ninguno")}')

print()
print('='*60)
print('TODOS LOS TESTS COMPLETADOS')
print('='*60)
