import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("La variable de entorno DATABASE_URL no está configurada.")
    if not app.config['SECRET_KEY']:
        raise ValueError("La variable de entorno SECRET_KEY no está configurada.")
        
    # Fix para URLs de PostgreSQL en algunos proveedores que usan postgres:// en lugar de postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Asegurar ruta correcta para UPLOAD_FOLDER basada en root_path
    default_upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'repuestos')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', default_upload_folder)

    # Asegurar que la carpeta de subidas existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'

    from app.models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from app.routes.auth import bp as auth_bp
    from app.routes.cliente_routes import bp as cliente_bp
    from app.routes.mecanico_routes import bp as mecanico_bp
    from app.routes.moto_routes import bp as moto_bp
    from app.routes.orden_routes import bp as orden_bp
    from app.routes.repuesto_routes import bp as repuesto_bp
    from app.routes.factura_routes import bp as factura_bp
    from app.routes.admin_routes import bp as admin_bp
    from app.routes.portal_routes import bp as portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(mecanico_bp)
    app.register_blueprint(moto_bp)
    app.register_blueprint(orden_bp)
    app.register_blueprint(repuesto_bp)
    app.register_blueprint(factura_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(portal_bp)

    # Servir archivos estáticos desde uploads con ruta dedicada
    @app.route('/uploads/repuestos/<filename>')
    def serve_repuesto_image(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Procesador de contexto para variables globales (Nombre de App, Logo, Redes)
    @app.context_processor
    def inject_settings():
        from app.models.config import Config
        return {
            'app_name': Config.get_val('app_name', 'MotoTaller Pro'),
            'app_logo': Config.get_val('app_logo', None),
            'app_instagram': Config.get_val('app_instagram', ''),
            'app_whatsapp': Config.get_val('app_whatsapp', ''),
        }

    # Health check para Coolify / Docker
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    # Redirigir raíz a login si no hay usuario
    @app.route('/')
    def root():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.admin_root', admin_id=current_user.id))
            return redirect(url_for('portal.dashboard'))
        return redirect(url_for('auth.login'))

    return app
