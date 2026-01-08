from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.text import slugify
import os

# ——————————————————————————————————————
# Funciones para upload_to callbacks
# ——————————————————————————————————————

def producto_imagen_upload_to(instance, filename):
    """
    Callback para generar la ruta de imágenes de galería de producto.
    Formato: productos/prod-{id}-{slug}/imagen-{numero}.{ext}
    """
    if not instance.producto.id:
        return f'productos/galeria/{filename}'
    
    ext = os.path.splitext(filename)[1].lower()
    slug = slugify(instance.producto.nombre)[:40]
    return f'productos/prod-{instance.producto.id}-{slug}/{filename}'


def variante_imagen_upload_to(instance, filename):
    """
    Callback para generar la ruta de imágenes de galería de variante.
    Formato: variantes/var-{prod-id}-{var-id}-{talla}-{color}/imagen-{numero}.{ext}
    """
    if not instance.variante.id:
        return f'variantes/galeria/{filename}'
    
    ext = os.path.splitext(filename)[1].lower()
    producto_slug = slugify(instance.variante.producto.nombre)[:30]
    talla_clean = slugify(instance.variante.talla or "unica")[:10]
    color_clean = slugify(instance.variante.color or "na")[:10]
    return f'variantes/var-{instance.variante.producto_id}-{instance.variante.id}-{talla_clean}-{color_clean}/{filename}'


# ——————————————————————————————————————
# Modelos de usuario y cliente
# ——————————————————————————————————————



class ClienteManager(BaseUserManager):
    def create_user(self, username, correo, nombre, password=None, telefono=None, direccion=None):
        """
        Crea y guarda un Cliente con username, correo y nombre obligatorios,
        y teléfono y dirección opcionales.
        """
        if not username:
            raise ValueError("El usuario debe tener un username")
        if not correo:
            raise ValueError("El usuario debe tener un correo electrónico")
        if not nombre:
            raise ValueError("El usuario debe tener un nombre")

        cliente = self.model(
            username=username,
            correo=correo,
            nombre=nombre,
            telefono=telefono,
            direccion=direccion
        )
        cliente.set_password(password)
        cliente.save(using=self._db)
        return cliente

    def create_superuser(self, username, correo, nombre, password):
        cliente = self.create_user(
            username=username,
            correo=correo,
            nombre=nombre,
            password=password
        )
        cliente.is_admin = True
        cliente.save(using=self._db)
        return cliente

class Cliente(AbstractBaseUser):
    # Información básica
    username   = models.CharField(max_length=255, unique=True)
    correo     = models.EmailField(max_length=255, blank=True)
    nombre     = models.CharField(max_length=255, null=True)
    telefono   = models.CharField(max_length=20, blank=True, null=True)
    telefono_alternativo = models.CharField(max_length=20, blank=True, null=True)
    
    # Control de cambio de username (1 vez por mes)
    ultima_modificacion_username = models.DateTimeField(null=True, blank=True)
    
    # Verificación de correo electrónico
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Dirección de envío
    calle           = models.CharField(max_length=500, blank=True, null=True)
    colonia         = models.CharField(max_length=200, blank=True, null=True)
    codigo_postal   = models.CharField(max_length=5, blank=True, null=True)
    ciudad          = models.CharField(max_length=200, blank=True, null=True)
    estado          = models.CharField(max_length=100, blank=True, null=True)
    referencias     = models.TextField(blank=True, null=True)
    
    # Dirección completa (legacy - mantener por compatibilidad)
    direccion  = models.CharField(max_length=500, blank=True, null=True)
    
    # Información fiscal
    tipo_cliente      = models.CharField(max_length=20, default='menudeo', choices=[('menudeo', 'Menudeo'), ('mayoreo', 'Mayoreo')])
    rfc               = models.CharField(max_length=13, blank=True, null=True)
    razon_social      = models.CharField(max_length=500, blank=True, null=True)
    direccion_fiscal  = models.CharField(max_length=500, blank=True, null=True)
    
    # Permisos
    is_active  = models.BooleanField(default=True)
    is_admin   = models.BooleanField(default=False)

    objects    = ClienteManager()

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['correo', 'nombre']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def direccion_completa(self):
        """Devuelve la dirección completa formateada"""
        if self.calle and self.colonia and self.ciudad:
            partes = [self.calle, self.colonia]
            if self.codigo_postal:
                partes.append(f"CP {self.codigo_postal}")
            partes.extend([self.ciudad, self.estado])
            return ", ".join(filter(None, partes))
        return self.direccion or ""


