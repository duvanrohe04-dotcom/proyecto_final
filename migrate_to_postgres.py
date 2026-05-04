#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
Ejecutar localmente antes de desplegar en Coolify:
1. Tener PostgreSQL instalado localmente o usar la URL de Coolify
2. pip install psycopg2-binary
3. python migrate_to_postgres.py
"""

import os
import sys

# URL de SQLite (origen)
SQLITE_URL = 'sqlite:///taller.db'

# URL de PostgreSQL (destino) - Reemplazar con tu URL
POSTGRES_URL = 'postgres://postgres:fAsgjW3bsrLbsBfrSIxltERDtu090hJGVQmiDheF8wL8tDnyxBXPYvUlwgd1u5c@xss53rbys91ky5kngduid77a:5432/postgres'

# Fix para SQLAlchemy
if POSTGRES_URL.startswith('postgres://'):
    POSTGRES_URL = POSTGRES_URL.replace('postgres://', 'postgresql://', 1)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# App temporal para SQLite
app_sqlite = Flask(__name__)
app_sqlite.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_URL
app_sqlite.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_sqlite = SQLAlchemy(app_sqlite)

# App temporal para PostgreSQL
app_pg = Flask(__name__)
app_pg.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URL
app_pg.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_pg = SQLAlchemy(app_pg)

# Importar modelos después de crear las instancias de db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.mecanico import Mecanico
from app.models.moto import Moto
from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto
from app.models.factura import Factura
from app.models.compra import Compra, CompraRepuesto
from app.models.resena import Resena
from app.models.config import Config

# Registrar modelos con ambas bases de datos
for model in [Usuario, Cliente, Mecanico, Moto, OrdenServicio, Repuesto, Factura, Compra, CompraRepuesto, Resena, Config]:
    if hasattr(model, '__tablename__'):
        model.__table__.tometadata(db_pg.Model.metadata)

def migrate():
    print("Iniciando migración de SQLite a PostgreSQL...")
    
    with app_sqlite.app_context():
        with app_pg.app_context():
            # Crear tablas en PostgreSQL
            db_pg.create_all()
            print("Tablas creadas en PostgreSQL")
            
            # Migrar datos tabla por tabla
            tables = [
                ('usuarios', Usuario),
                ('cliente', Cliente),
                ('mecanico', Mecanico),
                ('moto', Moto),
                ('orden_servicio', OrdenServicio),
                ('repuesto', Repuesto),
                ('factura', Factura),
                ('compra', Compra),
                ('compra_repuesto', CompraRepuesto),
                ('resena', Resena),
                ('config', Config),
            ]
            
            for table_name, model in tables:
                try:
                    records = model.query.all()
                    print(f"Migrando {len(records)} registros de {table_name}...")
                    
                    for record in records:
                        # Crear nuevo registro para PostgreSQL
                        new_record = model()
                        for column in model.__table__.columns:
                            if column.primary_key:
                                # Mantener el mismo ID
                                setattr(new_record, column.name, getattr(record, column.name))
                            else:
                                setattr(new_record, column.name, getattr(record, column.name))
                        
                        db_pg.session.add(new_record)
                    
                    db_pg.session.commit()
                    print(f"  ✓ {table_name} migrada exitosamente")
                    
                except Exception as e:
                    print(f"  ✗ Error migrando {table_name}: {str(e)}")
                    db_pg.session.rollback()
            
            print("\n¡Migración completada!")
            print(f"Total de usuarios: {Usuario.query.count()}")
            print(f"Total de clientes: {Cliente.query.count()}")
            print(f"Total de repuestos: {Repuesto.query.count()}")

if __name__ == '__main__':
    migrate()
