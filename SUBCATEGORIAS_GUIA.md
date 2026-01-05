# 📋 Guía de Subcategorías - Sistema de Filtros Avanzados

## Resumen de Cambios Realizados

Se ha implementado un **nuevo sistema de Subcategorías** para reemplazar el filtro de género anterior. Esto permite un filtrado mucho más flexible y escalable de productos.

---

## 🆕 Cambios en los Modelos

### 1. **Nuevo Modelo: `Subcategoria`**

```python
class Subcategoria(models.Model):
    """
    Subcategoría para filtrar productos dentro de una categoría específica.
    Permite filtros como: Por género (Dama, Caballero), Por marca, Por promoción, etc.
    """
    categoria          # FK a Categoria
    nombre             # ej: "Dama", "Caballero", "Nike", "En Oferta"
    descripcion        # Texto descriptivo (opcional)
    imagen             # Imagen para mostrar en filtros (opcional)
    orden              # Posición en la lista (default: 0)
    activa             # Si está activo o no
    created_at         # Fecha de creación
    updated_at         # Última actualización
```

**Ejemplo de uso:**
```
Categoría: "Calzado"
├── Subcategoría: "Dama" (orden: 1)
├── Subcategoría: "Caballero" (orden: 2)
├── Subcategoría: "Niños" (orden: 3)
└── Subcategoría: "En Oferta" (orden: 4)

Categoría: "Ropa"
├── Subcategoría: "Dama"
├── Subcategoría: "Caballero"
└── Subcategoría: "Oferta Navidad"
```

### 2. **Actualizaciones en Modelo `Producto`**

Se agregaron 2 campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `subcategoria` | ForeignKey (Subcategoria) | Relación con subcategoría para filtrados avanzados |
| `marca` | CharField | Nueva campo para filtrar por marca (Nike, Adidas, etc.) |
| `genero` | CharField (DEPRECATED) | Mantenido para compatibilidad, pero opcional ahora |

---

## 🔌 Nuevos Endpoints API

### 📍 **GET** `/api/subcategorias/`
Obtener todas las subcategorías

**Parámetros:**
- `categoria_id` (opcional): Filtrar por categoría
- `activas` (true/false, default: true): Mostrar solo subcategorías activas

**Ejemplo:**
```bash
GET /api/subcategorias/?categoria_id=1&activas=true
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Dama",
    "descripcion": "Productos para mujeres",
    "categoria_id": 1,
    "categoria_nombre": "Calzado",
    "imagen": "https://...",
    "orden": 1,
    "activa": true,
    "productos_count": 45,
    "created_at": "2026-01-04T10:30:00"
  }
]
```

---

### 📍 **POST** `/api/subcategorias/crear/`
Crear una nueva subcategoría (requiere admin)

**Body:**
```json
{
  "nombre": "Dama",
  "categoria_id": 1,
  "descripcion": "Productos para mujeres",
  "orden": 1,
  "activa": true
}
```

---

### 📍 **PUT/PATCH** `/api/subcategorias/actualizar/<id>/`
Actualizar una subcategoría (requiere admin)

**Body (todos los campos opcionales):**
```json
{
  "nombre": "Damas",
  "descripcion": "Nueva descripción",
  "orden": 2,
  "activa": false
}
```

---

### 📍 **DELETE** `/api/subcategorias/eliminar/<id>/`
Eliminar una subcategoría (requiere admin)

Los productos asociados mantendrán su categoría pero perderán la referencia a la subcategoría.

---

### 📍 **GET** `/api/categorias/<categoria_id>/subcategorias/`
Obtener todas las subcategorías de una categoría específica

**Parámetros:**
- `incluir_inactivas` (true/false, default: false)

**Respuesta:**
```json
{
  "categoria_id": 1,
  "categoria_nombre": "Calzado",
  "subcategorias": [
    {
      "id": 1,
      "nombre": "Dama",
      "descripcion": "Productos para mujeres",
      "imagen": "https://...",
      "orden": 1,
      "activa": true,
      "productos_count": 45
    }
  ]
}
```

---

## 🔍 Búsqueda Mejorada: `/api/search/`

Se ha mejorado significativamente el endpoint de búsqueda con soporte para:

### Parámetros nuevos:
| Parámetro | Ejemplo | Descripción |
|-----------|---------|-------------|
| `subcategoria` | `1` o `"Dama"` | Filtrar por subcategoría (ID o nombre) |
| `marca` | `"Nike"` | Filtrar por marca exacta |
| `colores` | `"Negro,Blanco,Rojo"` | Filtrar por colores (lista separada por coma) |

