# 🚀 Guía: Conectar Django a AWS RDS PostgreSQL

## 📋 Prerrequisitos

### ✅ Que ya debes tener:
- ✅ AWS RDS PostgreSQL creado
- ✅ Endpoint del RDS (algo como: `nowhere-db.c9abc123xyz.us-east-1.rds.amazonaws.com`)
- ✅ Usuario y contraseña del RDS
- ✅ Nombre de la base de datos (default: `postgres` o el que elegiste)
- ✅ Security Group permitiendo tu IP en puerto 5432

### 📦 Dependencias Python:
```bash
pip install psycopg2-binary python-decouple
```

---

## 🔧 PASO 1: Configurar .env

Actualiza tu archivo `.env` con las credenciales de AWS RDS:

```env
# ═══════════════════════════════════════════════════════════
# AWS RDS PostgreSQL - Base de Datos Compartida
# ═══════════════════════════════════════════════════════════
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu_password_aws_rds
DB_HOST=nowhere-db.c9abc123xyz.us-east-1.rds.amazonaws.com
DB_PORT=5432

# ═══════════════════════════════════════════════════════════
# EMAIL Y CREDENCIALES (mantener igual)
# ═══════════════════════════════════════════════════════════
EMAIL_HOST_USER=nowhere.soporte@gmail.com
EMAIL_HOST_PASSWORD=luif hayv tyqj csch
TWILIO_ACCOUNT_SID=ACfbd7a1efe99d0197dfb94db1924b2877
TWILIO_AUTH_TOKEN=c32ec3fd85592918361c9522eafb5ebf
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_ADMIN_PHONE=whatsapp:+5213322118360
SECRET_KEY=django-insecure-gp@8q$g&$pzfl!-t80*m72pitbub9c2ydnny1qosx2^7=b@(%y
JWT_SECRET_KEY=ElJona_dame 3sPuto
```

### 🔍 Cómo obtener tu endpoint de AWS RDS:
1. AWS Console → RDS → Databases
2. Clic en tu instancia PostgreSQL
3. En "Connectivity & security" copia el **Endpoint**
4. Ejemplo: `nowhere-db.c9abc123xyz.us-east-1.rds.amazonaws.com`

---

## 🔧 PASO 2: Verificar settings.py

Tu `ecommerce/settings.py` ya está configurado correctamente:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='nowhere_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}
```

**✅ No necesitas modificar nada aquí** - Solo actualiza el `.env`

---

## 🧪 PASO 3: Probar la Conexión

Antes de migrar, prueba que Django puede conectarse a AWS RDS:

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Probar conexión
python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings'); django.setup(); from django.db import connection; connection.ensure_connection(); print('✅ Conexión exitosa a AWS RDS')"
```

### 🚨 Posibles errores:

#### Error 1: `could not connect to server: Connection timed out`
**Causa:** Security Group no permite tu IP en puerto 5432

**Solución:**
1. AWS Console → EC2 → Security Groups
2. Busca el Security Group de tu RDS
3. Editar Inbound Rules
4. Agregar regla:
   - Type: PostgreSQL
   - Protocol: TCP
   - Port: 5432
   - Source: `Mi IP` o `0.0.0.0/0` (para desarrollo)

#### Error 2: `password authentication failed for user "postgres"`
**Causa:** Usuario o contraseña incorrectos

**Solución:**
- Verifica las credenciales en AWS RDS Console
- Revisa que el `.env` tenga la contraseña correcta

#### Error 3: `database "nowhere_db" does not exist`
**Causa:** La base de datos no existe en RDS

**Solución:**
```powershell
# Conectarse a RDS y crear la base de datos
$env:PGPASSWORD="tu_password_aws_rds"
psql -h nowhere-db.c9abc123xyz.us-east-1.rds.amazonaws.com -U postgres -c "CREATE DATABASE nowhere_db;"
```

O cambia `DB_NAME=postgres` en `.env` para usar la DB por defecto.

---

## 🚀 PASO 4: Ejecutar Migraciones

Una vez que la conexión funcione:

