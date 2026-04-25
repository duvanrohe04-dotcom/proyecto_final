from app import db

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, index=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(100))

    motos = db.relationship('Moto', back_populates='cliente', lazy='dynamic')
    facturas = db.relationship('Factura', back_populates='cliente', lazy='dynamic')
    compras = db.relationship('Compra', back_populates='cliente', lazy='dynamic')

    def __repr__(self):
        return f'<Cliente {self.nombre}>'
