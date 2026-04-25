from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.cliente import Cliente
from app import db
from functools import wraps

bp = Blueprint('cliente', __name__, url_prefix='/clientes')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('clientes/index.html', clientes=clientes)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('clientes/form.html', accion='Agregar', cliente=None)
        nuevo = Cliente(nombre=nombre, telefono=telefono or None, direccion=direccion or None)
        db.session.add(nuevo)
        db.session.commit()
        flash('Cliente registrado exitosamente.', 'success')
        return redirect(url_for('cliente.index'))
    return render_template('clientes/form.html', accion='Agregar', cliente=None)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nombre = request.form['nombre'].strip()
        cliente.telefono = request.form.get('telefono', '').strip() or None
        cliente.direccion = request.form.get('direccion', '').strip() or None
        db.session.commit()
        flash('Cliente actualizado.', 'success')
        return redirect(url_for('cliente.index'))
    return render_template('clientes/form.html', accion='Editar', cliente=cliente)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    from app.models.usuario import Usuario
    cliente = Cliente.query.get_or_404(id)
    nombre = cliente.nombre

    # Eliminar usuario asociado si existe
    usuario = Usuario.query.filter_by(nombre_usuario=nombre).first()
    if not usuario:
        # Intentar por nombre.apellido
        partes = nombre.split()
        if len(partes) >= 2:
            nombre_usuario_gen = f"{partes[0].lower()}.{partes[-1].lower()}"
            usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario_gen).first()
    if usuario and not usuario.is_admin():
        db.session.delete(usuario)

    db.session.delete(cliente)
    db.session.commit()
    flash(f'Cliente "{nombre}" y todos sus datos eliminados.', 'info')
    return redirect(url_for('cliente.index'))

@bp.route('/detalle/<int:id>')
@login_required
@admin_required
def detalle(id):
    cliente = Cliente.query.get_or_404(id)
    return render_template('clientes/detalle.html', cliente=cliente)
