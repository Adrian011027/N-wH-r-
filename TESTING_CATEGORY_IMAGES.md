# 🧪 GUÍA DE TESTING - Imágenes en Categorías y Subcategorías

## ⚡ Testing Rápido (5 minutos)

### Paso 1: Preparar una imagen de prueba
1. Abre una carpeta cualquiera en tu PC
2. Descarga una imagen JPG/PNG pequeña (ej: 500x500px)
3. Guárdala como `test.jpg` en escritorio o documentos

---

### Paso 2: Acceder al Dashboard
1. Abre navegador → `http://localhost:8000/dashboard/`
2. Inicia sesión con usuario admin (si es necesario)
3. Haz clic en **"Categorías"** en el menú lateral

---

### Paso 3: Test CREATE - Crear Categoría con Imagen

**Paso 3.1: Abrir formulario**
- Click en botón **"Crear Nueva Categoría"** (si existe)
- O busca el formulario "Crear" en la página

**Paso 3.2: Ingresar datos**
- Campo Nombre: Escribe `Test Category ${DATE}`
  - Ejemplo: `Test Category 15122024`
  - Esto permite crear múltiples sin conflictos
- Campo Imagen: Click en **"📷 Elegir imagen"**

**Paso 3.3: Seleccionar imagen**
- Se abre explorador de archivos
- Selecciona tu `test.jpg`
- Click "Abrir"

**Paso 3.4: Verificar preview**
- ✅ ¿Aparece preview 120x120px con la imagen?
- ✅ ¿Se ve el botón X rojo en la esquina superior derecha?
- ✅ ¿La imagen está centrada y bien visible?

**Paso 3.5: Guardar**
- Click en botón **"Guardar"** o **"Crear"**

**Paso 3.6: Verificar resultado**
- ✅ ¿Aparece alerta "Categoría creada exitosamente"?
- ✅ ¿La tabla se recarga automáticamente?
- ✅ ¿Aparece la nueva categoría en la tabla?
- ✅ ¿Se ve la imagen en miniatura en la tabla?

**Verificación en Backend (opcional):**
```bash
# En la terminal, verifica que la imagen se guardó
ls -la media/categorias/
# Deberías ver archivos como: test_category_15122024_<timestamp>.jpg
```

---

### Paso 4: Test EDIT - Editar Categoría Existente (Ver Imagen Actual)

**Paso 4.1: Buscar categoría con imagen**
- En la tabla de categorías, busca una que tengas con imagen
- O usa la que acabas de crear

**Paso 4.2: Click en Editar**
- En la fila de la categoría, haz click en botón **"Editar"**
- Se abre un modal o formulario

**Paso 4.3: Verificar imagen actual**
- ✅ ¿Aparece la imagen actual en el preview?
- ✅ ¿El preview muestra la imagen correctamente (120x120px)?
- ✅ ¿La URL parece correcta? (ejemplo: `/media/categorias/...`)

**Paso 4.4: Cambiar nombre (SIN cambiar imagen)**
- En el campo Nombre, agrega " EDITADO" al final
  - Ejemplo: `Test Category 15122024 EDITADO`
- NO hagas click en "📷 Cambiar imagen" aún

**Paso 4.5: Guardar SIN cambiar imagen**
- Click en **"Actualizar"** o **"Guardar"**

**Paso 4.6: Verificar resultado**
- ✅ ¿Alerta "Categoría actualizada exitosamente"?
- ✅ ¿La tabla se recarga?
- ✅ ¿El nombre cambió pero la imagen es IGUAL (no nueva)?

---

### Paso 5: Test EDIT - Reemplazar Imagen

**Paso 5.1: Abrir modal de edición nuevamente**
- Click en **"Editar"** de la categoría anterior

**Paso 5.2: Reemplazar imagen**
- Click en **"📷 Cambiar imagen"**
- Se abre explorador de archivos
- Selecciona OTRA imagen (diferente a la anterior)

**Paso 5.3: Verificar preview actualizado**
- ✅ ¿El preview cambia a la nueva imagen?
- ✅ ¿Se ve claramente diferente a la anterior?

**Paso 5.4: Guardar cambios**
- Click en **"Actualizar"** o **"Guardar"**

**Paso 5.5: Verificar en tabla**
- ✅ ¿La imagen en la tabla cambió?
- ✅ ¿Puedo ver visualmente que es una imagen diferente?

---

### Paso 6: Test SUBCATEGORÍAS - Proceso Similar

1. En Dashboard → Busca sección de **"Subcategorías"**
2. Repite pasos 3, 4, 5 pero con subcategorías
3. Al crear, deberás seleccionar una categoría padre
4. El preview debería funcionar igual

---

## 📱 Test en Navegador (DevTools)

