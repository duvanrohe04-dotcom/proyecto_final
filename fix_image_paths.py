"""
Script para corregir rutas de imágenes en la base de datos.
Ejecutar: venv/Scripts/python fix_image_paths.py
"""
import sqlite3
import os

DB_PATH = os.path.join('instance', 'taller.db')

def fix_image_paths():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Obtener todos los repuestos con sus imágenes
    cur.execute("SELECT id_repuesto, imagen FROM repuesto WHERE imagen IS NOT NULL")
    repuestos = cur.fetchall()
    
    print(f"Found {len(repuestos)} repuestos con imágenes")
    
    for id_rep, imagen in repuestos:
        if not imagen.startswith('http'):
            # Si la ruta no es una URL y no tiene 'static/', agregar 'static/'
            if not imagen.startswith('static/'):
                nueva_ruta = f"static/{imagen}"
                print(f"  Repuesto {id_rep}: '{imagen}' -> '{nueva_ruta}'")
                cur.execute("UPDATE repuesto SET imagen = ? WHERE id_repuesto = ?", (nueva_ruta, id_rep))
    
    conn.commit()
    conn.close()
    print("\n✅ Rutas corregidas.")

if __name__ == '__main__':
    fix_image_paths()
