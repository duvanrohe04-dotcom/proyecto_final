"""Crea la tabla de reseñas en la base de datos existente."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.usuario import Usuario
from app.models.resena import Resena

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Tabla 'resena' creada exitosamente.")
