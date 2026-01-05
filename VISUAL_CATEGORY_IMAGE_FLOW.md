# 📸 RESUMEN VISUAL - Preview de Imágenes Categorías & Subcategorías

## 🎯 Implementación Completada

### 1️⃣ **CREAR CATEGORÍA - Flujo Visual**

```
┌─────────────────────────────────────────┐
│  Dashboard → Categorías                 │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Form CREATE                                                 │
│                                                              │
│  Nombre: [___________________]                              │
│                                                              │
│  [📷 Elegir imagen]  ← Input file oculto + label bonita    │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │                      │   ← Preview container (120x120px) │
│  │   PREVIEW IMAGEN     │       Aparece después de SELECT  │
│  │   (si la selecciona) │       Tiene botón X rojo         │
│  │                      │                                   │
│  └──────────────────────┘                                   │
│                                                              │
│  [Guardar]  [Cancelar]                                      │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
     Usuario selecciona imagen JPG/PNG
              │
              ↓
     FileReader API (en JavaScript)
              │
              ↓
     Preview aparece (100% ancho, max 120x120px)
              │
              ↓
     Usuario hace click en "Guardar"
              │
              ↓
┌─────────────────────────────────────────┐
│  POST /api/categorias/crear/            │
│  Content-Type: multipart/form-data      │
│  ├─ nombre: "Test Categoría"            │
│  └─ imagen: <archivo JPG/PNG>           │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Backend: create_categoria(request)                         │
│  ├─ Procesa request.FILES.get("imagen")                    │
│  └─ Crea Categoria.objects.create(...)                     │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
     Imagen guardada en: media/categorias/<archivo>
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Respuesta JSON:                                            │
│  {                                                          │
│    "id": 42,                                                │
│    "nombre": "Test Categoría",                             │
│    "imagen": "/media/categorias/test_1234.jpg"            │
│  }                                                          │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
     ✅ Alerta "Categoría creada exitosamente"
              │
              ↓
     Tabla se recarga automáticamente
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│  TABLA DE CATEGORÍAS                                        │
│                                                              │
│  ID  │  Nombre         │  Imagen  │  Acciones              │
│  ────┼─────────────────┼──────────┼─────────────────       │
│  42  │ Test Categoría  │ [IMG]    │ [Editar] [Eliminar]   │
│                                    ↑ Imagen visible aquí    │
└─────────────────────────────────────────────────────────────┘
```

---

### 2️⃣ **EDITAR CATEGORÍA - Flujo Visual**

```
┌─────────────────────────────────────────┐
│  Tabla de Categorías                    │
│  Click en [Editar]                      │
└─────────────┬───────────────────────────┘
              │
              ↓
┌────────────────────────────────────────────────────────────────┐
│  Modal EDITAR CATEGORÍA                                        │
│                                                                │
│  Nombre: [Test Categoría________________]                     │
│                                                                │
│  Imagen actual:  [Mostrada desde DB]                         │
│  ┌──────────────────────┐                                    │
│  │                      │  ← URL del backend:                │
│  │   /media/categorias/ │    /media/categorias/test_1234.jpg│
│  │   test_1234.jpg      │                                    │
│  │                      │                                    │
│  └──────────────────────┘                                    │
│                                                                │
│  [📷 Cambiar imagen]  ← Input file oculto + label            │
│                                                                │
│  NOTA: Al seleccionar otra imagen, el preview                │
│        se actualiza con la nueva imagen                       │
│                                                                │
│  [Actualizar]  [Cancelar]                                    │
└─────────────┬────────────────────────────────────────────────┘
              │
              ↓
   Flujo similar a CREATE:
   FileReader → Preview → FormData → API → Backend → Guardado
              │
              ↓
   ✅ Alerta "Categoría actualizada exitosamente"
              │
              ↓
   Tabla se recarga con nueva imagen
```

---

## 📋 Componentes Implementados

### **HTML (Templates)**
```html
<!-- CREATE Form -->
<div class="file-input-wrapper">
  <input type="file" id="imagen-categoria" accept="image/*">
  <label for="imagen-categoria" class="file-label">
    📷 Elegir imagen
  </label>
</div>
<div class="preview-categoria"></div>

<!-- EDIT Modal -->
<div class="preview-edit"></div>
<div class="file-input-wrapper">
  <input type="file" id="imagen-edit" accept="image/*">
  <label for="imagen-edit" class="file-label">
    📷 Cambiar imagen
  </label>
</div>
```

