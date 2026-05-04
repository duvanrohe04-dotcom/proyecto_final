"""
Script para verificar y corregir el logo en la base de datos.
Ejecutar: python fix_logo.py
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.config import Config

def fix_logo():
    app = create_app()
    with app.app_context():
        # Obtener el logo actual
        logo = Config.get_val('app_logo', None)
        print(f"Logo actual: {logo}")
        
        if logo:
            # Si es una ruta local (no URL)
            if not logo.startswith('http'):
                # Limpiar la ruta para obtener solo el nombre del archivo
                filename = logo.split('/')[-1]
                
                # Verificar si el archivo existe en uploads/repuestos
                upload_path = os.path.join('app', 'static', 'uploads', 'repuestos', filename)
                
                if os.path.exists(upload_path):
                    print(f"✅ El archivo {filename} existe en {upload_path}")
                    # Asegurar que la ruta en DB sea correcta
                    correct_path = f"static/uploads/repuestos/{filename}"
                    if logo != correct_path:
                        Config.set_val('app_logo', correct_path)
                        print(f"✅ Ruta del logo actualizada a: {correct_path}")
                    else:
                        print("✅ La ruta del logo ya es correcta")
                else:
                    print(f"❌ El archivo {filename} NO existe en {upload_path}")
                    print("   Verifica que el volumen en Coolify esté montado correctamente")
        else:
            print("No hay logo configurado en la base de datos")
            print("Puedes subir un logo desde el panel de administración en /admin/ajustes")

if __name__ == '__main__':
    fix_logo()
