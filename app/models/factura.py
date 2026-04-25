from app import db
from datetime import date

class Factura(db.Model):
    __tablename__ = 'factura'
    id_factura = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente', onupdate='CASCADE', ondelete='SET NULL'), nullable=True)
    id_servicio = db.Column(db.Integer, db.ForeignKey('orden_servicio.id_servicio', onupdate='CASCADE', ondelete='SET NULL'), nullable=True)
    id_compra = db.Column(db.Integer, db.ForeignKey('compra.id_compra', onupdate='CASCADE', ondelete='SET NULL'), nullable=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    cliente = db.relationship('Cliente', back_populates='facturas')
    orden = db.relationship('OrdenServicio', back_populates='facturas')
    compra = db.relationship('Compra', back_populates='factura')

    def __repr__(self):
        return f'<Factura {self.id_factura}>'