class Usuario(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    role     = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.username} ({self.role})"


# ——————————————————————————————————————
# Categorías y Productos
# ——————————————————————————————————————

class Categoria(models.Model):
    nombre = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    def __str__(self):
        return self.nombre


class Subcategoria(models.Model):
    """
    Subcategoría para filtrar productos dentro de una categoría específica.
    Permite filtros como: Por género (Dama, Caballero), Por marca, Por promoción, etc.
    
    Ejemplos:
    - Categoría: "Calzado" → Subcategorías: Dama, Caballero, Accesorios
    - Categoría: "Ropa" → Subcategorías: Dama, Caballero, Niños
    - Filtro de promoción: "En Oferta", "Black Friday", "Liquidación"
    - Filtro de marca: "Nike", "Adidas", "Puma", etc.
    """
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=255, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='subcategorias/', blank=True, null=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en filtros")
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['orden', 'nombre']
        unique_together = ('categoria', 'nombre')
        verbose_name = 'Subcategoría'
        verbose_name_plural = 'Subcategorías'
        indexes = [
            models.Index(fields=['categoria', 'activa']),
            models.Index(fields=['nombre']),
        ]
    
    def __str__(self):
        return f"{self.categoria.nombre} - {self.nombre}"


class Producto(models.Model):
    nombre      = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio      = models.DecimalField(max_digits=10, decimal_places=2)
    categoria   = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    subcategorias = models.ManyToManyField(
        Subcategoria, 
        blank=True,
        related_name='productos',
        help_text="Múltiples subcategorías (marca, oferta, línea, etc.)"
    )
    genero      = models.CharField(max_length=50, blank=True, null=True, db_index=True, help_text="Hombre, Mujer, Ambos, etc.")
    precio_mayorista = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    en_oferta   = models.BooleanField(default=False)
    marca       = models.CharField(max_length=100, blank=True, null=True, db_index=True, help_text="Marca del producto para filtros")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    @property
    def stock_total(self):
        """
        Suma el stock de todas sus variantes.
        Útil para mostrar stock global de un producto con variantes.
        """
        return sum( var.stock for var in self.variantes.all() )


