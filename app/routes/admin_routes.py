from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.compra import Compra
from app.models.factura import Factura
from app import db
from functools import wraps
from datetime import date

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acceso restringido a administradores.', 'danger')
            admin_id = kwargs.get('admin_id', 1)
            return redirect(url_for('admin.admin_login', admin_id=admin_id))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login/<int:admin_id>', methods=['GET', 'POST'])
def admin_login(admin_id):
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.admin_root', admin_id=admin_id))
        return redirect(url_for('portal.dashboard'))

    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        password = request.form['password']
        user = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if user and user.check_password(password):
            if not user.is_admin():
                flash('Acceso denegado. Solo administradores.', 'danger')
                return render_template('admin/login.html', admin_id=admin_id)
            login_user(user)
            flash(f'¡Bienvenido, Administrador {user.nombre_usuario}!', 'success')
            return redirect(url_for('admin.admin_root', admin_id=admin_id))

        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('admin/login.html', admin_id=admin_id)

@bp.route('/<int:admin_id>')
@login_required
@admin_required
def admin_root(admin_id):
    from app.models.usuario import Usuario
    from app.models.cliente import Cliente
    from app.models.orden_servicio import OrdenServicio
    from app.models.compra import Compra
    from app.models.factura import Factura
    from sqlalchemy import func
    from datetime import date

    stats = {
        'total_usuarios': Usuario.query.count(),
        'total_clientes': Cliente.query.count(),
        'ordenes_pendientes': OrdenServicio.query.filter_by(estado='pendiente').count(),
        'ordenes_en_proceso': OrdenServicio.query.filter_by(estado='en_proceso').count(),
        'compras_solicitud': Compra.query.filter_by(estado='solicitud').count(),
        'facturas_hoy': Factura.query.filter(Factura.fecha == date.today()).count(),
        'total_ventas_hoy': db.session.query(func.coalesce(func.sum(Factura.total), 0)).filter(Factura.fecha == date.today()).scalar(),
    }
    return render_template('admin/welcome.html', admin_id=admin_id, stats=stats, usuario=current_user)

@bp.route('/usuarios/<int:admin_id>')
@login_required
@admin_required
def usuarios(admin_id):
    users = Usuario.query.order_by(Usuario.rol, Usuario.nombre_usuario).all()
    return render_template('admin/usuarios.html', users=users)

