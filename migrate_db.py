"""
Script de migración: agrega columnas nombre y apellido a la tabla usuarios
y crea los índices de optimización.
Ejecutar una sola vez: venv/Scripts/python migrate_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join('instance', 'taller.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verificar columnas existentes
    cur.execute("PRAGMA table_info(usuarios)")
    cols = [row[1] for row in cur.fetchall()]

    if 'nombre' not in cols:
        cur.execute("ALTER TABLE usuarios ADD COLUMN nombre VARCHAR(50)")
        print("✅ Columna 'nombre' agregada a usuarios")
    else:
        print("ℹ️  Columna 'nombre' ya existe")

    if 'apellido' not in cols:
        cur.execute("ALTER TABLE usuarios ADD COLUMN apellido VARCHAR(50)")
        print("✅ Columna 'apellido' agregada a usuarios")
    else:
        print("ℹ️  Columna 'apellido' ya existe")

    # Índices de optimización
    indices = [
        ("CREATE INDEX IF NOT EXISTS ix_usuarios_nombre_usuario ON usuarios(nombre_usuario)", "ix_usuarios_nombre_usuario"),
        ("CREATE INDEX IF NOT EXISTS ix_usuarios_rol ON usuarios(rol)", "ix_usuarios_rol"),
        ("CREATE INDEX IF NOT EXISTS ix_cliente_nombre ON cliente(nombre)", "ix_cliente_nombre"),
        ("CREATE INDEX IF NOT EXISTS ix_orden_fecha_hora ON orden_servicio(fecha, hora)", "ix_orden_fecha_hora"),
        ("CREATE INDEX IF NOT EXISTS ix_orden_estado ON orden_servicio(estado)", "ix_orden_estado"),
        ("CREATE INDEX IF NOT EXISTS ix_orden_id_moto ON orden_servicio(id_moto)", "ix_orden_id_moto"),
        ("CREATE INDEX IF NOT EXISTS ix_compra_id_cliente ON compra(id_cliente)", "ix_compra_id_cliente"),
        ("CREATE INDEX IF NOT EXISTS ix_compra_estado ON compra(estado)", "ix_compra_estado"),
        ("CREATE INDEX IF NOT EXISTS ix_resena_id_usuario ON resena(id_usuario)", "ix_resena_id_usuario"),
    ]

    for sql, nombre in indices:
        try:
            cur.execute(sql)
            print(f"✅ Índice '{nombre}' creado")
        except sqlite3.OperationalError as e:
            print(f"ℹ️  {nombre}: {e}")

    # Activar WAL mode
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    print("✅ WAL mode activado")
    
    # Corregir rutas de imágenes
    cur.execute("SELECT id_repuesto, imagen FROM repuesto WHERE imagen IS NOT NULL AND NOT imagen LIKE 'http%' AND NOT imagen LIKE 'static/%'")
    repuestos = cur.fetchall()
    for id_rep, imagen in repuestos:
        cur.execute("UPDATE repuesto SET imagen = ? WHERE id_repuesto = ?", (f"static/{imagen}", id_rep))
    if repuestos:
        print(f"✅ Rutas de {len(repuestos)} imágenes corregidas")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada.")

if __name__ == '__main__':
    migrate()
