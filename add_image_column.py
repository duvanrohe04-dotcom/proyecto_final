import sqlite3
import os

db_path = 'instance/taller.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE repuesto ADD COLUMN imagen VARCHAR(255)")
        conn.commit()
        print("Columna 'imagen' añadida exitosamente.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("La columna 'imagen' ya existe.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("La base de datos no existe aún.")
