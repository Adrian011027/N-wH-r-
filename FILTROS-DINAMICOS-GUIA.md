# 🎯 SISTEMA DE FILTROS DINÁMICOS - GUÍA COMPLETA

## ✅ Cambios Implementados

### 1️⃣ **Base de Datos (Models)**
- ✅ Cambio de FK a M2M: `Producto.subcategoria` → `Producto.subcategorias`
- ✅ Ahora un producto puede tener múltiples subcategorías
- ✅ Historial compatible mantenido

### 2️⃣ **API Endpoints (Backend)**

```
GET /api/categorias-por-genero/?genero=hombre
→ Retorna todas las categorías con productos de ese género

GET /api/subcategorias-por-categoria/?categoria_id=1&genero=hombre
→ Retorna subcategorías de esa categoría con productos del género

GET /api/productos-filtrados/?genero=hombre&categoria_id=1&subcategorias=1,2,3
→ Retorna productos filtrados por todos los criterios
```

### 3️⃣ **Frontend (JavaScript + CSS)**
- ✅ `filtros-dinamicos.js` - Lógica de interacción
- ✅ `filtros-dinamicos.css` - Estilos completos
- ✅ `filtros-dinamicos.html` - Estructura HTML reutilizable
- ✅ Integrado en `base.html`

---

## 📋 INSTRUCCIONES PARA USAR

### **Paso 1: Hacer las migraciones**

```bash
cd C:\Users\jonae\desktop\N-wH-r-
python manage.py makemigrations store
python manage.py migrate
```

El sistema creará automáticamente la tabla intermedia `producto_subcategorias`.

### **Paso 2: Incluir el HTML en tu página**

En cualquier template (ej: `templates/public/catalogo/index.html`):

```django
{% extends "public/base.html" %}

{% block content %}
  <div class="container">
    <!-- INCLUIR LOS FILTROS -->
    {% include "public/includes/filtros-dinamicos.html" %}
  </div>
{% endblock %}
```

**¡Eso es todo!** El JavaScript y CSS ya están incluidos en `base.html`.

### **Paso 3: Verificar que funciona**

1. Navega a tu página que incluye los filtros
2. Deberías ver:
   - ✅ Selector de género (dropdown)
   - ✅ Botones de categorías que se cargan dinámicamente
   - ✅ Checkboxes de subcategorías al seleccionar categoría
   - ✅ Productos listados al seleccionar subcategorías
   - ✅ Pills mostrando filtros activos

---

## 🔄 FLUJO DE USUARIO

```
1. Usuario abre la página
   ↓
2. Selecciona género (Hombre/Mujer/Ambos)
   ↓
3. Se cargan categorías disponibles para ese género
   ↓
4. Selecciona una categoría (Calzado, Bolsas, etc.)
   ↓
5. Se despliegansubcategorías de esa categoría
   ↓
6. Selecciona una o varias subcategorías (Nike, Adidas, En Oferta)
   ↓
7. Se muestran productos filtrados
```

---

## 📊 EJEMPLO DE CONSULTA

**Scenario:** Un usuario quiere ver calzado para hombre, de marcas Nike y Adidas

```javascript
// Frontend automáticamente hace esto:
GET /api/productos-filtrados/?genero=hombre&categoria_id=1&subcategorias=5,6

// Respuesta:
{
  "filtros": {
    "genero": "hombre",
    "categoria_id": "1",
    "subcategorias": ["5", "6"]
  },
  "total": 24,
  "productos": [
    {
      "id": 1,
      "nombre": "Nike Air Max 90",
      "precio": 4500,
      "en_oferta": true,
      "imagen": "...",
      "genero": "hombre",
      "categoria": "Calzado",
      "subcategorias": ["Nike", "Oferta Especial"]
    },
    ...
  ]
}
```

---

## 🎨 PERSONALIZACIÓN DE ESTILOS

El CSS ya está optimizado, pero si quieres cambiar colores:

En `static/public/css/filtros-dinamicos.css`:

```css
/* Cambiar color principal */
[data-genero-selector]:focus,
.categoria-btn.active,
.checkbox-item input[type="checkbox"] {
  /* Cambiar #007bff por tu color */
}
```

---

## 🔧 SI ALGO NO FUNCIONA

### Error: "No se pueden cargar las categorías"
- Verificar que los endpoints estén registrados en `urls.py`
- Verificar que `Producto` tenga registro con `genero` asignado

### Error: "Tabla no existe"
```bash
python manage.py migrate store --fake-initial  # Si es la primera vez
python manage.py migrate store                  # Ejecutar migraciones
```

### Los productos no se muestran
- Verificar que los productos tengan:
  - `genero` asignado (hombre, mujer, ambos)
  - `categoria` asignada
  - `subcategorias` asignadas (al menos una)

---

## 📱 RESPONSIVE

El sistema es completamente responsive:
- ✅ Desktop (>768px): Grid de 4 columnas de productos
- ✅ Tablet (480-768px): Grid de 3 columnas
- ✅ Mobile (<480px): Grid de 2 columnas

---

## 🚀 PRÓXIMOS PASOS OPCIONALES

1. **Agregar carruseles de imágenes** para productos (ya está implementado)
2. **Ordenamiento** (Por precio, más nuevo, etc.)
3. **Paginación** si hay muchos productos
4. **Búsqueda dentro del catálogo**
5. **Historial de filtros en URL** (para compartir links)

---

## 📝 RESUMEN

| Componente | Estado | Ubicación |
|-----------|--------|-----------|
| Modelos | ✅ Actualizado | `store/models.py` |
| API | ✅ Creada | `store/views/products.py` + `urls.py` |
| JavaScript | ✅ Implementado | `static/public/js/filtros-dinamicos.js` |
| Estilos | ✅ Completos | `static/public/css/filtros-dinamicos.css` |
| HTML | ✅ Reutilizable | `templates/public/includes/filtros-dinamicos.html` |
| Integración | ✅ Base | `templates/public/base.html` |

---

**¡Listo para usar! 🎉**
