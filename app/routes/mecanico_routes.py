from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.mecanico import Mecanico
from app import db
from functools import wraps

bp = Blueprint('mecanico', __name__, url_prefix='/mecanicos')

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
    mecanicos = Mecanico.query.order_by(Mecanico.nombre).all()
    return render_template('mecanicos/index.html', mecanicos=mecanicos)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        telefono = request.form.get('telefono', '').strip()
        especialidad = request.form.get('especialidad', '').strip()
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('mecanicos/form.html', accion='Agregar', mecanico=None)
        nuevo = Mecanico(nombre=nombre, telefono=telefono or None, especialidad=especialidad or None)
        db.session.add(nuevo)
        db.session.commit()
        flash('Mecánico registrado exitosamente.', 'success')
        return redirect(url_for('mecanico.index'))
    return render_template('mecanicos/form.html', accion='Agregar', mecanico=None)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    mecanico = Mecanico.query.get_or_404(id)
    if request.method == 'POST':
        mecanico.nombre = request.form['nombre'].strip()
        mecanico.telefono = request.form.get('telefono', '').strip() or None
        mecanico.especialidad = request.form.get('especialidad', '').strip() or None
        db.session.commit()
        flash('Mecánico actualizado.', 'success')
        return redirect(url_for('mecanico.index'))
    return render_template('mecanicos/form.html', accion='Editar', mecanico=mecanico)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    mecanico = Mecanico.query.get_or_404(id)
    db.session.delete(mecanico)
    db.session.commit()
    flash('Mecánico eliminado.', 'info')
    return redirect(url_for('mecanico.index'))
@bp.route('/detalle/<int:id>')
@login_required
@admin_required
def detalle(id):
    mecanico = Mecanico.query.get_or_404(id)
    from app.models.orden_servicio import OrdenServicio
    ordenes = mecanico.ordenes.order_by(OrdenServicio.fecha.desc()).all()
    return render_template('mecanicos/detalle.html', mecanico=mecanico, ordenes=ordenes)

