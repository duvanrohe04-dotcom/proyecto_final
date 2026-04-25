import sys
import os

sys.path.append(os.getcwd())

try:
    from app import create_app, db
    from app.models.config import Config
    
    app = create_app()
    with app.app_context():
        db.create_all()
        # Opcional: Insertar valores por defecto
        if not Config.query.filter_by(key='app_name').first():
            db.session.add(Config(key='app_name', value='MotoTaller Pro'))
            db.session.commit()
            print("Base de datos inicializada y valores por defecto agregados.")
        else:
            print("Base de datos ya estaba inicializada.")
except Exception as e:
    print(f"Error: {e}")
