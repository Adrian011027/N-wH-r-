"""
Management command para ocultar productos (bodega=True)

Uso:
    python manage.py hacer_productos_ocultos --productos 1 2 3
    python manage.py hacer_productos_ocultos --todos  # Ocultar TODOS (requiere confirmación)
"""

from django.core.management.base import BaseCommand
from store.models import Producto


class Command(BaseCommand):
    help = 'Oculta productos cambiando bodega=True'

    def add_arguments(self, parser):
        parser.add_argument(
            '--productos',
            nargs='+',
            type=int,
            help='IDs específicos de productos a ocultar',
        )
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Ocultar TODOS los productos',
        )

    def handle(self, *args, **options):
        productos_ids = options.get('productos')
        todos = options.get('todos')

        if not productos_ids and not todos:
            self.stdout.write(
                self.style.ERROR(
                    'Error: Debes especificar --productos ID1 ID2... o --todos'
                )
            )
            return

        if todos:
            # Confirmación para ocultar todos
            confirmacion = input(
                '⚠️  ¿Seguro que quieres ocultar TODOS los productos? (escribe "SI"): '
            )
            if confirmacion != 'SI':
                self.stdout.write(self.style.WARNING('Operación cancelada'))
                return
            
            productos = Producto.objects.all()
            self.stdout.write(
                self.style.WARNING(
                    f'Ocultando TODOS los {productos.count()} productos...'
                )
            )
        else:
            # Solo productos específicos
            productos = Producto.objects.filter(id__in=productos_ids)
            self.stdout.write(
                self.style.WARNING(
                    f'Ocultando {productos.count()} productos específicos...'
                )
            )

        # Contar cuántos ya estaban ocultos
        ya_ocultos = productos.filter(bodega=True).count()
        
        # Actualizar todos a bodega=True
        actualizados = productos.update(bodega=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Completado:\n'
                f'   - Total procesados: {actualizados}\n'
                f'   - Ya estaban ocultos: {ya_ocultos}\n'
                f'   - Cambiados a ocultos: {actualizados - ya_ocultos}\n'
            )
        )
        
        # Mostrar productos actualizados
        if actualizados > 0 and actualizados <= 20:
            self.stdout.write(self.style.SUCCESS('\nProductos ahora ocultos:'))
            for p in productos:
                self.stdout.write(f'  - #{p.id}: {p.nombre}')
