from app import db

class Repuesto(db.Model):
    __tablename__ = 'repuesto'
    id_repuesto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    imagen = db.Column(db.String(255), nullable=True)

    orden_repuestos = db.relationship('OrdenRepuesto', back_populates='repuesto', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Repuesto {self.nombre}>'


class OrdenRepuesto(db.Model):
    __tablename__ = 'orden_repuesto'
    id_orden_repuesto = db.Column(db.Integer, primary_key=True)
    id_servicio = db.Column(db.Integer, db.ForeignKey('orden_servicio.id_servicio', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    id_repuesto = db.Column(db.Integer, db.ForeignKey('repuesto.id_repuesto', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Numeric(10, 2))

    orden = db.relationship('OrdenServicio', back_populates='repuestos')
    repuesto = db.relationship('Repuesto', back_populates='orden_repuestos')

    def __repr__(self):
        return f'<OrdenRepuesto {self.id_orden_repuesto}>'