### Verificar Network Tab
1. Abre DevTools (F12)
2. Pestaña **"Network"**
3. Haz click en "Crear Nueva Categoría"
4. Selecciona imagen
5. Click "Guardar"
6. En Network, busca la solicitud `POST /api/categorias/crear/`
7. ✅ Status debe ser **200** o **201**
8. ✅ Response debe mostrar:
   ```json
   {
     "id": <numero>,
     "nombre": "...",
     "imagen": "/media/categorias/..."
   }
   ```

### Verificar Console Tab
1. Pestaña **"Console"**
2. Busca cualquier error rojo (debería haber 0)
3. Los logs informativos pueden estar pero no deben ser errores

---

## 🎯 Test Completo (Checklist)

### Categorías
- [ ] Crear categoría sin imagen → Funciona
- [ ] Crear categoría CON imagen → Preview aparece, se guarda
- [ ] Editar categoría → Ve imagen actual
- [ ] Editar SIN cambiar imagen → Imagen se mantiene igual
- [ ] Editar Y cambiar imagen → Nueva imagen se ve en tabla
- [ ] Remover preview con X → Input se resetea
- [ ] Respuesta API tiene campo "imagen" con URL

### Subcategorías
- [ ] Crear subcategoría CON imagen → Funciona igual
- [ ] Editar subcategoría → Ve imagen actual
- [ ] Cambiar imagen en subcategoría → Se actualiza
- [ ] Tabla muestra imagen pequeña en miniatura

### Backend
- [ ] Archivos guardados en `/media/categorias/`
- [ ] Archivos guardados en `/media/subcategorias/`
- [ ] URLs en respuesta JSON son accesibles
- [ ] Ningún error 500 en Django

---

## 🐛 Troubleshooting

### ❌ Preview no aparece
**Solución:**
1. Verifica que el input file tiene el ID correcto (`imagen-categoria`, `imagen-subcategoria`)
2. Verifica que existe elemento con class `preview-categoria` o `preview-subcategoria`
3. Abre DevTools Console (F12) y busca errores JavaScript
4. Verifica que `accept="image/*"` está en el input

### ❌ No se guarda la imagen
**Solución:**
1. Verifica en DevTools → Network que el request es `multipart/form-data`
2. Verifica que incluye el archivo en FormData
3. Chequea respuesta del servidor (200 vs 500)
4. Verifica carpeta `media/categorias/` existe

### ❌ Imagen se guarda pero no se ve en tabla
**Solución:**
1. Recarga la página (Ctrl+F5 para limpiar caché)
2. Verifica en Network que la URL de imagen está correcta
3. Verifica que el navegador puede acceder a `/media/categorias/...`
4. Chequea permisos de archivos en servidor

### ❌ Modal no muestra imagen actual al editar
**Solución:**
1. Verifica que `abrirModalEditar()` recibe el parámetro `imagenUrl`
2. Verifica que existe elemento con class `preview-edit` o `preview-edit-sub`
3. Chequea que la URL devuelta por GET es correcta

---

## 📊 Reporte de Testing

Después de completar todos los tests, completa este reporte:

```markdown
## Testing Report - Imágenes Categorías

**Fecha:** [HOY]
**Testeador:** [TU NOMBRE]
**Navegador:** [Chrome/Firefox/Edge]

### Resultados
- [ ] Crear categoría con imagen: ✅ / ❌
- [ ] Editar categoría ver imagen: ✅ / ❌
- [ ] Cambiar imagen: ✅ / ❌
- [ ] Subcategorías funcionan igual: ✅ / ❌
- [ ] Imágenes se guardan en disco: ✅ / ❌
- [ ] URLs son accesibles: ✅ / ❌
- [ ] Sin errores en Console: ✅ / ❌
- [ ] Respuesta API correcta: ✅ / ❌

### Problemas Encontrados
(Si los hay)
1. ...
2. ...

### Notas Adicionales
...

### Status Final
✅ LISTO PARA PRODUCCIÓN / ⚠️ REQUIERE ARREGLOS
```

---

## ⏱️ Tiempo Estimado

| Test | Duración |
|------|----------|
| Test 1: CREATE | 2 min |
| Test 2: EDIT Ver Imagen | 1 min |
| Test 3: EDIT Cambiar Imagen | 2 min |
| Test 4: SUBCATEGORÍAS | 2 min |
| DevTools Verification | 1 min |
| **TOTAL** | **~8 minutos** |

---

## 🚀 Si Todo Funciona

✅ Felicitaciones, la implementación está completa y funcional.

**Próximos pasos opcionales:**
- Integrar imágenes en navbar (si aplica)
- Subir imágenes a S3 en lugar de disco local
- Comprimir imágenes automáticamente
- Generar thumbnails
- Agreguar validación de tamaño máximo

---

## 🔗 Enlaces Útiles

- [Verificación Técnica](VERIFICATION_CATEGORY_IMAGES.md)
- [Flujo Visual](VISUAL_CATEGORY_IMAGE_FLOW.md)
- [Documentación API](DASHBOARD_FORMULARIOS.md)

