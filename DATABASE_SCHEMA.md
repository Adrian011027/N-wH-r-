# 📊 Esquema de Base de Datos - NöwHėrē E-commerce

## 🎯 Resumen de Tablas

Tu base de datos tendrá **15 tablas principales** cuando ejecutes las migraciones:

| # | Tabla | Registros Principales | Descripción |
|---|-------|----------------------|-------------|
| 1 | `store_cliente` | Usuarios/Clientes | Sistema de autenticación principal |
| 2 | `store_usuario` | Usuarios admin/staff | Usuarios del dashboard |
| 3 | `store_categoria` | Categorías | Ropa, Accesorios, etc. |
| 4 | `store_producto` | Productos | Catálogo principal |
| 5 | `store_atributo` | Tipos de atributos | Talla, Color, Material |
| 6 | `store_atributovalor` | Valores de atributos | 38, 40, Rojo, Azul |
| 7 | `store_variante` | Variantes de productos | Producto + Talla + Color + Stock |
| 8 | `store_varianteatributo` | Relación variante-atributos | M2M entre variantes y valores |
| 9 | `store_carrito` | Carritos de compra | Carritos activos/completados |
| 10 | `store_carritoproducto` | Items del carrito | Productos en cada carrito |
| 11 | `store_wishlist` | Listas de deseos | Wishlist por cliente |
| 12 | `store_wishlist_productos` | Productos en wishlist | M2M wishlist-productos |
| 13 | `store_orden` | Órdenes de compra | Historial de compras |
| 14 | `store_ordendetalle` | Detalles de orden | Items de cada orden |
| 15 | `store_blacklistedtoken` | Tokens JWT revocados | Seguridad JWT |
| 16 | `store_contactocliente` | Mensajes de contacto | Formulario de contacto |

---

## 🏗️ Estructura Detallada por Módulo

### 👥 **1. SISTEMA DE USUARIOS**

#### `store_cliente` (AbstractBaseUser - AUTH_USER_MODEL)
```sql
CREATE TABLE store_cliente (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Información básica
    username VARCHAR(255) UNIQUE NOT NULL,
    correo VARCHAR(254),
    nombre VARCHAR(255),
    telefono VARCHAR(20),
    telefono_alternativo VARCHAR(20),
    
    -- Control de cambios
    ultima_modificacion_username TIMESTAMP WITH TIME ZONE,
    
    -- Dirección de envío (nuevo sistema)
    calle VARCHAR(500),
    colonia VARCHAR(200),
    codigo_postal VARCHAR(5),
    ciudad VARCHAR(200),
    estado VARCHAR(100),
    referencias TEXT,
    
    -- Dirección legacy
    direccion VARCHAR(500),
    
    -- Información fiscal
    tipo_cliente VARCHAR(20) DEFAULT 'menudeo',
    rfc VARCHAR(13),
    razon_social VARCHAR(500),
    direccion_fiscal VARCHAR(500),
    
    -- Permisos
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false
);

-- Índices
CREATE INDEX idx_cliente_username ON store_cliente(username);
CREATE INDEX idx_cliente_correo ON store_cliente(correo);
```

**Registros esperados:**
- Admin: 1
- Clientes normales: ~100-10,000
- Mayoristas: ~10-100

#### `store_usuario` (Usuarios del dashboard)
```sql
CREATE TABLE store_usuario (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);
```

**Roles típicos:** admin, ventas, almacen, soporte

---

### 🛍️ **2. CATÁLOGO DE PRODUCTOS**

#### `store_categoria`
```sql
CREATE TABLE store_categoria (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);
```

**Ejemplos:** Playeras, Pantalones, Vestidos, Accesorios, Zapatos

#### `store_producto`
```sql
CREATE TABLE store_producto (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    precio NUMERIC(10, 2) NOT NULL,
    precio_mayorista NUMERIC(10, 2) DEFAULT 0,
    categoria_id BIGINT REFERENCES store_categoria(id) ON DELETE CASCADE,
    genero VARCHAR(50) NOT NULL,
    en_oferta BOOLEAN DEFAULT false,
    imagen VARCHAR(100),  -- ruta en /media/productos/
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_producto_categoria ON store_producto(categoria_id);
CREATE INDEX idx_producto_genero ON store_producto(genero);
CREATE INDEX idx_producto_oferta ON store_producto(en_oferta);
```

