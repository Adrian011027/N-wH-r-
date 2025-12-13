from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

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

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre      = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio      = models.DecimalField(max_digits=10, decimal_places=2)
    categoria   = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    genero      = models.CharField(max_length=50)
    precio_mayorista = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    en_oferta   = models.BooleanField(default=False)
    imagen      = models.ImageField(upload_to='productos/', blank=True, null=True)
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
    
    def _generate_image_key(self, filename):
        """
        Genera una clave canónica para la imagen del producto
        Formato: productos/prod-{id}-{nombre_slug}.{ext}
        Ejemplo: productos/prod-42-nike-air-force-negra.jpg
        """
        import os
        from django.utils.text import slugify
        
        # Esperar a que el producto tenga ID
        if not self.id:
            return f'productos/{filename}'
        
        ext = os.path.splitext(filename)[1].lower()
        slug = slugify(self.nombre)[:50]  # Limitar a 50 caracteres
        return f'productos/prod-{self.id}-{slug}{ext}'


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
    carrito        = models.OneToOneField(Carrito, on_delete=models.CASCADE)
    cliente        = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    total_amount   = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    created_at     = models.DateTimeField(auto_now_add=True)

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
