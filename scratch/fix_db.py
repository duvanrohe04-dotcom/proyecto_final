import sqlite3
import os

db_path = r'c:\Users\ASUS\OneDrive\Desktop\proyecto_final\instance\taller.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Intentar agregar la columna id_compra a la tabla factura
        cursor.execute("ALTER TABLE factura ADD COLUMN id_compra INTEGER REFERENCES compra(id_compra) ON UPDATE CASCADE ON DELETE SET NULL")
        print("Columna 'id_compra' agregada a la tabla 'factura'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("La columna 'id_compra' ya existe.")
        else:
            print(f"Error al agregar columna: {e}")
            
    conn.commit()
    conn.close()
    print("Migración finalizada.")
else:
    print("No se encontró la base de datos.")
