from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.orden_servicio import OrdenServicio
from app.models.moto import Moto
from app.models.cliente import Cliente
from app.models.mecanico import Mecanico
from app.models.factura import Factura
from app.models.repuesto import Repuesto, OrdenRepuesto
from app.models.compra import Compra, CompraRepuesto
from app import db
from sqlalchemy import case
from datetime import date
from functools import wraps

bp = Blueprint('portal', __name__, url_prefix='/portal')

def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_admin():
            return redirect(url_for('cliente.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@cliente_required
def dashboard():
    return render_template('cliente_portal/dashboard.html')

@bp.route('/agendar', methods=['GET', 'POST'])
@login_required
@cliente_required
def agendar():
    mecanicos = Mecanico.query.order_by(Mecanico.nombre).all()
    repuestos = Repuesto.query.order_by(Repuesto.nombre).all()
    horas = OrdenServicio.HORAS

    if request.method == 'POST':
        nombre = current_user.nombre_usuario
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        placa = request.form['placa'].strip().upper()
        tipo_moto = request.form.get('tipo_moto', '').strip()
        modelo_moto = request.form.get('modelo_moto', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_str = request.form['fecha']
        hora = request.form.get('hora', '').strip()
        id_mecanico = request.form.get('id_mecanico') or None

        if not nombre or not placa or not fecha_str or not hora or not telefono or not direccion or not tipo_moto or not modelo_moto or not descripcion or not id_mecanico:
            flash('Todos los campos del formulario son obligatorios.', 'danger')
            return render_template('cliente_portal/agendar.html', mecanicos=mecanicos, repuestos=repuestos, horas=horas)

        # Verificar si ya está reservada esa fecha y hora
        fecha_obj = date.fromisoformat(fecha_str)
        
        # Validar que no sea domingo
        if fecha_obj.weekday() == 6: # 6 es domingo
            flash('Lo sentimos, los domingos no hay servicio. Por favor elige otro día.', 'warning')
            return render_template('cliente_portal/agendar.html', mecanicos=mecanicos, horas=horas)

        # Validar disponibilidad (que no haya otra cita a la misma fecha y hora)
        # Solo contamos citas que no estén canceladas
        cita_existente = OrdenServicio.query.filter_by(fecha=fecha_obj, hora=hora).filter(OrdenServicio.estado != 'cancelado').first()
        if cita_existente:
            flash(f'Lo sentimos, el horario de las {hora} para el día {fecha_str} ya está reservado. Por favor elige otra hora o fecha.', 'warning')
            return render_template('cliente_portal/agendar.html', mecanicos=mecanicos, horas=horas)

        # Buscar cliente asociado al usuario actual o crear uno nuevo si no existe
        cliente = Cliente.query.filter_by(nombre=current_user.nombre_usuario).first()
        if not cliente:
            cliente = Cliente(nombre=current_user.nombre_usuario)
            db.session.add(cliente)
            db.session.flush()

        # Actualizar datos del cliente
        cliente.telefono = telefono
        cliente.direccion = direccion
        
        # Buscar o crear moto
        moto = Moto.query.filter_by(placa=placa).first()
        if not moto:
            moto = Moto(
                placa=placa,
                tipo=tipo_moto,
                modelo=int(modelo_moto) if modelo_moto else None,
                id_cliente=cliente.id_cliente
            )
            db.session.add(moto)
            db.session.flush()
        
        # Crear orden de servicio (la cita)
        nueva_orden = OrdenServicio(
            id_moto=moto.id_moto,
            id_mecanico=int(id_mecanico) if id_mecanico else None,
            fecha=fecha_obj,
            hora=hora,
            estado='pendiente',
            es_cita_cliente=True,
            descripcion=descripcion or None
        )
        db.session.add(nueva_orden)
        db.session.flush()

        db.session.commit()

        flash('¡Cita agendada exitosamente! Te esperamos en el taller.', 'success')
        return redirect(url_for('portal.confirmacion', id=nueva_orden.id_servicio))

    return render_template('cliente_portal/agendar.html', mecanicos=mecanicos, horas=horas)

@bp.route('/confirmacion/<int:id>')
@login_required
@cliente_required
def confirmacion(id):
    orden = OrdenServicio.query.get_or_404(id)
    return render_template('cliente_portal/confirmacion.html', orden=orden)

@bp.route('/mis-citas')
@login_required
@cliente_required
def mis_citas():
    # Definir el orden personalizado de los estados
    orden_estados = case(
        (OrdenServicio.estado == 'completado', 1),
        (OrdenServicio.estado == 'en_proceso', 2),
        (OrdenServicio.estado == 'pendiente', 3),
        (OrdenServicio.estado == 'cancelado', 4),
        else_=5
    )
    
    # Obtener todas las citas que son del cliente y ordenarlas
    citas = OrdenServicio.query.filter_by(es_cita_cliente=True).order_by(orden_estados, OrdenServicio.fecha.desc()).all()
    
    # Filtrar solo las citas del usuario actual usando su nombre_usuario (que es igual a cliente.nombre)
    mis_citas_list = [c for c in citas if c.moto.cliente.nombre == current_user.nombre_usuario]
    
    # Limitar a las últimas 20 si es necesario (según el código original)
    return render_template('cliente_portal/mis_citas.html', citas=mis_citas_list[:20])

@bp.route('/tienda')
@login_required
@cliente_required
def tienda():
    repuestos = Repuesto.query.order_by(Repuesto.nombre).all()
    cliente = Cliente.query.filter_by(nombre=current_user.nombre_usuario).first()
    return render_template('cliente_portal/tienda.html', repuestos=repuestos, cliente=cliente)

@bp.route('/realizar-compra', methods=['POST'])
@login_required
@cliente_required
def realizar_compra():
    repuestos_db = Repuesto.query.all()
    compra_items = []
    total_compra = 0
    
    # Buscar cliente asociado al usuario actual o crear uno nuevo si no existe
    cliente = Cliente.query.filter_by(nombre=current_user.nombre_usuario).first()
    if not cliente:
        cliente = Cliente(nombre=current_user.nombre_usuario)
        db.session.add(cliente)
        db.session.flush()

    for r in repuestos_db:
        cantidad_str = request.form.get(f'repuesto_{r.id_repuesto}')
        if cantidad_str and cantidad_str.isdigit() and int(cantidad_str) > 0:
            cantidad = int(cantidad_str)
            valor_item = float(r.valor) * cantidad
            compra_items.append({
                'repuesto': r,
                'cantidad': cantidad,
                'valor': valor_item
            })
            total_compra += valor_item
            
    if not compra_items:
        flash('No has seleccionado ningún repuesto para comprar.', 'warning')
        return redirect(url_for('portal.tienda'))

    # Actualizar datos del cliente si se proporcionaron nuevos
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    if telefono: cliente.telefono = telefono
    if direccion: cliente.direccion = direccion
        
    # Crear la compra
    nueva_compra = Compra(
        id_cliente=cliente.id_cliente,
        total=total_compra,
        estado='solicitud'
    )
    db.session.add(nueva_compra)
    db.session.flush()
    
    # Agregar los items
    for item in compra_items:
        ci = CompraRepuesto(
            id_compra=nueva_compra.id_compra,
            id_repuesto=item['repuesto'].id_repuesto,
            cantidad=item['cantidad'],
            valor=item['valor']
        )
        db.session.add(ci)
        
    db.session.commit()
    flash('Tu solicitud de compra ha sido enviada exitosamente.', 'success')
    return redirect(url_for('portal.mis_compras'))

@bp.route('/mis-compras')
@login_required
@cliente_required
def mis_compras():
    cliente = Cliente.query.filter_by(nombre=current_user.nombre_usuario).first()
    if not cliente:
        return render_template('cliente_portal/mis_compras.html', compras=[])
        
    compras = Compra.query.filter_by(id_cliente=cliente.id_cliente).order_by(Compra.fecha.desc()).all()
    return render_template('cliente_portal/mis_compras.html', compras=compras)

@bp.route('/cancelar-cita/<int:id>', methods=['POST'])
@login_required
@cliente_required
def cancelar_cita(id):
    orden = OrdenServicio.query.get_or_404(id)
    # Verificar que la cita pertenezca al usuario actual
    if orden.moto.cliente.nombre != current_user.nombre_usuario:
        flash('No tienes permiso para cancelar esta cita.', 'danger')
        return redirect(url_for('portal.mis_citas'))
    
    if orden.estado not in ['pendiente', 'en_proceso']:
        flash('No se puede cancelar una cita que ya está completada o cancelada.', 'warning')
        return redirect(url_for('portal.mis_citas'))

    orden.estado = 'cancelado'
    db.session.commit()
    flash('Cita cancelada exitosamente.', 'success')
    return redirect(url_for('portal.mis_citas'))

@bp.route('/cancelar-compra/<int:id>', methods=['POST'])
@login_required
@cliente_required
def cancelar_compra(id):
    compra = Compra.query.get_or_404(id)
    # Verificar que la compra pertenezca al usuario actual
    cliente = Cliente.query.filter_by(nombre=current_user.nombre_usuario).first()
    if not cliente or compra.id_cliente != cliente.id_cliente:
        flash('No tienes permiso para cancelar este pedido.', 'danger')
        return redirect(url_for('portal.mis_compras'))
    
    if compra.estado != 'solicitud':
        flash('No se puede cancelar un pedido que ya está procesado o entregado.', 'warning')
        return redirect(url_for('portal.mis_compras'))

    compra.estado = 'cancelado'
    db.session.commit()
    flash('Pedido cancelado exitosamente.', 'success')
    return redirect(url_for('portal.mis_compras'))

@bp.route('/resenas', methods=['GET', 'POST'])
@login_required
@cliente_required
def resenas():
    from app.models.resena import Resena
    if request.method == 'POST':
        estrellas = int(request.form.get('estrellas', 5))
        comentario = request.form.get('comentario', '').strip()
        if comentario and 1 <= estrellas <= 5:
            nueva = Resena(
                id_usuario=current_user.id,
                estrellas=estrellas,
                comentario=comentario
            )
            db.session.add(nueva)
            db.session.commit()
            flash('¡Gracias por tu reseña!', 'success')
        else:
            flash('Por favor escribe un comentario y selecciona una calificación.', 'warning')
        return redirect(url_for('portal.resenas'))

    resenas_list = Resena.query.order_by(Resena.fecha.desc()).all()
    return render_template('cliente_portal/resenas.html', resenas=resenas_list)

@bp.route('/resenas/eliminar/<int:id>', methods=['POST'])
@login_required
@cliente_required
def eliminar_resena(id):
    from app.models.resena import Resena
    resena = Resena.query.get_or_404(id)
    if resena.id_usuario != current_user.id:
        flash('No puedes eliminar esta reseña.', 'danger')
    else:
        db.session.delete(resena)
        db.session.commit()
        flash('Reseña eliminada.', 'success')
    return redirect(url_for('portal.resenas'))

@bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@cliente_required
def perfil():
    from app.models.cliente import Cliente
    from werkzeug.security import generate_password_hash

    cliente = Cliente.query.filter_by(nombre=current_user.nombre_usuario).first()
    if not cliente:
        cliente = Cliente(nombre=current_user.nombre_usuario)
        db.session.add(cliente)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'datos':
            current_user.nombre_usuario = request.form.get('nombre_usuario', '').strip()
            cliente.nombre = current_user.nombre_usuario
            cliente.telefono = request.form.get('telefono', '').strip()
            cliente.direccion = request.form.get('direccion', '').strip()
            db.session.commit()
            flash('Datos actualizados correctamente.', 'success')

        elif action == 'password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_user.check_password(current_password):
                flash('La contraseña actual es incorrecta.', 'danger')
            elif new_password != confirm_password:
                flash('Las nuevas contraseñas no coinciden.', 'danger')
            elif len(new_password) < 4:
                flash('La nueva contraseña debe tener al menos 4 caracteres.', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Contraseña actualizada correctamente.', 'success')

        return redirect(url_for('portal.perfil'))

    return render_template('cliente_portal/perfil.html', cliente=cliente)

