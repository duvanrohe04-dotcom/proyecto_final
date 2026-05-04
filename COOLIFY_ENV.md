# Configuración para Coolify

## Problemas corregidos:

### 1. Imágenes del catálogo no cargaban en clientes
- **Causa**: Las imágenes se servían con `url_for('static', filename=r.imagen)` pero en Coolify los archivos estáticos pueden no servirse correctamente desde subcarpetas con rutas relativas.
- **Solución**: Se creó una ruta dedicada `/uploads/repuestos/<filename>` en `app/__init__.py` que sirve las imágenes correctamente usando `send_from_directory`.
- **Archivos actualizados**:
  - `app/__init__.py`: Nueva ruta `serve_repuesto_image`
  - `app/templates/repuestos/index.html`: Actualizada ruta de imagen
  - `app/templates/repuestos/form.html`: Actualizada vista previa de imagen
  - `app/templates/cliente_portal/tienda.html`: Actualizada ruta de imagen para clientes
  - `app/templates/base.html`: Actualizada ruta del logo
  - `app/templates/base_portal.html`: Actualizada ruta del logo

### 2. Panel admin se veía cortado en móvil
- **Causa**: Faltaba `viewport-fit=cover` y el sidebar no tenía un diseño móvil adecuado.
- **Solución**:
  - Agregado `viewport-fit=cover` y configuración de `user-scalable=no` en meta viewport
  - Mejorado el sidebar para móvil: posición fija, mejor z-index, scroll interno
  - Mejorado el overlay con backdrop-filter y transición suave
  - Agregado botón de cierre (X) en el sidebar para móvil
  - Ajustados tamaños de fuente, padding y espaciados para móvil
  - Usado `100dvh` (dynamic viewport height) para mejor compatibilidad móvil

## Variables de entorno recomendadas para Coolify:

```
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta_segura_aqui
DATABASE_URL=sqlite:///taller.db
UPLOAD_FOLDER=/app/app/static/uploads/repuestos
```

## Notas importantes:
1. Asegúrate de que la carpeta `uploads/repuestos` tenga permisos de escritura en el contenedor de Coolify
2. Si usas volúmenes persistentes en Coolify, monta la carpeta `app/static/uploads` para no perder las imágenes
3. En Coolify, configura un volumen: `/app/app/static/uploads:/app/app/static/uploads`

## Estructura de archivos esperada:
```
proyecto_final/
├── app/
│   ├── __init__.py (actualizado con nueva ruta)
│   ├── static/
│   │   └── uploads/
│   │       └── repuestos/ (debe tener permisos de escritura)
│   └── templates/
│       ├── base.html (mejorado responsive)
│       ├── base_portal.html (mejorado viewport)
│       ├── repuestos/
│       │   ├── index.html (ruta imagen corregida)
│       │   └── form.html (ruta imagen corregida)
│       └── cliente_portal/
│           └── tienda.html (ruta imagen corregida)
```

## Para hacer commit de los cambios:
```bash
cd /ruta/a/proyecto_final
git add .
git commit -m "Fix: Corregir carga de imágenes en producción y diseño móvil del admin"
git push
```
