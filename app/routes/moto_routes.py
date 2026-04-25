from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.moto import Moto
from app.models.cliente import Cliente
from app import db
from functools import wraps

bp = Blueprint('moto', __name__, url_prefix='/motos')

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
    motos = Moto.query.join(Cliente).order_by(Cliente.nombre).all()
    return render_template('motos/index.html', motos=motos)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    if request.method == 'POST':
        placa = request.form['placa'].strip().upper()
        tipo = request.form.get('tipo', '').strip()
        modelo = request.form.get('modelo', '').strip()
        id_cliente = request.form['id_cliente']
        if not placa or not id_cliente:
            flash('Placa y cliente son obligatorios.', 'danger')
            return render_template('motos/form.html', accion='Agregar', moto=None, clientes=clientes)
        if Moto.query.filter_by(placa=placa).first():
            flash('Ya existe una moto con esa placa.', 'warning')
            return render_template('motos/form.html', accion='Agregar', moto=None, clientes=clientes)
        nueva = Moto(
            placa=placa,
            tipo=tipo or None,
            modelo=int(modelo) if modelo else None,
            id_cliente=int(id_cliente)
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Moto registrada exitosamente.', 'success')
        return redirect(url_for('moto.index'))
    return render_template('motos/form.html', accion='Agregar', moto=None, clientes=clientes)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    moto = Moto.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    if request.method == 'POST':
        placa_nueva = request.form['placa'].strip().upper()
        existente = Moto.query.filter_by(placa=placa_nueva).first()
        if existente and existente.id_moto != moto.id_moto:
            flash('Ya existe otra moto con esa placa.', 'warning')
            return render_template('motos/form.html', accion='Editar', moto=moto, clientes=clientes)
        moto.placa = placa_nueva
        moto.tipo = request.form.get('tipo', '').strip() or None
        modelo = request.form.get('modelo', '').strip()
        moto.modelo = int(modelo) if modelo else None
        moto.id_cliente = int(request.form['id_cliente'])
        db.session.commit()
        flash('Moto actualizada.', 'success')
        return redirect(url_for('moto.index'))
    return render_template('motos/form.html', accion='Editar', moto=moto, clientes=clientes)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    moto = Moto.query.get_or_404(id)
    db.session.delete(moto)
    db.session.commit()
    flash('Moto eliminada.', 'info')
    return redirect(url_for('moto.index'))

@bp.route('/historial/<int:id>')
@login_required
@admin_required
def historial(id):
    moto = Moto.query.get_or_404(id)
    # Obtener todas las órdenes de servicio para esta moto, ordenadas por fecha descendente
    from app.models.orden_servicio import OrdenServicio
    ordenes = OrdenServicio.query.filter_by(id_moto=moto.id_moto).order_by(OrdenServicio.fecha.desc(), OrdenServicio.hora.desc()).all()
    return render_template('motos/historial.html', moto=moto, ordenes=ordenes)
