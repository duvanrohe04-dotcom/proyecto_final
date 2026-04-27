from app import db
from datetime import date

class Compra(db.Model):
    __tablename__ = 'compra'
    id_compra = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente', onupdate='CASCADE', ondelete='SET NULL'), nullable=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    estado = db.Column(db.String(20), nullable=False, default='solicitud') # solicitud, entregado, cancelado
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    cliente = db.relationship('Cliente', back_populates='compras')
    repuestos = db.relationship('CompraRepuesto', back_populates='compra', lazy='dynamic', cascade='all, delete-orphan')
    factura = db.relationship('Factura', back_populates='compra', uselist=False)

    def __repr__(self):
        return f'<Compra {self.id_compra}>'

class CompraRepuesto(db.Model):
    __tablename__ = 'compra_repuesto'
    id_compra_repuesto = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(db.Integer, db.ForeignKey('compra.id_compra', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    id_repuesto = db.Column(db.Integer, db.ForeignKey('repuesto.id_repuesto', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Numeric(10, 2)) # Valor total por este item (cantidad * precio_unitario)

    compra = db.relationship('Compra', back_populates='repuestos')
    repuesto = db.relationship('Repuesto')

    def __repr__(self):
        return f'<CompraRepuesto {self.id_compra_repuesto}>'
