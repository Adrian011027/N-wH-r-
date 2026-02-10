# Generated migration to convert genero from short format (H, M) to long format (Hombre, Mujer, Unisex)

from django.db import migrations

def convert_genero(apps, schema_editor):
    """Convierte los valores de género a formato extenso"""
    Producto = apps.get_model('store', 'Producto')
    
    # Mapeo de valores antiguos a nuevos
    mapping = {
        'H': 'Hombre',
        'M': 'Mujer',
        'U': 'Unisex',
        'hombre': 'Hombre',
        'mujer': 'Mujer',
        'unisex': 'Unisex',
    }
    
    for producto in Producto.objects.all():
        if producto.genero in mapping:
            producto.genero = mapping[producto.genero]
            producto.save()

def reverse_genero(apps, schema_editor):
    """Revierte los valores a formato corto si es necesario"""
    Producto = apps.get_model('store', 'Producto')
    
    reverse_mapping = {
        'Hombre': 'H',
        'Mujer': 'M',
        'Unisex': 'U',
    }
    
    for producto in Producto.objects.all():
        if producto.genero in reverse_mapping:
            producto.genero = reverse_mapping[producto.genero]
            producto.save()

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_orden_carrito_nullable'),
    ]

    operations = [
        migrations.RunPython(convert_genero, reverse_genero),
    ]
