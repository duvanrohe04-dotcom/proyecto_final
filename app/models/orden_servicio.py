from app import db
from datetime import date, time

class OrdenServicio(db.Model):
    __tablename__ = 'orden_servicio'
    id_servicio = db.Column(db.Integer, primary_key=True)
    id_moto = db.Column(db.Integer, db.ForeignKey('moto.id_moto', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    id_mecanico = db.Column(db.Integer, db.ForeignKey('mecanico.id_mecanico', onupdate='CASCADE', ondelete='SET NULL'), nullable=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    hora = db.Column(db.String(5), nullable=True)  # Ej: "09:00"
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    valor = db.Column(db.Numeric(10, 2))
    es_cita_cliente = db.Column(db.Boolean, default=False)
    descripcion = db.Column(db.String(300))

    moto = db.relationship('Moto', back_populates='ordenes')
    mecanico = db.relationship('Mecanico', back_populates='ordenes')
    repuestos = db.relationship('OrdenRepuesto', back_populates='orden', lazy='dynamic', cascade='all, delete-orphan')
    facturas = db.relationship('Factura', back_populates='orden', lazy='dynamic')

    ESTADOS = ['pendiente', 'en_proceso', 'completado', 'cancelado']
    HORAS = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00']

    def __repr__(self):
        return f'<OrdenServicio {self.id_servicio}>'
