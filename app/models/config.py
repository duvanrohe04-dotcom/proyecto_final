from app import db

class Config(db.Model):
    __tablename__ = 'config'
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=True)

    @staticmethod
    def get_val(key, default=None):
        item = Config.query.get(key)
        return item.value if item else default

    @staticmethod
    def set_val(key, value):
        item = Config.query.get(key)
        if item:
            item.value = value
        else:
            item = Config(key=key, value=value)
            db.session.add(item)
        db.session.commit()
