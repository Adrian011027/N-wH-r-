# NOTA TEMPORAL: Actualizar carrito.py después de las migraciones
# 
# Las siguientes líneas en store/views/carrito.py necesitan actualizarse:
#
# BUSCAR Y REEMPLAZAR:
# 
# 1. Eliminar todos los .prefetch_related("variante__attrs__atributo_valor")
#    → Ya no se necesitan
#
# 2. Cambiar: [str(av) for av in var.attrs.all()]
#    → Por: {"talla": var.talla, "color": var.color, "otros": var.otros}
#
# 3. Cambiar: av.atributo_valor.valor for av in var.attrs.all() if av.atributo_valor.atributo.nombre.lower() == "talla"
#    → Por: var.talla
#
# 4. Cambiar: atributos = [str(av) for av in var.attrs.all()]
#    → Por: atributos = f"Talla: {var.talla}, Color: {var.color}"
#
# 5. En lugar de:
#    if 'talla' in var_attr.atributo_valor.atributo.nombre.lower():
#        talla = var_attr.atributo_valor.valor
#    → Usar directamente: talla = variante.talla
