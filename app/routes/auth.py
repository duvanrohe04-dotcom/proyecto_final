import logging
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuario import Usuario
from app import db, limiter

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Solo letras, números, puntos, guiones y guiones bajos — sin HTML ni SQL
_SAFE_USERNAME = re.compile(r'^[\w.\-]{1,80}$')

@bp.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('cliente.index'))
        return redirect(url_for('portal.dashboard'))

    if request.method == 'POST':
        entrada = request.form.get('nombre_usuario', '').strip()[:80]
        password = request.form.get('password', '')

        if not entrada or not password:
            flash('Completa todos los campos.', 'danger')
            return render_template('login.html')

        # Buscar directamente (admin u usuario con nombre exacto)
        user = Usuario.query.filter_by(nombre_usuario=entrada).first()

        # Intentar "Nombre Apellido" → "nombre.apellido"
        if not user:
            partes = entrada.split()
            if len(partes) >= 2:
                nombre_usuario_gen = f"{partes[0].lower()}.{partes[-1].lower()}"
                user = Usuario.query.filter_by(nombre_usuario=nombre_usuario_gen).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'¡Bienvenido, {user.nombre_usuario}!', 'success')
            # Redirigir a la URL solicitada originalmente si existe y es segura
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            if user.is_admin():
                return redirect(url_for('cliente.index'))
            return redirect(url_for('portal.dashboard'))

        logger.warning(f'Login fallido para usuario: "{entrada}" desde IP: {request.remote_addr}')
        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()[:50]
        apellido = request.form.get('apellido', '').strip()[:50]
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Validaciones
        if not nombre or not apellido:
            flash('El nombre y apellido son obligatorios.', 'danger')
            return render_template('register.html')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$', nombre):
            flash('El nombre solo puede contener letras.', 'danger')
            return render_template('register.html')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$', apellido):
            flash('El apellido solo puede contener letras.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('register.html')
        if len(password) > 128:
            flash('La contraseña es demasiado larga.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html')

        # Generar nombre de usuario: nombre.apellido en minúsculas
        nombre_usuario = f"{nombre.lower().replace(' ', '')}.{apellido.lower().replace(' ', '')}"
        base = nombre_usuario
        counter = 1
        while Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            nombre_usuario = f"{base}{counter}"
            counter += 1

        new_user = Usuario(nombre_usuario=nombre_usuario, rol='cliente')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        logger.info(f'Nuevo usuario registrado: {nombre_usuario}')
        flash(f'¡Cuenta creada! Tu usuario es: {nombre_usuario}. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@bp.route('/logout')
@login_required
def logout():
    logger.info(f'Sesión cerrada: {current_user.nombre_usuario}')
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))