**Propiedad calculada (no en DB):**
- `stock_total`: Suma del stock de todas sus variantes

---

### 🎨 **3. SISTEMA DE VARIANTES**

#### `store_atributo` (Tipos de atributos)
```sql
CREATE TABLE store_atributo (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);
```

**Ejemplos:** Talla, Color, Material, Estilo

#### `store_atributovalor` (Valores específicos)
```sql
CREATE TABLE store_atributovalor (
    id BIGSERIAL PRIMARY KEY,
    atributo_id BIGINT REFERENCES store_atributo(id) ON DELETE CASCADE,
    valor VARCHAR(100) NOT NULL
);

-- Índice
CREATE INDEX idx_atributovalor_atributo ON store_atributovalor(atributo_id);
```

**Ejemplos:**
- Talla: XS, S, M, L, XL, 36, 38, 40
- Color: Rojo, Azul, Negro, Blanco

#### `store_variante` (Combinaciones producto + atributos + stock)
```sql
CREATE TABLE store_variante (
    id BIGSERIAL PRIMARY KEY,
    producto_id BIGINT REFERENCES store_producto(id) ON DELETE CASCADE,
    sku VARCHAR(100),  -- Código interno opcional
    precio NUMERIC(10, 2),  -- Si varía del precio base
    precio_mayorista NUMERIC(10, 2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_variante_producto ON store_variante(producto_id);
CREATE INDEX idx_variante_sku ON store_variante(sku);
CREATE INDEX idx_variante_stock ON store_variante(stock);
```

**Ejemplo:** Playera NöwHėrē Negra Talla M = 1 variante con stock 50

#### `store_varianteatributo` (Relación M2M)
```sql
CREATE TABLE store_varianteatributo (
    id BIGSERIAL PRIMARY KEY,
    variante_id BIGINT REFERENCES store_variante(id) ON DELETE CASCADE,
    atributo_valor_id BIGINT REFERENCES store_atributovalor(id) ON DELETE CASCADE,
    
    UNIQUE(variante_id, atributo_valor_id)
);

-- Índices
CREATE INDEX idx_varianteatr_variante ON store_varianteatributo(variante_id);
CREATE INDEX idx_varianteatr_valor ON store_varianteatributo(atributo_valor_id);
```

---

### 🛒 **4. CARRITO Y WISHLIST**

#### `store_carrito`
```sql
CREATE TABLE store_carrito (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES store_cliente(id) ON DELETE CASCADE NULL,
    session_key VARCHAR(40),  -- Para invitados
    status VARCHAR(50) DEFAULT 'vacio',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_carrito_cliente ON store_carrito(cliente_id);
CREATE INDEX idx_carrito_session ON store_carrito(session_key);
CREATE INDEX idx_carrito_status ON store_carrito(status);
```

**Estados:** vacio, activo, checkout, completado

#### `store_carritoproducto`
```sql
CREATE TABLE store_carritoproducto (
    id BIGSERIAL PRIMARY KEY,
    carrito_id BIGINT REFERENCES store_carrito(id) ON DELETE CASCADE,
    variante_id BIGINT REFERENCES store_variante(id) ON DELETE CASCADE,
    cantidad INTEGER DEFAULT 1
);

-- Índices
CREATE INDEX idx_carritoprod_carrito ON store_carritoproducto(carrito_id);
CREATE INDEX idx_carritoprod_variante ON store_carritoproducto(variante_id);
```

#### `store_wishlist` y `store_wishlist_productos`
```sql
CREATE TABLE store_wishlist (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES store_cliente(id) ON DELETE CASCADE
);

CREATE TABLE store_wishlist_productos (
    id BIGSERIAL PRIMARY KEY,
    wishlist_id BIGINT REFERENCES store_wishlist(id) ON DELETE CASCADE,
    producto_id BIGINT REFERENCES store_producto(id) ON DELETE CASCADE,
    
    UNIQUE(wishlist_id, producto_id)
);
```