```powershell
# 1. Crear archivos de migración (si hay cambios en models.py)
python manage.py makemigrations

# 2. Aplicar migraciones a AWS RDS
python manage.py migrate

# 3. Verificar que se crearon las tablas
python manage.py dbshell
```

Dentro de `dbshell`:
```sql
-- Ver todas las tablas creadas
\dt

-- Ver específicamente las tablas de store
\dt store_*

-- Contar tablas
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'store_%';

-- Salir
\q
```

**✅ Deberías ver 15+ tablas con prefijo `store_`**

---

## 👥 PASO 5: Crear Usuarios Iniciales

```powershell
python create_users.py
```

**Usuarios creados:**
- `admin` / `admin123` (Usuario dashboard, rol: admin)
- `jona` / `123456` (Cliente normal, correo: jona@nowhere.com)
- `angel` / `123456` (Cliente normal, correo: angel@nowhere.com)

### Verificar en la base de datos:
```sql
-- Conectarse
python manage.py dbshell

-- Ver usuarios del dashboard
SELECT id, username, role FROM store_usuario;

-- Ver clientes
SELECT id, username, correo, nombre, tipo_cliente, is_admin FROM store_cliente;

-- Salir
\q
```

---

## 🧪 PASO 6: Probar la Aplicación

```powershell
# Iniciar servidor Django
python manage.py runserver
```

### Pruebas recomendadas:

#### 1. Login Dashboard
- URL: http://127.0.0.1:8000/dashboard/login/
- Usuario: `admin`
- Password: `admin123`
- ✅ Deberías entrar al dashboard

#### 2. Login Cliente (Frontend)
- URL: http://127.0.0.1:8000/ (tu página de login)
- Usuario: `jona` o `angel`
- Password: `123456`
- ✅ Deberías entrar como cliente

#### 3. API de Productos
```powershell
# Prueba con curl o en el navegador
curl http://127.0.0.1:8000/api/productos/
```

---

## 📊 PASO 7: Poblar con Datos de Prueba (Opcional)

### Opción A: Desde Django Admin
1. http://127.0.0.1:8000/admin/
2. Login con `admin` / `admin123`
3. Agregar manualmente:
   - Categorías (Playeras, Pantalones, Vestidos)
   - Productos
   - Atributos (Talla, Color)
   - Valores (S, M, L, XL / Rojo, Azul)
   - Variantes

### Opción B: Script de Seed (si quieres, lo puedo crear)
```python
# seed_data.py (puedo crearlo)
- 5 categorías
- 20 productos
- 3 atributos
- 15 valores de atributos
- 100 variantes con stock
```

**¿Quieres que cree el script de seed automático?**

---

## 🔄 PASO 8: Compartir con tu Compañero (Jona)

### Para que Jona se conecte a la misma DB:

1. **Compartir archivo `.env`** (sin subirlo a Git):
```powershell
# Método 1: Por mensaje privado/email
# Copia el contenido de .env y envíaselo

# Método 2: Crear .env.example (sin contraseñas)
cp .env .env.example
# Edita .env.example y reemplaza los valores sensibles con placeholders
```

2. **Jona debe:**
```bash
# 1. Clonar el repo (si no lo tiene)
git clone <tu-repo>

# 2. Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear .env con las credenciales de AWS RDS (las mismas tuyas)

# 5. NO ejecutar makemigrations ni migrate (ya están aplicadas por ti)

# 6. Iniciar servidor
python manage.py runserver
```

**⚠️ IMPORTANTE:** Solo UNA persona debe ejecutar las migraciones iniciales. El resto solo necesita el `.env` actualizado.

---

## 🔐 Seguridad del .env

### ❌ NUNCA hagas esto:
```bash
git add .env
git commit -m "Agregar configuración"
git push
```

### ✅ Asegúrate de tener en `.gitignore`:
```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Database
db.sqlite3
*.sqlite3

# Media files
/media/

# Virtual environment
venv/
```

