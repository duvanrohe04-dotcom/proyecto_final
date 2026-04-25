from app import db

class Mecanico(db.Model):
    __tablename__ = 'mecanico'
    id_mecanico = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(20))
    especialidad = db.Column(db.String(50))

    ordenes = db.relationship('OrdenServicio', back_populates='mecanico', lazy='dynamic')

    def __repr__(self):
        return f'<Mecanico {self.nombre}>'
