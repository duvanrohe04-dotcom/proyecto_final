import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["300 per day", "60 per hour"])

# Extensiones permitidas para subida de archivos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_UPLOAD_MB = 5

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__)

    # ── CONFIGURACIÓN ──────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-inseguro-cambiar')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///taller.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads', 'repuestos')
    app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024  # 5 MB máximo por subida

    # Pool de conexiones — evita saturación bajo carga
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,     # verifica conexión antes de usarla
        'pool_recycle': 1800,      # recicla conexiones cada 30 min
        'connect_args': {
            'check_same_thread': False,  # SQLite multi-hilo
            'timeout': 20,              # espera hasta 20s por lock
        }
    }

    # Cookies seguras
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = 3600  # 1 hora

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── EXTENSIONES ────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Activar WAL mode en SQLite para mejor concurrencia
    from sqlalchemy import event, text
    from sqlalchemy.engine import Engine
    import sqlite3

    @event.listens_for(Engine, 'connect')
    def set_sqlite_pragma(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            cursor = dbapi_conn.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')    # activar claves foráneas y cascadas
            cursor.execute('PRAGMA journal_mode=WAL')   # escrituras no bloquean lecturas
            cursor.execute('PRAGMA synchronous=NORMAL') # balance velocidad/seguridad
            cursor.execute('PRAGMA cache_size=-32000')  # 32 MB de caché en memoria
            cursor.execute('PRAGMA temp_store=MEMORY')  # tablas temporales en RAM
            cursor.execute('PRAGMA mmap_size=268435456')# 256 MB memory-mapped I/O
            cursor.close()

    # Headers de seguridad HTTP con Talisman
    csp = {
        'default-src': ["'self'", 'https:'],
        'script-src':  ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com'],
        'style-src':   ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com', 'https://fonts.googleapis.com'],
        'font-src':    ["'self'", 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com'],
        'img-src':     ["'self'", 'data:', 'https:'],
        'frame-ancestors': ["'none'"],
    }
    Talisman(
        app,
        content_security_policy=csp,
        force_https=False,
        strict_transport_security=False,
        frame_options='DENY',
        referrer_policy='strict-origin-when-cross-origin',
        feature_policy={
            'geolocation': "'none'",
            'camera': "'none'",
            'microphone': "'none'",
        }
    )

    # ── LOGIN MANAGER ──────────────────────────────────────────
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'

    from app.models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # ── BLUEPRINTS ─────────────────────────────────────────────
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

    # ── CONTEXTO GLOBAL ────────────────────────────────────────
    @app.context_processor
    def inject_settings():
        from app.models.config import Config
        return {
            'app_name':      Config.get_val('app_name', 'MotoTaller Pro'),
            'app_logo':      Config.get_val('app_logo', None),
            'app_instagram': Config.get_val('app_instagram', ''),
            'app_whatsapp':  Config.get_val('app_whatsapp', ''),
        }

    # ── MANEJO DE ERRORES ──────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, request as req
        flash(f'El archivo es demasiado grande. Máximo {MAX_UPLOAD_MB} MB.', 'danger')
        return redirect(req.referrer or '/'), 413

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        from flask import flash, redirect, request as req
        flash('Token de seguridad inválido o expirado. Por favor intenta de nuevo.', 'danger')
        return redirect(req.referrer or '/'), 400

    # ── LOGGING ────────────────────────────────────────────────
    if not app.debug:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        handler = RotatingFileHandler('logs/motortaller.log', maxBytes=1_000_000, backupCount=3)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(handler)

    return app