### ✅ Crea `.env.example` para el equipo:
```env
# .env.example - Template para el equipo
# Copiar a .env y rellenar con valores reales

# AWS RDS PostgreSQL
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=<PEDIR_A_ADMIN>
DB_HOST=<ENDPOINT_AWS_RDS>
DB_PORT=5432

# Email
EMAIL_HOST_USER=<CORREO_GMAIL>
EMAIL_HOST_PASSWORD=<APP_PASSWORD_GMAIL>

# Twilio
TWILIO_ACCOUNT_SID=<PEDIR_A_ADMIN>
TWILIO_AUTH_TOKEN=<PEDIR_A_ADMIN>
TWILIO_WHATSAPP_FROM=<NUMERO_TWILIO>
TWILIO_ADMIN_PHONE=<NUMERO_ADMIN>

# Django
SECRET_KEY=<GENERAR_NUEVA_EN_PRODUCCION>
JWT_SECRET_KEY=<GENERAR_NUEVA_EN_PRODUCCION>
```

---

## 📊 Monitoreo y Mantenimiento

### Ver conexiones activas:
```sql
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = 'nowhere_db';
```

### Ver tamaño de la base de datos:
```sql
SELECT 
    pg_size_pretty(pg_database_size('nowhere_db')) AS size;
```

### Ver tamaño de cada tabla:
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🆘 Troubleshooting

### Problema: "Too many connections"
```python
# En settings.py, agregar:
DATABASES = {
    'default': {
        # ... configuración existente ...
        'CONN_MAX_AGE': 60,  # Reutilizar conexiones por 60 segundos
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'connect_timeout': 10,
        },
    }
}
```

### Problema: Latencia alta
- Verifica que tu RDS esté en la región más cercana (us-east-1 para México)
- Considera usar RDS Proxy para pooling de conexiones
- Usa índices en campos frecuentemente consultados

### Problema: Costo alto
- Free Tier AWS RDS: 750 horas/mes (db.t3.micro o db.t2.micro)
- Detén la instancia cuando no la uses (AWS la reiniciará después de 7 días)
- Alternativas gratuitas: Railway, Supabase, Render

---

## ✅ Checklist Final

- [ ] `.env` actualizado con credenciales de AWS RDS
- [ ] Conexión testeada exitosamente
- [ ] `python manage.py migrate` ejecutado
- [ ] 15+ tablas creadas en RDS
- [ ] `python create_users.py` ejecutado
- [ ] 3 usuarios verificados en la DB
- [ ] Login dashboard funciona (admin/admin123)
- [ ] Login cliente funciona (jona/123456)
- [ ] API de productos responde
- [ ] `.env` agregado a `.gitignore`
- [ ] `.env.example` creado para el equipo
- [ ] Jona tiene acceso a las credenciales
- [ ] Ambos pueden conectarse simultáneamente

---

## 🎯 Próximos Pasos

1. **Poblar base de datos** con productos de prueba
2. **Configurar S3** para imágenes (opcional, para producción)
3. **Configurar backups** automáticos en AWS RDS
4. **Monitorear costos** en AWS Billing
5. **Implementar features** de la roadmap (Reseñas, Historial, Cupones)

---

## 💡 Tips Pro

### Backup manual antes de cambios grandes:
```bash
# Exportar toda la DB
pg_dump -h tu-endpoint.rds.amazonaws.com -U postgres -d nowhere_db > backup_$(date +%Y%m%d).sql

# Restaurar si algo sale mal
psql -h tu-endpoint.rds.amazonaws.com -U postgres -d nowhere_db < backup_20231215.sql
```

### Variables de entorno para psql:
```powershell
# Agregar a tu perfil de PowerShell
$env:PGHOST="tu-endpoint.rds.amazonaws.com"
$env:PGUSER="postgres"
$env:PGDATABASE="nowhere_db"
$env:PGPASSWORD="tu_password"

# Ahora puedes usar solo:
psql
```

### Django dbshell shortcut:
```powershell
# En lugar de psql manual, usar:
python manage.py dbshell

# Ejecutar archivo SQL:
python manage.py dbshell < script.sql
```

---

**¿Listo para conectar? Dame tu endpoint de AWS RDS y actualizo el .env por ti** 🚀

