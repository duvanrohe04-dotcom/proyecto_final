from app import create_app, db
from app.models.orden_servicio import OrdenServicio
from app.models.moto import Moto
from app.models.cliente import Cliente
from sqlalchemy import case

app = create_app()
with app.app_context():
    try:
        search_query = ''
        query = OrdenServicio.query.join(Moto).join(Cliente)
        
        orden_estados = case(
            (OrdenServicio.estado == 'completado', 1),
            (OrdenServicio.estado == 'en_proceso', 2),
            (OrdenServicio.estado == 'pendiente', 3),
            (OrdenServicio.estado == 'cancelado', 4),
            else_=5
        )
        ordenes = query.order_by(orden_estados, OrdenServicio.fecha.desc()).all()
        print(f"Successfully fetched {len(ordenes)} orders")
    except Exception as e:
        print(f"Error: {e}")
