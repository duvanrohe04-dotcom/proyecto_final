from app import db

class Moto(db.Model):
    __tablename__ = 'moto'
    id_moto = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), nullable=False, unique=True)
    tipo = db.Column(db.String(50))
    modelo = db.Column(db.Integer)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)

    cliente = db.relationship('Cliente', back_populates='motos')
    ordenes = db.relationship('OrdenServicio', back_populates='moto', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Moto {self.placa}>'
