# Configuración para Coolify

## Variables de entorno a configurar en Coolify:

```
DATABASE_URL=postgres://postgres:fAsgjW3bsrLbsBfrSIxltERDtu090hJGVQmiDheF8wL8tDnyxBXPYvUlwgd1u5c@xss53rbys91ky5kngduid77a:5432/postgres
SECRET_KEY=tu_clave_secreta_segura_aqui_cambiala_ya
UPLOAD_FOLDER=/app/app/static/uploads/repuestos
```

## Volúmenes persistentes (IMPORTANTE):
Configurar en Coolify:
```
/app/app/static/uploads
```

## Problemas corregidos:

### 1. Imágenes del catálogo no cargaban en clientes ✓
- Causa: Las imágenes se servían con `url_for('static', ...)` que fallaba en Coolify
- Solución: Nueva ruta `/uploads/repuestos/<filename>` en `app/__init__.py`
- Archivos actualizados:
  - `app/__init__.py`: Ruta `serve_repuesto_image`
  - `app/templates/repuestos/index.html`: Ruta imagen corregida
  - `app/templates/repuestos/form.html`: Vista previa corregida
  - `app/templates/cliente_portal/tienda.html`: Ruta para clientes
  - `app/templates/base.html`: Logo corregido
  - `app/templates/base_portal.html`: Logo corregido

### 2. Panel admin se veía cortado en móvil ✓
- Causa: Faltaba `viewport-fit=cover` y diseño móvil inadecuado
- Solución:
  - `viewport-fit=cover` en meta viewport
  - Sidebar fijo con `100dvh` (dynamic viewport height)
  - Overlay con backdrop-filter y transiciones
  - Botón de cierre (X) en sidebar móvil
  - Espaciados y fuentes ajustados para móvil

### 3. Migración de SQLite a PostgreSQL ✓
- Ahora usa variable de entorno `DATABASE_URL`
- Compatible con ambos: PostgreSQL en producción, SQLite local
- Fix automático: `postgres://` → `postgresql://`
- Agregado `psycopg2-binary` a requirements.txt

## Para hacer deploy:

1. Configura las variables de entorno en Coolify (arriba)
2. Configura el volumen persistente para uploads
3. Haz commit y push:
```bash
cd proyecto_final
git add .
git commit -m "Fix: Imágenes catálogo, panel admin móvil y migración a PostgreSQL"
git push
```

## Migrar datos de SQLite a PostgreSQL:
Ejecuta localmente ANTES del primer deploy:
```bash
pip install psycopg2-binary
python migrate_to_postgres.py
```

## Notas:
- La URL de PostgreSQL ya está en el código y se convierte automáticamente
- Las imágenes necesitan el volumen persistente para no perderse
- Cambia el `SECRET_KEY` por uno seguro en producción
