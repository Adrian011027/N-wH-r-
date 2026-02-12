# Generated manually on 2026-02-12
# Migración de datos para marcar la primera variante de cada producto como principal

from django.db import migrations


def marcar_variantes_principales(apps, schema_editor):
    """
    Marca la primera variante (por ID) de cada producto como es_variante_principal=True
    """
    Producto = apps.get_model('store', 'Producto')
    Variante = apps.get_model('store', 'Variante')
    
    productos_actualizados = 0
    variantes_marcadas = 0
    
    for producto in Producto.objects.all():
        # Obtener la primera variante del producto (por ID más bajo)
        primera_variante = producto.variantes.order_by('id').first()
        
        if primera_variante and not primera_variante.es_variante_principal:
            primera_variante.es_variante_principal = True
            primera_variante.save(update_fields=['es_variante_principal'])
            variantes_marcadas += 1
            productos_actualizados += 1
    
    print(f"\n✓ Migración completada:")
    print(f"  - Productos procesados: {productos_actualizados}")
    print(f"  - Variantes marcadas como principales: {variantes_marcadas}")


def revertir_cambios(apps, schema_editor):
    """
    Revierte los cambios eliminando la marca de variante principal
    """
    Variante = apps.get_model('store', 'Variante')
    Variante.objects.all().update(es_variante_principal=False)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_variante_es_variante_principal_alter_producto_genero_and_more'),
    ]

    operations = [
        migrations.RunPython(marcar_variantes_principales, revertir_cambios),
    ]