### Parámetros existentes mejorados:
| Parámetro | Ejemplo |
|-----------|---------|
| `genero` | `"M"`, `"H"`, `"UNISEX"`, `"U"` (ahora acepta "U" como alias de "UNISEX") |

### Ejemplo de búsqueda completa:
```bash
GET /api/search/?q=zapatos&categoria=1&subcategoria=1&marca=Nike&precio_min=500&precio_max=2000&tallas=38,39&colores=Negro,Blanco&en_oferta=true&ordenar=precio_asc&page=1&per_page=20
```

### Respuesta mejorada:
```json
{
  "productos": [
    {
      "id": 1,
      "nombre": "Nike Air Force 1",
      "precio": 1500.00,
      "categoria": "Calzado",
      "categoria_id": 1,
      "subcategoria": "Dama",
      "subcategoria_id": 1,
      "marca": "Nike",
      "en_oferta": true,
      "tallas_disponibles": ["36", "37", "38", "39"],
      "colores_disponibles": ["Negro", "Blanco", "Rojo"],
      "variantes": [...]
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

---

## 📊 Endpoint de Opciones de Filtro: `/api/search/filters/`

Obtiene todas las opciones disponibles para los filtros dinámicos.

**Parámetros:**
- `categoria_id` (opcional): Limitar opciones a una categoría específica

**Respuesta:**
```json
{
  "categorias": [
    {"id": 1, "nombre": "Calzado"},
    {"id": 2, "nombre": "Ropa"}
  ],
  "subcategorias": [
    {"id": 1, "nombre": "Dama", "categoria_id": 1},
    {"id": 2, "nombre": "Caballero", "categoria_id": 1}
  ],
  "precio_min": 100.00,
  "precio_max": 5000.00,
  "tallas": ["25", "26", "27", "M", "L", "XL"],
  "colores": ["Negro", "Blanco", "Rojo", "Azul"],
  "marcas": ["Nike", "Adidas", "Puma", "Reebok"],
  "generos": ["M", "H", "UNISEX"]
}
```

---

## 🛠️ Pasos para Implementar

### 1. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Crear Subcategorías (Desde Admin o API)

**Opción A: Desde Admin Django:**
```
Admin Panel → Subcategorías → Agregar
```

**Opción B: Desde API:**
```bash
POST /api/subcategorias/crear/
{
  "nombre": "Dama",
  "categoria_id": 1,
  "descripcion": "Productos para mujeres",
  "orden": 1,
  "activa": true
}
```

### 3. Actualizar Productos

Ahora los productos pueden tener:
- `categoria` (FK) → obligatorio
- `subcategoria` (FK) → opcional pero recomendado para filtros
- `marca` → opcional
- `genero` → mantener solo por compatibilidad

**Ejemplo:**
```python
from store.models import Producto, Subcategoria

subcategoria = Subcategoria.objects.get(nombre="Dama")
producto = Producto.objects.get(id=1)
producto.subcategoria = subcategoria
producto.marca = "Nike"
producto.save()
```

---

## 🐛 Solución: El filtro de género NO funcionaba

### ❌ **Problema Original:**
1. El endpoint de búsqueda esperaba `genero=UNISEX` pero en realidad los productos tienen `genero="U"` o `genero="M"` / `genero="H"`
2. No había un sistema robusto de filtros además del género
3. No se podía filtrar por marca, promoción, etc.

### ✅ **Solución Implementada:**
1. Se creó un sistema de **Subcategorías** que reemplaza al género como filtro principal
2. Se agregó soporte para filtrar por **marca**
3. Se mejoró el endpoint de búsqueda para aceptar `genero` con valores correctos: `M`, `H`, `UNISEX`, o `U`
4. Se mantiene compatibilidad con código existente pero se recomienda usar `subcategoria` para nuevas implementaciones

### 📝 **Migración de código existente:**

**Antes:**
```bash
GET /api/search/?genero=M
```

**Ahora (mejorado):**
```bash
# Opción 1: Usar el antiguo sistema (aún funciona)
GET /api/search/?genero=M

# Opción 2: Usar el nuevo sistema (recomendado)
GET /api/search/?subcategoria=1  # donde 1 es el ID de "Dama"