class ProductoImagen(models.Model):
    """
    Galería de imágenes para el carrusel del producto.
    Carrusel de máximo 5 imágenes por producto.
    """
    MAX_IMAGENES = 5
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to=producto_imagen_upload_to)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en el carrusel (1-5)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'created_at']
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        constraints = [
            models.UniqueConstraint(
                fields=['producto', 'orden'],
                name='unique_producto_imagen_orden'
            )
        ]

    def __str__(self):
        return f"{self.producto.nombre} - Imagen {self.orden}"
    
    def _generate_image_key(self, filename, imagen_numero):
        """
        Genera una ruta canónica para la imagen de la galería.
        Formato: productos/prod-{id}-{nombre_slug}/imagen-{numero}.{ext}
        Ejemplo: productos/prod-42-nike-air-force/imagen-1.jpg
        """
        import os
        from django.utils.text import slugify
        
        # Esperar a que el producto tenga ID
        if not self.producto.id:
            return f'productos/galeria/{filename}'
        
        ext = os.path.splitext(filename)[1].lower()
        slug = slugify(self.producto.nombre)[:40]  # Limitar a 40 caracteres
        return f'productos/prod-{self.producto.id}-{slug}/imagen-{imagen_numero}{ext}'
    
    def clean(self):
        """
        Valida que no existan más de 5 imágenes por producto.
        Soporta formatos: JPG, PNG, WebP, GIF, AVIF, etc.
        """
        from django.core.exceptions import ValidationError
        
        # Contar imágenes existentes (excluyendo esta si ya existe)
        query = ProductoImagen.objects.filter(producto=self.producto)
        if self.pk:
            query = query.exclude(pk=self.pk)
        
        if query.count() >= self.MAX_IMAGENES:
            raise ValidationError(
                f"El producto '{self.producto.nombre}' ya tiene {self.MAX_IMAGENES} imágenes. "
                f"Máximo permitido: {self.MAX_IMAGENES}. "
                f"Formatos soportados: JPG, PNG, WebP, GIF, AVIF."
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Sincronizar con la primera variante después de guardar
        self._sync_to_first_variant()
    
    def delete(self, *args, **kwargs):
        # Sincronizar antes de eliminar
        self._sync_delete_to_first_variant()
        super().delete(*args, **kwargs)
    
    def _sync_to_first_variant(self):
        """
        Sincroniza esta imagen del producto con la galería de la PRIMERA variante.
        Si no existe una VarianteImagen con el mismo orden en la primera variante, la crea.
        Si ya existe, actualiza la imagen (reemplaza la anterior).
        """
        try:
            # Obtener la primera variante (por ID más bajo)
            primera_variante = self.producto.variantes.order_by('id').first()
            if not primera_variante:
                return  # No hay variantes, nada que sincronizar
            
            # Verificar si esta imagen es diferente (evitar loops infinitos)
            variante_img = VarianteImagen.objects.filter(
                variante=primera_variante,
                orden=self.orden
            ).first()
            
            if variante_img:
                # Si existe y es la misma imagen, no hacer nada
                if variante_img.imagen.name == self.imagen.name:
                    return
                # Si existe pero es diferente, eliminar la anterior y crear nueva
                if variante_img.imagen:
                    variante_img.imagen.delete(save=False)
                variante_img.imagen = self.imagen
                variante_img.save()
            else:
                # No existe, crear nueva
                VarianteImagen.objects.create(
                    variante=primera_variante,
                    imagen=self.imagen,
                    orden=self.orden
                )
        except Exception as e:
            print(f"Error sincronizando imagen a primera variante: {e}")
    
    def _sync_delete_to_first_variant(self):
        """
        Elimina la imagen correspondiente en la primera variante cuando se elimina del producto.
        """
        try:
            primera_variante = self.producto.variantes.order_by('id').first()
            if not primera_variante:
                return
            
            variante_img = VarianteImagen.objects.filter(
                variante=primera_variante,
                orden=self.orden
            ).first()
            
            if variante_img:
                if variante_img.imagen:
                    variante_img.imagen.delete(save=False)
                variante_img.delete()
        except Exception as e:
            print(f"Error eliminando imagen sincronizada en primera variante: {e}")


# ——————————————————————————————————————
# Sistema de variantes simplificado (moda/calzado)
# ——————————————————————————————————————

class Variante(models.Model):
    """
    Variante de producto con talla, color, imagen y atributos extras en JSON.
    Optimizado para e-commerce de moda, calzado y accesorios.
    
    Ejemplos:
    - Zapatos: talla="38", color="Negro", otros={"material": "Piel", "suela": "Goma"}
    - Bolsa: talla="UNICA", color="Rojo", otros={"dimensiones": "35x28x12cm"}
    - Playera: talla="M", color="Blanco", otros={"material": "Algodón 100%"}
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variantes")
    sku = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Código interno o UPC (ej: NIKE-AIR-38-BLK)"
    )
    
    # Campos directos para filtros rápidos
    talla = models.CharField(
        max_length=20, 
        default="UNICA",
        db_index=True,
        help_text="Talla del producto (ej: 38, M, L, UNICA, N/A)"
    )
    color = models.CharField(
        max_length=50, 
        default="N/A",
        db_index=True,
        help_text="Color principal del producto"
    )
    
    # Imagen específica de la variante
    imagen = models.ImageField(
        upload_to='variantes/', 
        blank=True, 
        null=True,
        help_text="Imagen específica de esta variante (ej: talla 38 en color negro)"
    )
    
    # Atributos adicionales en JSON (flexible, sin migraciones)
    otros = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Atributos extras en JSON: material, dimensiones, peso, etc."
    )
    
    # Imagen específica de la variante
    imagen = models.ImageField(
        upload_to='variantes/',
        blank=True,
        null=True,
        help_text="Imagen específica de esta variante (color/talla específica)"
    )
    
    # Precio y stock
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True, 
        null=True,
        help_text="Precio específico de esta variante (si difiere del producto base)"
    )
    precio_mayorista = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Precio para clientes mayoristas"
    )
    stock = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Cantidad disponible en inventario"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['talla', 'color', 'stock']),
            models.Index(fields=['producto', 'stock']),
        ]
        ordering = ['talla', 'color']
    
    def __str__(self):
        """Representación legible: Producto (Talla: X, Color: Y)"""
        partes = []
        if self.talla and self.talla != "UNICA":
            partes.append(f"Talla: {self.talla}")
        if self.color and self.color != "N/A":
            partes.append(f"Color: {self.color}")
        
        if partes:
            return f"{self.producto.nombre} ({', '.join(partes)})"
        return f"{self.producto.nombre}"
    
    @property
    def precio_final(self):
        """Retorna el precio de la variante o del producto base"""
        return self.precio if self.precio else self.producto.precio
    
    @property
    def precio_mayorista_final(self):
        """Retorna el precio mayorista de la variante o del producto base"""
        return self.precio_mayorista if self.precio_mayorista else self.producto.precio_mayorista
    
    @property
    def disponible(self):
        """Indica si hay stock disponible"""
        return self.stock > 0
    
    def reducir_stock(self, cantidad):
        """Reduce el stock de manera segura"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        return False
    
    def aumentar_stock(self, cantidad):
        """Aumenta el stock"""
        self.stock += cantidad
        self.save()
    
    def _generate_image_key(self, filename):
        """
        Genera una clave canónica para la imagen de la variante
        Formato: variantes/var-{producto_id}-{variante_id}-{talla}-{color}-{slug}.{ext}
        Ejemplo: variantes/var-42-156-38-negro-nike-air-force.jpg
        
        Esto asegura:
        - No hay solapación con otras variantes
        - Nombre descriptivo y único
        - Fácil de encontrar en S3
        """
        import os
        from django.utils.text import slugify
        
        # Esperar a que la variante tenga ID
        if not self.id:
            return f'variantes/{filename}'
        
        ext = os.path.splitext(filename)[1].lower()
        producto_slug = slugify(self.producto.nombre)[:30]
        talla_clean = slugify(self.talla or "unica")[:10]
        color_clean = slugify(self.color or "na")[:10]
        
        return f'variantes/var-{self.producto_id}-{self.id}-{talla_clean}-{color_clean}-{producto_slug}{ext}'


class VarianteImagen(models.Model):
    """
    Galería de imágenes para el carrusel de cada variante.
    Carrusel de máximo 5 imágenes por variante (combinación talla/color).
    Útil para mostrar la misma variante desde diferentes ángulos.
    """
    MAX_IMAGENES = 5
    
    variante = models.ForeignKey(Variante, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(
        upload_to=variante_imagen_upload_to,
        help_text="Imagen de la variante desde diferentes ángulos"
    )
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en el carrusel (1-5)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'created_at']
        verbose_name = 'Imagen de Variante'
        verbose_name_plural = 'Imágenes de Variantes'
        constraints = [
            models.UniqueConstraint(
                fields=['variante', 'orden'],
                name='unique_variante_imagen_orden'
            )
        ]

    def __str__(self):
        return f"{self.variante} - Imagen {self.orden}"
    
    def _generate_image_key(self, filename, imagen_numero):
        """
        Genera una ruta canónica para la imagen de la galería de variante.
        Formato: variantes/var-{prod-id}-{var-id}-{talla}-{color}/imagen-{numero}.{ext}
        Ejemplo: variantes/var-42-123-40-negro/imagen-1.jpg
        """
        import os
        from django.utils.text import slugify
        
        # Esperar a que la variante tenga ID
        if not self.variante.id:
            return f'variantes/galeria/{filename}'
        
        ext = os.path.splitext(filename)[1].lower()
        producto_slug = slugify(self.variante.producto.nombre)[:30]
        talla_clean = slugify(self.variante.talla or "unica")[:10]
        color_clean = slugify(self.variante.color or "na")[:10]
        
        return f'variantes/var-{self.variante.producto_id}-{self.variante.id}-{talla_clean}-{color_clean}/imagen-{imagen_numero}{ext}'
    
    def clean(self):
        """
        Valida que no existan más de 5 imágenes por variante.
        Soporta formatos: JPG, PNG, WebP, GIF, AVIF, etc.
        """
        from django.core.exceptions import ValidationError
        
        # Contar imágenes existentes (excluyendo esta si ya existe)
        query = VarianteImagen.objects.filter(variante=self.variante)
        if self.pk:
            query = query.exclude(pk=self.pk)
        
        if query.count() >= self.MAX_IMAGENES:
            raise ValidationError(
                f"La variante '{self.variante}' ya tiene {self.MAX_IMAGENES} imágenes. "
                f"Máximo permitido: {self.MAX_IMAGENES}. "
                f"Formatos soportados: JPG, PNG, WebP, GIF, AVIF."
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Sincronizar con el producto si es la primera variante
        self._sync_to_producto()
    
    def delete(self, *args, **kwargs):
        # Sincronizar antes de eliminar
        self._sync_delete_to_producto()
        super().delete(*args, **kwargs)
    
    def _sync_to_producto(self):
        """
        Sincroniza esta imagen con el producto SOLO si la variante es la PRIMERA (por ID más bajo).
        Si la variante no es la primera, no hace nada.
        """
        try:
            # Verificar si esta variante es la primera del producto
            primera_variante = self.variante.producto.variantes.order_by('id').first()
            if not primera_variante or primera_variante.id != self.variante.id:
                return  # Esta no es la primera variante, nada que sincronizar
            
            # Esta SÍ es la primera variante, sincronizar con el producto
            producto = self.variante.producto
            
            # Verificar si ya existe una imagen con este orden en el producto
            producto_img = ProductoImagen.objects.filter(
                producto=producto,
                orden=self.orden
            ).first()
            
            if producto_img:
                # Si existe y es la misma imagen, no hacer nada
                if producto_img.imagen.name == self.imagen.name:
                    return
                # Si existe pero es diferente, actualizar
                if producto_img.imagen:
                    producto_img.imagen.delete(save=False)
                producto_img.imagen = self.imagen
                producto_img.save()
            else:
                # No existe, crear nueva
                ProductoImagen.objects.create(
                    producto=producto,
                    imagen=self.imagen,
                    orden=self.orden
                )
        except Exception as e:
            print(f"Error sincronizando imagen a producto desde primera variante: {e}")
    
    def _sync_delete_to_producto(self):
        """
        Elimina la imagen correspondiente del producto cuando se elimina de la primera variante.
        """
        try:
            # Verificar si esta variante es la primera del producto
            primera_variante = self.variante.producto.variantes.order_by('id').first()
            if not primera_variante or primera_variante.id != self.variante.id:
                return  # Esta no es la primera variante, nada que sincronizar
            
            producto = self.variante.producto
            
            producto_img = ProductoImagen.objects.filter(
                producto=producto,
                orden=self.orden
            ).first()
            
            if producto_img:
                if producto_img.imagen:
                    producto_img.imagen.delete(save=False)
                producto_img.delete()
        except Exception as e:
            print(f"Error eliminando imagen sincronizada en producto desde primera variante: {e}")

# ——————————————————————————————————————
# Carrito, Wishlist y Órdenes
# ——————————————————————————————————————

class Carrito(models.Model):
    # 📌  cliente puede ser NULL / opcional
    cliente     = models.ForeignKey(
        Cliente,
        null=True, blank=True,               # ahora es opcional
        on_delete=models.CASCADE,
        related_name="carritos"              # puedes dejarlo sin related_name si prefieres
    )
    # 📌  nuevo campo para invitados
    session_key = models.CharField(
        max_length=40,
        null=True, blank=True,
        db_index=True
    )

    status      = models.CharField(max_length=50, default="vacio")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        usuario = self.cliente.username if self.cliente else "Invitado"
        return f"Carrito de {usuario} ({self.status})"

class CarritoProducto(models.Model):
    carrito  = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    variante = models.ForeignKey(Variante, on_delete=models.CASCADE)
    cantidad  = models.PositiveIntegerField(default=1)
    def __str__(self):
        return f"{self.variante} en {self.carrito}"

class Wishlist(models.Model):
    cliente   = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    productos = models.ManyToManyField(Producto, blank=True, related_name='wishlists')

    def __str__(self):
        # Listamos los nombres de todos los productos en la wishlist
        nombres = ", ".join(p.nombre for p in self.productos.all())
        return f"{self.cliente.username} quiere {nombres}"

class Orden(models.Model):
    carrito             = models.OneToOneField(Carrito, on_delete=models.CASCADE)
    cliente             = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    total_amount        = models.DecimalField(max_digits=10, decimal_places=2)
    status              = models.CharField(max_length=50)
    payment_method      = models.CharField(max_length=50)
    conekta_order_id    = models.CharField(max_length=100, blank=True, null=True)
    conekta_charge_id   = models.CharField(max_length=100, blank=True, null=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Orden #{self.id} - {self.cliente.username}"

class OrdenDetalle(models.Model):
    order          = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="detalles")
    variante       = models.ForeignKey(Variante, on_delete=models.CASCADE)
    cantidad       = models.IntegerField()
    precio_unitario= models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}×{self.variante} en Orden #{self.order.id}"


# ——————————————————————————————————————
# Contacto de clientes
# ——————————————————————————————————————

class ContactoCliente(models.Model):
    cliente    = models.OneToOneField(Cliente, on_delete=models.CASCADE, primary_key=True)
    nombre     = models.CharField(max_length=255)
    email      = models.CharField(max_length=255)
    mensaje    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contacto de {self.cliente.username}"


class BlacklistedToken(models.Model):
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted at {self.created_at}"