@bp.route('/usuarios/agregar/<int:admin_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar_usuario(admin_id):
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario'].strip()
        password = request.form['password']
        rol = request.form.get('rol', 'cliente')
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()

        if not nombre_usuario or not password:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/form_usuario.html', accion='Agregar', user=None)
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('admin/form_usuario.html', accion='Agregar', user=None)
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash('Ese nombre de usuario ya existe.', 'warning')
            return render_template('admin/form_usuario.html', accion='Agregar', user=None)

        nuevo = Usuario(nombre_usuario=nombre_usuario, rol=rol)
        nuevo.set_password(password)
        db.session.add(nuevo)

        # Si es cliente, crear también en tabla clientes
        if rol == 'cliente':
            if not Cliente.query.filter_by(nombre=nombre_usuario).first():
                nuevo_cliente = Cliente(
                    nombre=nombre_usuario,
                    telefono=telefono or None,
                    direccion=direccion or None
                )
                db.session.add(nuevo_cliente)

        db.session.commit()
        flash(f'Usuario "{nombre_usuario}" creado exitosamente.', 'success')
        return redirect(url_for('admin.usuarios', admin_id=admin_id))

    return render_template('admin/form_usuario.html', accion='Agregar', user=None)

@bp.route('/usuarios/editar/<int:admin_id>/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(admin_id, id):
    user = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        nueva_password = request.form.get('password', '').strip()
        nuevo_rol = request.form.get('rol', user.rol)

        if nueva_password:
            if len(nueva_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
                return render_template('admin/form_usuario.html', accion='Editar', user=user)
            user.set_password(nueva_password)

        user.rol = nuevo_rol
        db.session.commit()
        flash(f'Usuario "{user.nombre_usuario}" actualizado.', 'success')
        return redirect(url_for('admin.usuarios', admin_id=admin_id))

    return render_template('admin/form_usuario.html', accion='Editar', user=user)

@bp.route('/usuarios/eliminar/<int:admin_id>/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(admin_id, id):
    user = Usuario.query.get_or_404(id)
    if user.id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'danger')
        return redirect(url_for('admin.usuarios', admin_id=admin_id))
    nombre = user.nombre_usuario
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario "{nombre}" eliminado.', 'info')
    return redirect(url_for('admin.usuarios', admin_id=admin_id))

@bp.route('/compras/<int:admin_id>')
@login_required
@admin_required
def compras(admin_id):
    solicitudes = Compra.query.order_by(Compra.fecha.desc()).all()
    return render_template('admin/compras.html', solicitudes=solicitudes)

@bp.route('/compras/<int:admin_id>/estado/<int:id>/<string:nuevo_estado>', methods=['POST'])
@login_required
@admin_required
def actualizar_estado_compra(admin_id, id, nuevo_estado):
    compra = Compra.query.get_or_404(id)
    
    if nuevo_estado not in ['solicitud', 'entregado', 'cancelado']:
        flash('Estado no válido.', 'danger')
        return redirect(url_for('admin.compras', admin_id=admin_id))
        
    old_estado = compra.estado
    compra.estado = nuevo_estado
    
    # Generar factura automáticamente si pasa a 'entregado'
    if nuevo_estado == 'entregado' and old_estado != 'entregado':
        # Verificar si ya tiene factura para evitar duplicados
        if not compra.factura:
            nueva_factura = Factura(
                id_cliente=compra.id_cliente,
                id_compra=compra.id_compra,
                total=compra.total,
                fecha=date.today()
            )
            db.session.add(nueva_factura)
            flash(f'Pedido #{compra.id_compra} marcado como entregado. Factura generada automáticamente.', 'success')
        else:
            flash(f'Pedido #{compra.id_compra} marcado como entregado.', 'success')
    else:
        flash(f'Estado del pedido #{compra.id_compra} actualizado a {nuevo_estado}.', 'info')
        
    db.session.commit()
    return redirect(url_for('admin.compras', admin_id=admin_id))

@bp.route('/ajustes/<int:admin_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def ajustes(admin_id):
    from app.models.config import Config
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app

    if request.method == 'POST':
        app_name = request.form.get('app_name', '').strip()
        app_logo_url = request.form.get('app_logo_url', '').strip()
        app_logo_file = request.files.get('app_logo_file')
        app_instagram = request.form.get('app_instagram', '').strip()
        app_whatsapp = request.form.get('app_whatsapp', '').strip()

        if app_name:
            Config.set_val('app_name', app_name)
        
        if app_logo_file and app_logo_file.filename:
            filename = secure_filename(f"logo_{app_logo_file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            app_logo_file.save(filepath)
            Config.set_val('app_logo', f"static/uploads/repuestos/{filename}")
        elif app_logo_url:
            Config.set_val('app_logo', app_logo_url)

        Config.set_val('app_instagram', app_instagram)
        Config.set_val('app_whatsapp', app_whatsapp)

        flash('Ajustes actualizados correctamente.', 'success')
        return redirect(url_for('admin.ajustes', admin_id=admin_id))

    return render_template('admin/ajustes.html')


@bp.route('/resenas/<int:admin_id>')
@login_required
@admin_required
def resenas(admin_id):
    from app.models.resena import Resena
    resenas_list = Resena.query.order_by(Resena.fecha.desc()).all()
    return render_template('admin/resenas.html', resenas=resenas_list)


@bp.route('/resenas/<int:admin_id>/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_resena(admin_id, id):
    from app.models.resena import Resena
    resena = Resena.query.get_or_404(id)
    db.session.delete(resena)
    db.session.commit()
    flash('Reseña eliminada correctamente.', 'success')
    return redirect(url_for('admin.resenas', admin_id=admin_id))


@bp.route('/resenas/<int:admin_id>/eliminar-todas', methods=['POST'])
@login_required
@admin_required
def eliminar_todas_resenas(admin_id):
    from app.models.resena import Resena
    Resena.query.delete()
    db.session.commit()
    flash('Todas las reseñas han sido eliminadas.', 'success')
    return redirect(url_for('admin.resenas', admin_id=admin_id))

