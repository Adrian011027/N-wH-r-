# 🔍 Sistema de Búsqueda y Filtros - NöwHėrē

## 📋 Descripción

Sistema completo de búsqueda y filtrado de productos con interfaz intuitiva y API RESTful.

---

## ✨ Características Implementadas

### 🎯 Búsqueda
- ✅ Búsqueda por nombre de producto
- ✅ Búsqueda por descripción
- ✅ Búsqueda en tiempo real (opcional)
- ✅ Búsqueda con botón y Enter

### 🎨 Filtros Disponibles
- ✅ **Por Categoría**: Todas las categorías disponibles
- ✅ **Por Género**: Mujer, Hombre, Unisex
- ✅ **Por Precio**: Rango mínimo y máximo con sliders interactivos
- ✅ **Por Tallas**: Selección múltiple de tallas disponibles
- ✅ **Por Disponibilidad**: 
  - Solo productos en stock
  - Solo productos en oferta
  
### 📊 Ordenamiento
- 🆕 Más recientes
- 💰 Precio: Menor a mayor
- 💰 Precio: Mayor a menor
- 🔤 Nombre: A-Z
- 🔤 Nombre: Z-A

### 📄 Paginación
- ✅ 20 productos por página (configurable)
- ✅ Navegación anterior/siguiente
- ✅ Indicador de página actual

---

## 🌐 Endpoints API

### 1. **Buscar y Filtrar Productos**
```http
GET /api/search/
```

**Parámetros Query:**
| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `q` | string | Término de búsqueda | `?q=nike` |
| `categoria` | int/string | ID o nombre de categoría | `?categoria=1` |
| `genero` | string | M, H, UNISEX | `?genero=M` |
| `precio_min` | decimal | Precio mínimo | `?precio_min=500` |
| `precio_max` | decimal | Precio máximo | `?precio_max=2000` |
| `en_oferta` | boolean | Solo en oferta | `?en_oferta=true` |
| `tallas` | string | Tallas separadas por coma | `?tallas=25,26,27` |
| `disponibles` | boolean | Solo con stock | `?disponibles=true` |
| `ordenar` | string | Tipo de orden | `?ordenar=precio_asc` |
| `page` | int | Número de página | `?page=2` |
| `per_page` | int | Productos por página | `?per_page=20` |

**Valores de ordenamiento:**
- `nuevo` - Más recientes
- `precio_asc` - Precio ascendente
- `precio_desc` - Precio descendente
- `nombre_asc` - Nombre A-Z
- `nombre_desc` - Nombre Z-A
- `popular` - Más populares

**Ejemplo de request:**
```bash
GET /api/search/?q=tenis&categoria=1&genero=M&precio_min=500&precio_max=1500&tallas=25,26&en_oferta=true&ordenar=precio_asc&page=1
```

**Respuesta exitosa (200):**
```json
{
  "productos": [
    {
      "id": 1,
      "nombre": "Air Force 1",
      "descripcion": "Tenis clásicos",
      "precio": 1299.99,
      "precio_mayorista": 999.99,
      "categoria": "Tenis",
      "categoria_id": 1,
      "genero": "M",
      "en_oferta": true,
      "imagen": "/media/productos/airforce.jpg",
      "tallas_disponibles": ["25", "26", "27"],
      "stock_total": 15,
      "variantes": [
        {
          "id": 1,
          "talla": "25",
          "precio": 1299.99,
          "stock": 5,
          "atributos": {
            "Talla": "25"
          }
        }
      ]
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "total_pages": 3,
  "has_next": true,
  "has_prev": false
}
```

---

### 2. **Obtener Opciones de Filtros**
```http
GET /api/search/filters/
```

**Respuesta (200):**
```json
{
  "categorias": [
    {"id": 1, "nombre": "Tenis"},
    {"id": 2, "nombre": "Botas"}
  ],
  "precio_min": 299.0,
  "precio_max": 3999.0,
  "tallas": ["23", "24", "25", "26", "27", "28"],
  "generos": ["M", "H", "UNISEX"]
}
```

---

### 3. **Página de Búsqueda (HTML)**
```http
GET /buscar/
```

Renderiza el template completo con la interfaz de búsqueda y filtros.

---

## 💻 Uso del Frontend

### Acceso a la Página
```html
<!-- Desde el header -->
<a href="{% url 'search_page' %}">Buscar</a>

<!-- O directamente -->
http://localhost:8000/buscar/
```

### Búsqueda Programática (JavaScript)
```javascript
// Cargar productos con filtros específicos
const params = new URLSearchParams({
  q: 'nike',
  categoria: '1',
  genero: 'M',
  precio_min: '500',
  precio_max: '2000',
  tallas: '25,26,27',
  ordenar: 'precio_asc',
  page: 1
});

const response = await fetch(`/api/search/?${params.toString()}`);
const data = await response.json();

console.log(data.productos); // Array de productos
console.log(data.total);     // Total de resultados
```

