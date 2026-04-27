import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.repuesto import Repuesto
from app import db
from functools import wraps

bp = Blueprint('repuesto', __name__, url_prefix='/repuestos')

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
    repuestos = Repuesto.query.order_by(Repuesto.nombre).all()
    return render_template('repuestos/index.html', repuestos=repuestos)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        valor = request.form['valor'].strip()
        url_imagen = request.form.get('url_imagen', '').strip()
        archivo_imagen = request.files.get('archivo_imagen')

        if not nombre or not valor:
            flash('Nombre y valor son obligatorios.', 'danger')
            return render_template('repuestos/form.html', accion='Agregar', repuesto=None)

        nuevo = Repuesto(nombre=nombre, valor=float(valor))

        # Prioridad: Archivo subido > URL > Nada
        if archivo_imagen and archivo_imagen.filename:
            filename = secure_filename(f"rep_{nombre}_{archivo_imagen.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            archivo_imagen.save(filepath)
            nuevo.imagen = f"uploads/repuestos/{filename}"
        elif url_imagen:
            nuevo.imagen = url_imagen

        db.session.add(nuevo)
        db.session.commit()
        flash('Producto registrado en el Catálogo.', 'success')
        return redirect(url_for('repuesto.index'))
    return render_template('repuestos/form.html', accion='Agregar', repuesto=None)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    repuesto = Repuesto.query.get_or_404(id)
    if request.method == 'POST':
        repuesto.nombre = request.form['nombre'].strip()
        repuesto.valor = float(request.form['valor'])
        
        url_imagen = request.form.get('url_imagen', '').strip()
        archivo_imagen = request.files.get('archivo_imagen')

        if archivo_imagen and archivo_imagen.filename:
            filename = secure_filename(f"rep_{repuesto.nombre}_{archivo_imagen.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            archivo_imagen.save(filepath)
            repuesto.imagen = f"uploads/repuestos/{filename}"
        elif url_imagen:
            repuesto.imagen = url_imagen

        db.session.commit()
        flash('Producto del Catálogo actualizado.', 'success')
        return redirect(url_for('repuesto.index'))
    return render_template('repuestos/form.html', accion='Editar', repuesto=repuesto)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    repuesto = Repuesto.query.get_or_404(id)
    db.session.delete(repuesto)
    db.session.commit()
    flash('Producto eliminado del Catálogo.', 'info')
    return redirect(url_for('repuesto.index'))
