#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear la base de datos nowhere-db en AWS RDS
"""
import psycopg2
from decouple import config

# Conectar a la base de datos por defecto
conn = psycopg2.connect(
    host=config('DB_HOST'),
    port=config('DB_PORT'),
    user=config('DB_USER'),
    password=config('DB_PASSWORD'),
    database='postgres'  # Conectar a postgres por defecto
)
conn.autocommit = True

cursor = conn.cursor()

try:
    # Verificar si la base de datos existe
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'nowhere-db'")
    exists = cursor.fetchone()
    
    if exists:
        print("\n✅ La base de datos 'nowhere-db' ya existe\n")
    else:
        # Crear la base de datos con comillas por el guión
        cursor.execute('CREATE DATABASE "nowhere-db"')
        print("\n✅ Base de datos 'nowhere-db' creada exitosamente\n")
        print("📝 Ahora ejecuta:")
        print("   python manage.py migrate\n")
        
except Exception as e:
    print(f"\n❌ Error: {e}\n")
finally:
    cursor.close()
    conn.close()
