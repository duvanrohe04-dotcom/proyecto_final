from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuario import Usuario
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.usuarios'))
        return redirect(url_for('portal.dashboard'))

    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        password = request.form['password']
        user = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'¡Bienvenido, {user.nombre_usuario}!', 'success')
            if user.is_admin():
                return redirect(url_for('admin.usuarios'))
            return redirect(url_for('portal.dashboard'))

        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if not nombre_usuario:
            flash('El nombre no puede estar vacío.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html')
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash('Ese nombre de usuario ya existe.', 'warning')
            return render_template('register.html')

        new_user = Usuario(nombre_usuario=nombre_usuario, rol='cliente')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('¡Cuenta creada! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))
