#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para borrar TODAS las tablas de la base de datos y empezar limpio.
⚠️ USAR SOLO EN DESARROLLO - ESTO BORRA TODO
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.db import connection

print("\n" + "="*70)
print("⚠️  ADVERTENCIA: Esto borrará TODAS las tablas")
print("="*70)

confirmacion = input("\n¿Estás seguro? Escribe 'SI BORRAR TODO': ")

if confirmacion == "SI BORRAR TODO":
    with connection.cursor() as cursor:
        # Obtener todas las tablas
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public';
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        if tables:
            print(f"\n🗑️  Borrando {len(tables)} tablas...")
            
            # Borrar todas las tablas
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            
            print("✅ Todas las tablas borradas")
            print("\n📝 Ahora ejecuta:")
            print("   python manage.py migrate")
            print("   python create_users.py\n")
        else:
            print("\n✅ La base de datos ya está vacía\n")
else:
    print("\n❌ Operación cancelada\n")
