# 📱 NAVBAR CON FILTROS DINÁMICOS EN CASCADA

## ✅ Lo que cambió

### Antes:
```
Inicio
Dama
Caballero
Accesorios
Todo
```

### Ahora (Sistema en Cascada):
```
Inicio
👥 Ambos
  📂 Calzado
    🏷️ Marcas
      └─ Nike
      └─ Adidas
      └─ LV
    🎁 Promociones
      └─ En Oferta
  📂 Bolsas
    🏷️ Marcas
      └─ Nike
      └─ Prada
👩 Mujer
  📂 Ropa
  📂 Accesorios
👨 Hombre
  📂 Calzado
  📂 Ropa
Ver Todo
```

---

## 🎯 Flujo de Usuario

```
1️⃣ Usuario abre el navbar
   ↓
2️⃣ Ve 3 géneros: 👥 Ambos, 👩 Mujer, 👨 Hombre
   ↓
3️⃣ Hace clic en "👨 Hombre" (se marca como activo con fondo azul)
   ↓ ⚡ Carga dinámicamente: categorías disponibles para HOMBRE
   ↓
4️⃣ Ve categorías: Calzado, Ropa, Accesorios
   Selecciona "Calzado" (se marca como activo)
   ↓ ⚡ Carga dinámicamente: subcategorías de CALZADO + HOMBRE
   ↓
5️⃣ Ve subcategorías agrupadas por tipo:
   - 🏷️ MARCAS: Nike, Adidas, Puma
   - 🎁 PROMOCIONES: En Oferta, Black Friday
   Hace clic en "Nike" para filtrar
```

---

## 🔧 Cambios Técnicos

### Backend (APIs)
✅ 3 endpoints ya creados:
```bash
GET /api/categorias-por-genero/?genero=hombre
GET /api/subcategorias-por-categoria/?categoria_id=1&genero=hombre
GET /api/productos-filtrados/?genero=hombre&categoria_id=1&subcategorias=1,2
```

### Frontend (JavaScript)
✅ `nav-menu.js` **completamente reescrito**
- Sistema de caché para evitar llamadas repetidas
- Event listeners para abrir/cerrar submenús
- Renderización dinámica de categorías y subcategorías
- Manejo de errores

### Estilos (CSS)
✅ Estilos nuevos en `header.css`:
- Items activos con fondo azul
- Submenús con animaciones suaves
- Thumbnails de categorías y subcategorías
- Botón toggle que rota 90° al abrir
- Responsive (funciona en móvil)

---

## 🎨 Características Visuales

### Género seleccionado:
```
👨 Hombre  ← Fondo azul oscuro (#0056b3), texto blanco
```

### Categoría seleccionada:
```
📂 Calzado  ← Fondo azul claro (#e7f3ff), texto azul
```

### Botón toggle:
- Gira 90° cuando se abre el submenú
- Color azul cuando el submenú está abierto

### Submenús:
- Fondo gris claro (#f9f9f9)
- Línea azul en la izquierda
- Indentación para visual de jerarquía
- Transición suave

---

## 📋 No Necesita Migraciones

❌ **No crearás migraciones nuevas** porque:
- Ya cambiaste `subcategoria` FK a `subcategorias` M2M en `models.py`
- Los endpoints ya existen en `urls.py`
- Solo es JavaScript y CSS

**Pero sí necesitas ejecutar las migraciones anteriores:**
```bash
python manage.py makemigrations store
python manage.py migrate
```

---

## 🚀 Cómo Está Funcionando

1. **User abre navbar**
   ```javascript
   document.addEventListener('DOMContentLoaded', init);
   // Renderiza 3 géneros pre-definidos
   ```

2. **User hace clic en género**
   ```javascript
   selectGenero('hombre', liElement)
   // → Llama: GET /api/categorias-por-genero/?genero=hombre
   // → Cachea el resultado
   // → Renderiza categorías dinámicamente
   ```

3. **User hace clic en categoría**
   ```javascript
   selectCategoria(1, 'Calzado', 'hombre', liElement)
   // → Llama: GET /api/subcategorias-por-categoria/?categoria_id=1&genero=hombre
   // → Cachea el resultado
   // → Agrupa por tipo (Marca, Promoción, etc.)
   // → Renderiza subcategorías dinámicamente
   ```

4. **User hace clic en subcategoría**
   ```javascript
   // Aquí puedes:
   // - Filtrar productos
   // - Navegar a URL
   // - Disparar evento personalizado
   ```

---

## ⚙️ Sistema de Caché

Para evitar hacer la misma llamada API varias veces:

```javascript
const cache = {
  categorias: {
    'hombre': [...],
    'mujer': [...]
  },
  subcategorias: {
    'hombre-1': [...],
    'hombre-2': [...]
  }
};
```

---

## 🐛 Debugging

Abre la consola del navegador (F12) y verás logs:

```
📍 Género seleccionado: hombre
📂 Categoría seleccionada: Calzado (ID: 1)
🏷️ Subcategoría: Nike
```

---

## 📱 Mobile vs Desktop

Funciona exactamente igual en ambos casos:
- Mismo menú lateral
- Mismo flujo de cascada
- Estilos adaptados para pantallas pequeñas

---

## 🎯 Próximos Pasos (Opcionales)

1. **Al hacer clic en subcategoría:**
   - Navegar a `/productos/?subcategoria=Nike`
   - O disparar un evento y filtrar productos en la página actual

2. **Agregar búsqueda dentro del navbar**

3. **Historial de búsqueda reciente**

4. **Sincronizar con URL** para que se pueda compartir `/navbar?genero=hombre&categoria=calzado`

---

**¡Listo! El navbar ahora es dinámico y responsive.** 🚀
