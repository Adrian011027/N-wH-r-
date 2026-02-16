"""
Migration: Agregar campos de Stripe al modelo Orden
Se añaden stripe_session_id y stripe_payment_intent para la integración con Stripe.
Los campos de Conekta se mantienen por compatibilidad con órdenes históricas.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_marcar_variantes_principales'),
    ]

    operations = [
        migrations.AddField(
            model_name='orden',
            name='stripe_session_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='orden',
            name='stripe_payment_intent',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
