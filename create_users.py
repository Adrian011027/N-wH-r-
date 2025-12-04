#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear usuarios iniciales en la base de datos AWS RDS
- admin (Usuario dashboard, rol: admin)
- jona (Cliente normal)
- angel (Cliente normal)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Usuario, Cliente
from django.contrib.auth.hashers import make_password

def crear_usuarios():
    print("\n" + "="*70)
    print("👥 CREANDO USUARIOS INICIALES")
    print("="*70)
    
    # 1. Usuario admin para el dashboard
    if Usuario.objects.filter(username='admin').exists():
        print("\n⚠️  Usuario 'admin' ya existe")
    else:
        Usuario.objects.create(
            username='admin',
            password=make_password('admin123'),
            role='admin'
        )
        print("\n✅ Usuario creado: admin")
        print("   Password: admin123")
        print("   Rol: admin")
        print("   URL: http://127.0.0.1:8000/dashboard/login/")
    
    # 2. Cliente jona
    if Cliente.objects.filter(username='jona').exists():
        print("\n⚠️  Cliente 'jona' ya existe")
    else:
        Cliente.objects.create_user(
            username='jona',
            correo='jona@nowhere.com',
            nombre='Jonathan',
            password='123456',
            telefono='3312345678',
            direccion='Guadalajara, Jalisco'
        )
        print("\n✅ Cliente creado: jona")
        print("   Password: 123456")
        print("   Email: jona@nowhere.com")
    
    # 3. Cliente angel
    if Cliente.objects.filter(username='angel').exists():
        print("\n⚠️  Cliente 'angel' ya existe")
    else:
        Cliente.objects.create_user(
            username='angel',
            correo='angel@nowhere.com',
            nombre='Angel',
            password='123456',
            telefono='3387654321',
            direccion='Guadalajara, Jalisco'
        )
        print("\n✅ Cliente creado: angel")
        print("   Password: 123456")
        print("   Email: angel@nowhere.com")
    
    print("\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    print(f"👤 Usuarios dashboard: {Usuario.objects.count()}")
    print(f"👥 Clientes: {Cliente.objects.count()}")
    print("\n🧪 Prueba de login:")
    print("   Dashboard: http://127.0.0.1:8000/dashboard/login/")
    print("   Usuario: admin / admin123")
    print("\n   Frontend: http://127.0.0.1:8000/")
    print("   Usuario: jona / 123456  o  angel / 123456")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        crear_usuarios()
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
