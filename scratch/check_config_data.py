import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app, db
import sqlite3

app = create_app()

with app.app_context():
    conn = sqlite3.connect('instance/taller.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM config')
    result = cur.fetchall()
    print("Contenido de la tabla config:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")
    conn.close()
