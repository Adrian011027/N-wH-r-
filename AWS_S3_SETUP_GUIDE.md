# 🚀 Guía de Configuración AWS S3 para Nowhere E-commerce

## 📋 Requisitos Previos
- Cuenta de AWS activa
- Bucket S3 creado ✅
- Python 3.x instalado

---

## 1️⃣ Instalar Dependencias

```bash
pip install boto3==1.35.76 django-storages==1.14.4
```

O desde requirements.txt:
```bash
pip install -r requirements.txt
```

---

## 2️⃣ Crear Usuario IAM y Obtener Credenciales

### Paso 1: Ir a IAM en AWS Console
1. Ve a **IAM** → **Users** → **Create User**
2. Nombre: `nowhere-s3-user` (o el que prefieras)
3. Selecciona **Access key - Programmatic access**

### Paso 2: Asignar Permisos
1. **Attach policies directly**
2. Busca y selecciona: **`AmazonS3FullAccess`**
3. Click **Next** → **Create user**

### Paso 3: Guardar Credenciales
Después de crear el usuario, verás:
- **Access Key ID**: `AKIAXXXXXXXXXXXXXXXX`
- **Secret Access Key**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **¡IMPORTANTE!** Guarda estas credenciales inmediatamente, no podrás verlas después.

---

## 3️⃣ Configurar el Bucket S3

### Opción A: Via Consola AWS (Ya hecho ✅)
Tu bucket ya está creado con:
- **Nombre**: `tu-nombre-de-bucket`
- **Región**: `us-east-2`
- **ACL**: Acceso público habilitado
- **Cifrado**: SSE-S3 (predeterminado)

### Opción B: Configuración CORS (Recomendado para Frontend)
Ve a tu bucket → **Permissions** → **CORS** y añade:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD", "PUT", "POST"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"]
    }
]
```

---

## 4️⃣ Configurar Variables de Entorno (.env)

Edita tu archivo `.env` y completa:

```bash
# AWS S3 Configuration for Images
USE_S3=True
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_STORAGE_BUCKET_NAME=tu-nombre-de-bucket
AWS_S3_REGION_NAME=us-east-2
```

**Reemplaza:**
- `AWS_ACCESS_KEY_ID` → Tu Access Key del paso 2
- `AWS_SECRET_ACCESS_KEY` → Tu Secret Key del paso 2
- `AWS_STORAGE_BUCKET_NAME` → Nombre de tu bucket
- `AWS_S3_REGION_NAME` → Región de tu bucket (us-east-2 si es Ohio)

---

## 5️⃣ Aplicar Migraciones de Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará los nuevos campos:
- `Categoria.imagen` - Imagen de categoría
- `Variante.imagen` - Imagen específica de variante
- `ProductoImagen` - Galería de imágenes para carrusel

---

## 6️⃣ Verificar Configuración

### Test de Conexión S3

Crea un archivo `test_s3.py` en la raíz del proyecto:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Test de escritura
test_file = ContentFile(b'Test de conexion S3')
filename = default_storage.save('test/test.txt', test_file)
print(f"✅ Archivo subido: {default_storage.url(filename)}")

# Test de lectura
if default_storage.exists(filename):
    print("✅ Archivo existe en S3")
    default_storage.delete(filename)
    print("✅ Archivo eliminado correctamente")
else:
    print("❌ Error: archivo no encontrado")
```

Ejecutar:
```bash
python test_s3.py
```

---

## 7️⃣ Estructura de Almacenamiento en S3

Tu bucket organizará las imágenes así:

```
tu-bucket-name/
├── media/
│   ├── categorias/
│   │   ├── casualon.jpg
│   │   └── old-money.jpg
│   ├── productos/
│   │   ├── zapato-nike-123.jpg
│   │   └── bolsa-gucci-456.jpg
│   ├── productos/galeria/
│   │   ├── zapato-nike-123-frontal.jpg
│   │   ├── zapato-nike-123-lateral.jpg
│   │   └── zapato-nike-123-suela.jpg
│   └── variantes/
│       ├── zapato-nike-38-negro.jpg
│       ├── zapato-nike-39-negro.jpg
│       └── zapato-nike-38-blanco.jpg
```

---

## 8️⃣ URLs de las Imágenes

Las imágenes se servirán automáticamente desde S3:

```
https://tu-bucket.s3.amazonaws.com/media/productos/zapato.jpg
```

Django generará estas URLs automáticamente usando `.url`:
```python
producto.imagen.url  # https://tu-bucket.s3.amazonaws.com/media/productos/zapato.jpg
```

---

## 9️⃣ Migrar Imágenes Existentes (Opcional)

Si ya tienes imágenes en `media/`, puedes subirlas a S3:

```bash
# Instalar AWS CLI
pip install awscli

# Configurar
aws configure

# Subir archivos
aws s3 sync ./media/ s3://tu-bucket/media/ --acl public-read
```

---

## 🔒 Seguridad

### Mejores Prácticas:
✅ **Nunca** subas el `.env` a GitHub  
✅ Añade `.env` a `.gitignore`  
✅ Usa diferentes buckets para desarrollo/producción  
✅ Activa versionado del bucket para recuperar archivos  
✅ Configura lifecycle policies para eliminar archivos antiguos  

### Rotar Credenciales:
1. Crea nuevas Access Keys en IAM
2. Actualiza `.env` con las nuevas keys
3. Reinicia el servidor Django
4. Elimina las keys antiguas en IAM

---

## 🚨 Troubleshooting

### Error: "NoSuchBucket"
- Verifica el nombre del bucket en `.env`
- Asegúrate que la región sea correcta

### Error: "AccessDenied"
- Verifica las credenciales en `.env`
- Confirma que el usuario IAM tenga `AmazonS3FullAccess`

### Error: "403 Forbidden" al ver imágenes
- Verifica que el bucket tenga ACL público habilitado
- Confirma `AWS_DEFAULT_ACL = 'public-read'` en settings.py

### Imágenes no se muestran
- Verifica que `USE_S3=True` en `.env`
- Reinicia el servidor Django
- Revisa los logs para ver URLs generadas

---

## 💰 Costos Estimados

Para un e-commerce pequeño/mediano:
- **Almacenamiento**: ~$0.023 por GB/mes
- **Transferencia**: Primeros 100GB gratis/mes
- **Requests**: GET gratuitos, PUT ~$0.005 por 1000 requests

**Ejemplo**: 1000 productos con 5 imágenes cada uno (5GB total):
- Almacenamiento: $0.12/mes
- Muy económico para empezar 💰

---

## 📚 Recursos Adicionales

- [Documentación AWS S3](https://docs.aws.amazon.com/s3/)
- [Django Storages](https://django-storages.readthedocs.io/)
- [Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

## ✅ Checklist Final

- [ ] Usuario IAM creado con permisos S3
- [ ] Credenciales guardadas en `.env`
- [ ] `USE_S3=True` activado
- [ ] Migraciones aplicadas
- [ ] Test de conexión exitoso
- [ ] Primer producto con imagen subido

**¡Listo para producción!** 🎉