# Opción 3: Combinar ambos
GET /api/search/?subcategoria=1&marca=Nike&colores=Negro&precio_min=500
```

---

## 📚 Archivo de Migraciones

Se genera automáticamente al ejecutar `makemigrations`. Contendrá:

```python
# Crear tabla Subcategoria
class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_...'),  # última migración anterior
    ]

    operations = [
        # Crear modelo Subcategoria
        migrations.CreateModel(
            name='Subcategoria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(db_index=True, max_length=255)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('imagen', models.ImageField(blank=True, null=True, upload_to='subcategorias/')),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden de aparición en filtros')),
                ('activa', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategorias', to='store.categoria')),
            ],
            options={
                'verbose_name': 'Subcategoría',
                'verbose_name_plural': 'Subcategorías',
                'ordering': ['orden', 'nombre'],
            },
        ),
        
        # Agregar campos a Producto
        migrations.AddField(
            model_name='producto',
            name='subcategoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='productos', to='store.subcategoria'),
        ),
        migrations.AddField(
            model_name='producto',
            name='marca',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        # Hacer genero opcional
        migrations.AlterField(
            model_name='producto',
            name='genero',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
```

---

## 🎯 Casos de Uso

### Caso 1: Filtrar por género (forma antigua)
```bash
GET /api/search/?genero=M
```

### Caso 2: Filtrar por subcategoría específica
```bash
GET /api/search/?subcategoria=3  # ID 3 = "En Oferta"
```

### Caso 3: Filtrar por marca
```bash
GET /api/search/?marca=Nike
```

### Caso 4: Búsqueda compleja
```bash
GET /api/search/?categoria=1&subcategoria=1&marca=Nike&precio_min=1000&precio_max=3000&en_oferta=true&ordenar=precio_asc
```

### Caso 5: Obtener filtros dinámicos
```bash
GET /api/search/filters/?categoria_id=1
```
Devuelve todas las subcategorías, marcas, tallas y colores disponibles en la categoría "Calzado".

---

## 🔐 Seguridad

- Todos los endpoints de **creación/actualización/eliminación** requieren que el usuario sea **admin** (`@admin_required()`)
- Los endpoints de **lectura** son públicos
- Se validan todos los inputs JSON

---

## 📱 Ejemplo de Uso en Frontend

```javascript
// Obtener filtros disponibles
async function getFilterOptions(categoryId = null) {
  const url = '/api/search/filters/' + (categoryId ? `?categoria_id=${categoryId}` : '');
  const response = await fetch(url);
  return await response.json();
}

// Buscar productos con filtros
async function searchProducts(params) {
  const queryString = new URLSearchParams(params).toString();
  const response = await fetch(`/api/search/?${queryString}`);
  return await response.json();
}

// Ejemplo de uso
const filters = await getFilterOptions(1); // Filtros de categoría 1
console.log('Subcategorías disponibles:', filters.subcategorias);
console.log('Marcas disponibles:', filters.marcas);

const results = await searchProducts({
  subcategoria: 1,
  marca: 'Nike',
  precio_min: 1000,
  precio_max: 3000,
  ordenar: 'precio_asc'
});
```

---

## ✅ Checklist de Implementación

- [x] Crear modelo `Subcategoria`
- [x] Agregar campos a modelo `Producto`
- [x] Crear vistas CRUD para subcategorías
- [x] Crear endpoints API para subcategorías
- [x] Mejorar búsqueda con nuevos filtros
- [x] Agregar endpoint de opciones de filtro
- [x] Mantener compatibilidad hacia atrás con `genero`
- [x] Documentar cambios
- [ ] Ejecutar migraciones: `python manage.py migrate`
- [ ] Crear subcategorías iniciales en admin
- [ ] Asignar subcategorías a productos existentes
- [ ] Actualizar frontend para usar nuevos filtros

---

## 📞 Preguntas Frecuentes

**P: ¿Se pierden los datos de género existentes?**
R: No, el campo `genero` se mantiene como opcional. Los productos existentes no se modifican, pero se recomienda migrar a `subcategoria` gradualmente.

**P: ¿Puedo tener un producto sin subcategoría?**
R: Sí, el campo es opcional. Pero para que aparezca en filtros de subcategoría debe tenerlo asignado.

**P: ¿Cómo migro productos con genero="M" a una subcategoría "Dama"?**
```python
from store.models import Producto, Subcategoria

subcategoria_dama = Subcategoria.objects.get(nombre="Dama")
productos = Producto.objects.filter(genero="M")
for p in productos:
    p.subcategoria = subcategoria_dama
    p.save()
```

**P: ¿Qué pasa si elimino una subcategoría?**
R: Los productos pierden la referencia a esa subcategoría (se asigna NULL) pero conservan su categoría padre. No se eliminan productos.

---

## 🚀 Próximos Pasos Recomendados

1. Ejecutar migraciones
2. Crear estructura de subcategorías en el Admin
3. Asignar subcategorías a productos existentes
4. Actualizar templates frontend para usar nuevos filtros
5. Probar API con ejemplos proporcionados
6. Eliminar progresivamente uso de campo `genero` en código nuevo

