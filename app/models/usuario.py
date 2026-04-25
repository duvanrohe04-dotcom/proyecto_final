from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(150), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(50), nullable=True)
    apellido = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='cliente', index=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.rol == 'admin'

    @property
    def nombre_completo(self):
        if self.nombre and self.apellido:
            return f"{self.nombre} {self.apellido}"
        return self.nombre_usuario

    def to_dict(self):
        return {'id': self.id, 'nombre_usuario': self.nombre_usuario,
                'nombre': self.nombre, 'apellido': self.apellido, 'rol': self.rol}
