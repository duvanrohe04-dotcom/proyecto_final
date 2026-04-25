from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.factura import Factura
from app.models.cliente import Cliente
from app.models.orden_servicio import OrdenServicio
from app import db
from datetime import date
from functools import wraps

bp = Blueprint('factura', __name__, url_prefix='/facturas')

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
    # Limpiar facturas antiguas de órdenes no completadas/entregadas (generadas por datos de prueba)
    facturas_invalidas = Factura.query.join(OrdenServicio).filter(~OrdenServicio.estado.in_(['completado', 'entregado'])).all()
    if facturas_invalidas:
        for f in facturas_invalidas:
            db.session.delete(f)
        db.session.commit()

    facturas = Factura.query.order_by(Factura.fecha.desc()).all()
    return render_template('facturas/index.html', facturas=facturas)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    # Mostrar solo órdenes que ya están completadas o entregadas
    ordenes = OrdenServicio.query.filter(OrdenServicio.estado.in_(['completado', 'entregado'])).order_by(OrdenServicio.id_servicio.desc()).all()
    if request.method == 'POST':
        id_cliente = request.form.get('id_cliente') or None
        id_servicio = request.form.get('id_servicio') or None
        fecha_str = request.form['fecha']
        total = request.form['total'].strip()
        if not total:
            flash('El total es obligatorio.', 'danger')
            return render_template('facturas/form.html', accion='Agregar', factura=None, clientes=clientes, ordenes=ordenes)
        nueva = Factura(
            id_cliente=int(id_cliente) if id_cliente else None,
            id_servicio=int(id_servicio) if id_servicio else None,
            fecha=date.fromisoformat(fecha_str),
            total=float(total)
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Factura generada exitosamente.', 'success')
        return redirect(url_for('factura.index'))
    return render_template('facturas/form.html', accion='Agregar', factura=None, clientes=clientes, ordenes=ordenes)

@bp.route('/ver/<int:id>')
@login_required
@admin_required
def ver(id):
    factura = Factura.query.get_or_404(id)
    return render_template('facturas/ver.html', factura=factura)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    factura = Factura.query.get_or_404(id)
    db.session.delete(factura)
    db.session.commit()
    flash('Factura eliminada.', 'info')
    return redirect(url_for('factura.index'))
