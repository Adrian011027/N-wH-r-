"""
Management command para hacer públicos todos los productos (bodega=False)

Uso:
    python manage.py hacer_productos_publicos
    python manage.py hacer_productos_publicos --productos 1 2 3  # Solo IDs específicos
"""

from django.core.management.base import BaseCommand
from store.models import Producto


class Command(BaseCommand):
    help = 'Hace públicos todos los productos cambiando bodega=False'

    def add_arguments(self, parser):
        parser.add_argument(
            '--productos',
            nargs='+',
            type=int,
            help='IDs específicos de productos a hacer públicos (opcional)',
        )

    def handle(self, *args, **options):
        productos_ids = options.get('productos')

        if productos_ids:
            # Solo productos específicos
            productos = Producto.objects.filter(id__in=productos_ids)
            self.stdout.write(
                self.style.WARNING(
                    f'Haciendo públicos {productos.count()} productos específicos...'
                )
            )
        else:
            # Todos los productos
            productos = Producto.objects.all()
            self.stdout.write(
                self.style.WARNING(
                    f'Haciendo públicos TODOS los {productos.count()} productos...'
                )
            )

        # Contar cuántos ya eran públicos
        ya_publicos = productos.filter(bodega=False).count()
        
        # Actualizar todos a bodega=False
        actualizados = productos.update(bodega=False)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Completado:\n'
                f'   - Total procesados: {actualizados}\n'
                f'   - Ya eran públicos: {ya_publicos}\n'
                f'   - Cambiados a públicos: {actualizados - ya_publicos}\n'
            )
        )
        
        # Mostrar productos actualizados
        if actualizados > 0 and actualizados <= 20:
            self.stdout.write(self.style.SUCCESS('\nProductos ahora públicos:'))
            for p in productos:
                self.stdout.write(f'  - #{p.id}: {p.nombre}')
