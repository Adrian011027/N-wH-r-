"""
Script para migrar variantes sin talla/color al nuevo sistema simplificado.
Ejecutar con: python migrar_variantes.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Variante

def migrar_variantes():
    """
    Actualiza variantes que tienen talla vacía, None o con valores genéricos
    para que muestren valores descriptivos en el dashboard.
    """
    print("🔄 Iniciando migración de variantes...\n")
    
    # Buscar variantes sin talla o con valores genéricos
    variantes_sin_talla = Variante.objects.filter(
        talla__in=['', 'UNICA', 'N/A', None]
    )
    
    total = variantes_sin_talla.count()
    print(f"📊 Encontradas {total} variantes sin talla específica\n")
    
    if total == 0:
        print("✅ No hay variantes que migrar. Todas tienen talla asignada.")
        return
    
    # Mostrar ejemplos
    print("📋 Ejemplos de variantes a actualizar:")
    for i, v in enumerate(variantes_sin_talla[:5]):
        print(f"  {i+1}. Producto: {v.producto.nombre} | Talla actual: '{v.talla}' | Color: '{v.color}'")
    
    if total > 5:
        print(f"  ... y {total - 5} más\n")
    else:
        print()
    
    # Preguntar confirmación
    respuesta = input("¿Deseas actualizar estas variantes? (s/n): ").strip().lower()
    
    if respuesta != 's':
        print("❌ Migración cancelada por el usuario.")
        return
    
    print("\n🚀 Actualizando variantes...\n")
    
    actualizadas = 0
    for v in variantes_sin_talla:
        # Si la talla está vacía o es None, asignar "Única"
        if not v.talla or v.talla in ['', 'N/A']:
            v.talla = 'Única'
        
        # Si no tiene color o es N/A, dejarlo como "Sin especificar"
        if not v.color or v.color == 'N/A':
            v.color = 'Sin especificar'
        
        v.save()
        actualizadas += 1
        
        if actualizadas % 10 == 0:
            print(f"  ✓ Actualizadas {actualizadas}/{total} variantes...")
    
    print(f"\n✅ ¡Migración completada! Se actualizaron {actualizadas} variantes.")
    print("\n📝 Cambios realizados:")
    print("  - Tallas vacías/N/A → 'Única'")
    print("  - Colores N/A → 'Sin especificar'")
    print("\n💡 Ahora puedes editar manualmente las variantes en el dashboard para asignar tallas específicas.")

if __name__ == '__main__':
    try:
        migrar_variantes()
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
