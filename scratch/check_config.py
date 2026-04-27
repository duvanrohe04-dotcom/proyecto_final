import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app, db
import sqlite3

app = create_app()

with app.app_context():
    # Usar sqlite3 directamente
    conn = sqlite3.connect('instance/taller.db')
    cur = conn.cursor()
    cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="config"')
    result = cur.fetchall()
    print('Tabla config existe:', len(result) > 0)
    
    if len(result) > 0:
        print("✅ La tabla config ya existe")
    else:
        print("La tabla config NO EXISTE. Creando...")
        db.create_all()
        print("✅ Tabla config creada")
        
        # Insertar valores por defecto
        from app.models.config import Config
        if not Config.query.filter_by(key='app_name').first():
            db.session.add(Config(key='app_name', value='MotoTaller Pro'))
            db.session.add(Config(key='app_logo', value=None))
            db.session.add(Config(key='app_instagram', value=''))
            db.session.add(Config(key='app_whatsapp', value=''))
            db.session.commit()
            print("✅ Configuración por defecto insertada")
    
    conn.close()
