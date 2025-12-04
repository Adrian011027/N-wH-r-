"""
Script para eliminar tablas obsoletas del sistema antiguo de atributos.
Ejecutar con: python limpiar_tablas_atributos.py
"""
import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings

def eliminar_tablas_antiguas():
    """Elimina las tablas del sistema antiguo de atributos que ya no se usan"""
    
    # Obtener configuración de la base de datos desde settings.py
    db_config = settings.DATABASES['default']
    
    print("🔄 Conectando a la base de datos...")
    
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            dbname=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            port=db_config['PORT']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa\n")
        
        # Tablas a eliminar (orden importa por foreign keys)
        tablas = [
            'store_varianteatributo',
            'store_atributovalor',
            'store_atributo'
        ]
        
        print("📋 Tablas a eliminar:")
        for tabla in tablas:
            print(f"   - {tabla}")
        
        respuesta = input("\n¿Confirmas eliminar estas tablas? (s/n): ").strip().lower()
        
        if respuesta != 's':
            print("❌ Operación cancelada por el usuario.")
            cursor.close()
            conn.close()
            return
        
        print("\n🗑️ Eliminando tablas...\n")
        
        eliminadas = 0
        for tabla in tablas:
            try:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (tabla,))
                
                existe = cursor.fetchone()[0]
                
                if existe:
                    # Eliminar tabla
                    cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                        sql.Identifier(tabla)
                    ))
                    print(f"   ✅ {tabla} eliminada")
                    eliminadas += 1
                else:
                    print(f"   ⚠️ {tabla} no existe (ya fue eliminada)")
                    
            except Exception as e:
                print(f"   ❌ Error al eliminar {tabla}: {e}")
        
        print(f"\n✅ Proceso completado: {eliminadas} tablas eliminadas\n")
        
        # Verificar tablas restantes
        print("📊 Verificando tablas store_ restantes:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'store_%'
            ORDER BY table_name;
        """)
        
        tablas_restantes = cursor.fetchall()
        for (tabla,) in tablas_restantes:
            print(f"   • {tabla}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ ¡Limpieza completada con éxito!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Error de PostgreSQL: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    eliminar_tablas_antiguas()