---

## 🎨 Personalización CSS

El archivo `static/public/busqueda/css/search.css` contiene todas las clases:

```css
/* Cambiar color principal */
.search-btn,
.btn-apply {
  background: #tu-color; /* Cambiar #1D1D1D */
}

/* Ajustar grid de productos */
.productos-grid {
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  /* Cambiar 250px por el tamaño deseado */
}
```

---

## 📱 Responsive

### Desktop (> 992px)
- Sidebar fijo a la izquierda
- Grid de 4-5 columnas

### Tablet (768px - 992px)
- Sidebar oculto, activable con botón
- Grid de 3 columnas

### Mobile (< 768px)
- Sidebar como overlay
- Grid de 2 columnas
- Filtros más compactos

---

## 🔧 Configuración Avanzada

### Cambiar Productos por Página
```javascript
// En search.js, línea 19
per_page: 20  // Cambiar a 12, 24, 30, etc.
```

### Habilitar Búsqueda en Tiempo Real
```javascript
// En search.js, descomentar línea 82
searchInput.addEventListener('input', (e) => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    performSearch(); // ← Descomentar esta línea
  }, 500);
});
```

### Agregar Más Opciones de Ordenamiento
```python
# En store/views/search.py, agregar en la sección de ORDENAMIENTO
elif ordenar == 'mas_vendido':
    productos = productos.annotate(
        ventas_count=Count('ordendetalle')
    ).order_by('-ventas_count')
```

---

## 🧪 Testing

### Test Manual con REST Client

Crear archivo `test-search.http`:

```http
### Búsqueda simple
GET http://localhost:8000/api/search/?q=tenis

### Búsqueda con filtros múltiples
GET http://localhost:8000/api/search/?q=nike&categoria=1&genero=M&precio_min=500&precio_max=2000&tallas=25,26&ordenar=precio_asc

### Obtener opciones de filtros
GET http://localhost:8000/api/search/filters/

### Búsqueda solo en oferta
GET http://localhost:8000/api/search/?en_oferta=true&ordenar=precio_desc

### Paginación
GET http://localhost:8000/api/search/?page=2&per_page=10
```

---

## 🚀 Próximas Mejoras

### Funcionalidades Sugeridas
- [ ] Búsqueda por voz
- [ ] Autocompletado de búsqueda
- [ ] Historial de búsquedas
- [ ] Búsquedas guardadas
- [ ] Comparador de productos
- [ ] Vista de lista vs grid
- [ ] Filtro por color
- [ ] Filtro por material
- [ ] Búsqueda por imagen
- [ ] Recomendaciones basadas en búsqueda

### Optimizaciones
- [ ] Cache de resultados frecuentes
- [ ] Elasticsearch para búsqueda avanzada
- [ ] Índice full-text en PostgreSQL
- [ ] Lazy loading de imágenes
- [ ] Infinite scroll
- [ ] Service Worker para offline

---

## 📚 Archivos Creados

```
store/
├── views/
│   └── search.py              # Lógica de búsqueda y filtros
├── urls.py                    # Rutas agregadas
│
templates/
└── public/
    └── busqueda/
        └── search.html        # Template principal
│
static/
└── public/
    └── busqueda/
        ├── css/
        │   └── search.css     # Estilos
        └── js/
            └── search.js      # Lógica frontend
```

---

## 🐛 Troubleshooting

### Problema: No se muestran productos
**Solución:** Verificar que existan productos con `stock > 0` en variantes

### Problema: Filtros no aplican
**Solución:** Abrir consola del navegador (F12) y verificar errores

### Problema: Imágenes no cargan
**Solución:** Verificar `MEDIA_URL` y `MEDIA_ROOT` en `settings.py`

### Problema: Error 500 en API
**Solución:** Revisar logs del servidor Django

```bash
python manage.py runserver
# Revisar terminal para ver traceback
```

---

## 📞 Soporte

Para dudas o problemas:
1. Revisar la consola del navegador (F12)
2. Revisar logs del servidor Django
3. Verificar que todas las migraciones estén aplicadas:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

---

## ✅ Checklist de Implementación

- [x] Vista de búsqueda en backend
- [x] Endpoint API `/api/search/`
- [x] Endpoint `/api/search/filters/`
- [x] Template HTML responsive
- [x] CSS completo con responsive
- [x] JavaScript con todos los filtros
- [x] Paginación funcional
- [x] Integración en header
- [x] Documentación completa

---

**¡Sistema de búsqueda listo para usar! 🎉**
