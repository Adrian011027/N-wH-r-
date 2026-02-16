"""
Migration: Variante model restructure
 - 1 variante = 1 color (with tallas_stock JSONField instead of individual talla/stock)
 - Add talla field to CarritoProducto and OrdenDetalle
"""
from django.db import migrations, models


def migrate_talla_stock_forward(apps, schema_editor):
    """
    Convierte el campo talla + stock de cada Variante
    al nuevo formato tallas_stock = {"talla": stock}
    """
    Variante = apps.get_model('store', 'Variante')
    for v in Variante.objects.all():
        talla = v.talla or 'UNICA'
        stock = v.stock or 0
        # Agrupar: si ya existe una variante del mismo producto+color,
        # se podría fusionar, pero por seguridad asignamos 1:1
        v.tallas_stock = {talla: stock}
        v.save(update_fields=['tallas_stock'])

    # Llenar el campo talla en CarritoProducto con la talla de la variante
    CarritoProducto = apps.get_model('store', 'CarritoProducto')
    for cp in CarritoProducto.objects.select_related('variante').all():
        cp.talla = cp.variante.talla or 'UNICA'
        cp.save(update_fields=['talla'])

    # Llenar el campo talla en OrdenDetalle con la talla de la variante
    OrdenDetalle = apps.get_model('store', 'OrdenDetalle')
    for od in OrdenDetalle.objects.select_related('variante').all():
        od.talla = od.variante.talla or 'UNICA'
        od.save(update_fields=['talla'])


def migrate_talla_stock_reverse(apps, schema_editor):
    """
    Reverse: extract first talla from tallas_stock back to talla+stock fields
    """
    Variante = apps.get_model('store', 'Variante')
    for v in Variante.objects.all():
        if v.tallas_stock:
            first_talla = next(iter(v.tallas_stock))
            v.talla = first_talla
            v.stock = v.tallas_stock[first_talla]
        else:
            v.talla = 'UNICA'
            v.stock = 0
        v.save(update_fields=['talla', 'stock'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_orden_stripe_fields'),
    ]

    operations = [
        # 1. Add new fields FIRST (before removing old ones)
        migrations.AddField(
            model_name='variante',
            name='tallas_stock',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='Dict de talla→stock. Ej: {"38": 5, "39": 3, "40": 0}'
            ),
        ),
        migrations.AddField(
            model_name='carritoproducto',
            name='talla',
            field=models.CharField(
                default='UNICA', max_length=20,
                help_text='Talla seleccionada de tallas_stock'
            ),
        ),
        migrations.AddField(
            model_name='ordendetalle',
            name='talla',
            field=models.CharField(
                default='UNICA', max_length=20,
                help_text='Talla que se compró'
            ),
        ),

        # 2. Data migration: convert talla+stock → tallas_stock
        migrations.RunPython(
            migrate_talla_stock_forward,
            migrate_talla_stock_reverse,
        ),

        # 3. Now remove old fields
        migrations.RemoveIndex(
            model_name='variante',
            name='store_varia_talla_a46dc4_idx',
        ),
        migrations.RemoveIndex(
            model_name='variante',
            name='store_varia_product_e66c22_idx',
        ),
        migrations.RemoveField(
            model_name='variante',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='variante',
            name='talla',
        ),

        # 4. Update meta
        migrations.AlterModelOptions(
            name='variante',
            options={'ordering': ['color']},
        ),
        migrations.AlterField(
            model_name='variante',
            name='imagen',
            field=models.ImageField(
                blank=True, null=True,
                upload_to='variantes/',
                help_text='Imagen específica de esta variante'
            ),
        ),

        # 5. Add new indexes
        migrations.AddIndex(
            model_name='variante',
            index=models.Index(fields=['color'], name='store_varia_color_b4d196_idx'),
        ),
        migrations.AddIndex(
            model_name='variante',
            index=models.Index(fields=['producto'], name='store_varia_product_4dd624_idx'),
        ),
    ]