### **CSS (Estilos)**
```css
.file-input-wrapper {
  position: relative;
}

.file-input-wrapper input {
  display: none;  /* Input oculto */
}

.file-label {
  display: inline-block;
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s;
}

.file-label:hover {
  background: #0056b3;
}

.image-preview-container {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #ddd;
  margin-top: 10px;
  position: relative;
}

.btn-remove-preview {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 28px;
  height: 28px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
}
```

### **JavaScript (Event Listeners)**
```javascript
// Preview en CREATE
inputImagen.addEventListener("change", function() {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const container = document.querySelector('.preview-categoria');
      container.innerHTML = `
        <div class="image-preview-container">
          <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
          <button class="btn-remove-preview">✕</button>
        </div>
      `;
    };
    reader.readAsDataURL(file);
  }
});

// Preview en EDIT
editImagen.addEventListener("change", function() {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const container = document.querySelector('.preview-edit');
      container.innerHTML = `
        <div class="image-preview-container">
          <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
          <button class="btn-remove-preview">✕</button>
        </div>
      `;
    };
    reader.readAsDataURL(file);
  }
});

// Remover preview
document.addEventListener("click", function(e) {
  if (e.target.closest(".btn-remove-preview")) {
    e.target.closest(".image-preview-container").parentElement.innerHTML = "";
    inputImagen.value = "";
  }
});
```

---

## 📊 Comparación: Antes vs Después

| Aspecto | ❌ Antes | ✅ Después |
|---------|---------|----------|
| **Input File** | Nativo (feo) | Estilizado (📷 emoji) |
| **Preview** | No había | Muestra imagen antes de guardar |
| **Edición** | No se veía imagen actual | Muestra imagen actual al abrir modal |
| **UX** | Usuario a ciegas | Confirma visualmente antes de enviar |
| **Cambiar imagen** | No había forma | Botón X rojo para reseleccionar |
| **Carpeta guardado** | Media root | `/media/categorias/` o `/media/subcategorias/` |
| **URL devuelta** | No había | `/media/categorias/<archivo>` |

---

## 🔧 Endpoints API

### CREATE
```http
POST /api/categorias/crear/
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN>

nombre=Nueva Categoría&imagen=<file>
```

**Respuesta:**
```json
{
  "id": 42,
  "nombre": "Nueva Categoría",
  "imagen": "/media/categorias/nueva_cat_12345.jpg"
}
```

---

### UPDATE
```http
POST /api/categorias/actualizar/42/
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN>

nombre=Nueva Categoría&imagen=<file>
```

**Nota:** La imagen es OPCIONAL en UPDATE. Si no se envía, mantiene la imagen anterior.

---

## ✅ Checklist de Testing

- [ ] **Test 1:** Crear categoría con imagen → preview aparece
- [ ] **Test 2:** Editar categoría → imagen actual visible
- [ ] **Test 3:** Cambiar imagen en edición → preview actualiza
- [ ] **Test 4:** Editar sin cambiar imagen → imagen se mantiene
- [ ] **Test 5:** Crear subcategoría con imagen
- [ ] **Test 6:** Remover preview con botón X → input se resetea
- [ ] **Test 7:** Verificar imágenes en `/media/categorias/` después de crear
- [ ] **Test 8:** Verificar imágenes en navbar si están configuradas

---

## 🎨 Visual de Componentes

### **Botón 📷 Elegir imagen**
```
┌──────────────────────┐
│   📷 Elegir imagen   │  ← Azul (#007bff), hover más oscuro
└──────────────────────┘
```

### **Preview Container (120x120px)**
```
┌──────────────┐
│              │
│   Imagen     │ × ← Botón rojo para remover
│   120x120    │
│              │
└──────────────┘
```

---

## 🚀 Estado Final

✅ **Completado:**
- Formularios HTML con file input wrapper
- CSS para estilos bonitos
- JavaScript para preview con FileReader
- Backend endpoints listos
- Modelos DB configurados
- Rutas de media configuradas

🎯 **Listo para:**
- Testing funcional
- Integración en navbar (si aplica)
- Sincronización con S3 (si aplica)