---

### 📦 **5. ÓRDENES Y COMPRAS**

#### `store_orden`
```sql
CREATE TABLE store_orden (
    id BIGSERIAL PRIMARY KEY,
    carrito_id BIGINT UNIQUE REFERENCES store_carrito(id) ON DELETE CASCADE,
    cliente_id BIGINT REFERENCES store_cliente(id) ON DELETE CASCADE,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_orden_cliente ON store_orden(cliente_id);
CREATE INDEX idx_orden_status ON store_orden(status);
CREATE INDEX idx_orden_created ON store_orden(created_at);
```

**Estados:** pendiente, pagado, enviado, entregado, cancelado

#### `store_ordendetalle`
```sql
CREATE TABLE store_ordendetalle (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES store_orden(id) ON DELETE CASCADE,
    variante_id BIGINT REFERENCES store_variante(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL
);

-- Índices
CREATE INDEX idx_ordendet_orden ON store_ordendetalle(order_id);
CREATE INDEX idx_ordendet_variante ON store_ordendetalle(variante_id);
```

---

### 🔐 **6. SEGURIDAD Y CONTACTO**

#### `store_blacklistedtoken` (JWT revocados)
```sql
CREATE TABLE store_blacklistedtoken (
    id BIGSERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_blacklist_token ON store_blacklistedtoken(token);
```

#### `store_contactocliente`
```sql
CREATE TABLE store_contactocliente (
    cliente_id BIGINT PRIMARY KEY REFERENCES store_cliente(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 📈 Relaciones Principales

```
Cliente (1) ──────< (N) Carrito
Cliente (1) ──────< (N) Orden
Cliente (1) ────── (1) Wishlist
Cliente (1) ────── (1) ContactoCliente

Categoria (1) ────< (N) Producto
Producto (1) ─────< (N) Variante
Producto (N) ────> (N) Wishlist (M2M)

Atributo (1) ─────< (N) AtributoValor
Variante (N) ────> (N) AtributoValor (M2M via VarianteAtributo)

Carrito (1) ──────< (N) CarritoProducto
Carrito (1) ────── (1) Orden

Orden (1) ────────< (N) OrdenDetalle
Variante (1) ─────< (N) OrdenDetalle
Variante (1) ─────< (N) CarritoProducto
```

---

## 📊 Tamaño Estimado de Datos

| Tabla | Registros Iniciales | Crecimiento Esperado |
|-------|---------------------|----------------------|
| Cliente | 3 (admin, jona, angel) | +100/mes |
| Producto | 50-100 | +20/mes |
| Variante | 200-500 | +80/mes |
| Orden | 0 | +500/mes |
| Carrito | 10-50 activos | Variable |
| BlacklistedToken | 0 | +50/día |

**Tamaño estimado en 6 meses:**
- Base de datos: ~500 MB
- Media (imágenes): ~2-5 GB

---

## 🔍 Consultas Útiles Post-Migración

### Ver todas las tablas creadas
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'store_%'
ORDER BY table_name;
```

### Ver estructura de una tabla
```sql
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'store_producto'
ORDER BY ordinal_position;
```

### Ver todas las relaciones (Foreign Keys)
```sql
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name LIKE 'store_%'
ORDER BY tc.table_name;
```

### Contar registros en todas las tablas
```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'store_%'
ORDER BY n_live_tup DESC;
```

---

## ✅ Checklist Pre-Migración

- [ ] AWS RDS PostgreSQL creado
- [ ] Security Group configurado (puerto 5432)
- [ ] Credenciales guardadas
- [ ] .env actualizado con endpoint de AWS
- [ ] psycopg2-binary instalado
- [ ] Conexión testeada

## ✅ Checklist Post-Migración

- [ ] `python manage.py makemigrations` exitoso
- [ ] `python manage.py migrate` exitoso
- [ ] Verificar 15+ tablas creadas
- [ ] `python create_users.py` ejecutado
- [ ] Verificar 3 usuarios creados
- [ ] Test de login en dashboard
- [ ] Test de API de productos

