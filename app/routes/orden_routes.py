from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.orden_servicio import OrdenServicio
from app.models.moto import Moto
from app.models.cliente import Cliente
from app.models.mecanico import Mecanico
from app.models.repuesto import Repuesto, OrdenRepuesto
from app.models.factura import Factura
from app import db
from sqlalchemy import case
from datetime import date, timedelta
from functools import wraps

bp = Blueprint('orden', __name__, url_prefix='/ordenes')

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
    # Limpieza automática de órdenes completadas o entregadas con más de 15 días
    fecha_limite = date.today() - timedelta(days=15)
    ordenes_antiguas = OrdenServicio.query.filter(
        OrdenServicio.estado == 'completado',
        OrdenServicio.fecha <= fecha_limite
    ).all()
    
    if ordenes_antiguas:
        for antigua in ordenes_antiguas:
            db.session.delete(antigua)
        db.session.commit()

    search_query = request.args.get('q', '').strip()
    
    # Query base uniendo con Moto y Cliente para permitir búsqueda por nombre
    query = OrdenServicio.query.join(Moto).join(Cliente)
    
    if search_query:
        query = query.filter(Cliente.nombre.ilike(f'%{search_query}%'))
    
    # Ordenar por fecha y hora ascendente (la más cercana arriba)
    ordenes = query.order_by(OrdenServicio.fecha.asc(), OrdenServicio.hora.asc()).all()
    nombres_clientes = [c.nombre for c in Cliente.query.order_by(Cliente.nombre).all()]
    return render_template('ordenes/index.html', 
                         ordenes=ordenes, 
                         search_query=search_query, 
                         nombres_clientes=nombres_clientes)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    motos = Moto.query.order_by(Moto.placa).all()
    mecanicos = Mecanico.query.order_by(Mecanico.nombre).all()
    if request.method == 'POST':
        id_moto = request.form['id_moto']
        id_mecanico = request.form.get('id_mecanico') or None
        fecha_str = request.form['fecha']
        hora = request.form.get('hora', '').strip() or None
        estado = request.form['estado']
        valor = request.form.get('valor', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        nueva = OrdenServicio(
            id_moto=int(id_moto),
            id_mecanico=int(id_mecanico) if id_mecanico else None,
            fecha=date.fromisoformat(fecha_str),
            hora=hora,
            estado=estado,
            valor=float(valor) if valor else None,
            descripcion=descripcion or None
        )
        db.session.add(nueva)
        db.session.flush()

        # Procesar productos del catálogo seleccionados
        for rep in Repuesto.query.all():
            cant = request.form.get(f'repuesto_{rep.id_repuesto}', '0')
            if cant and cant.isdigit() and int(cant) > 0:
                cantidad = int(cant)
                item = OrdenRepuesto(
                    id_servicio=nueva.id_servicio,
                    id_repuesto=rep.id_repuesto,
                    cantidad=cantidad,
                    valor=float(rep.valor) * cantidad
                )
                db.session.add(item)
        
        db.session.flush()

        # Crear factura si el estado es completado
        if estado == 'completado':
            moto = Moto.query.get(int(id_moto))
            total_productos = sum(float(r.valor or 0) for r in nueva.repuestos)
            total_factura = total_productos + (float(valor) if valor else 0)
            
            factura = Factura(
                id_cliente=moto.id_cliente,
                id_servicio=nueva.id_servicio,
                fecha=date.today(),
                total=total_factura
            )
            db.session.add(factura)
            flash('Registro en Agenda creado y factura generada.', 'success')
        else:
            flash('Registro en Agenda creado exitosamente.', 'success')
            
        db.session.commit()
        return redirect(url_for('orden.index'))
    repuestos = Repuesto.query.order_by(Repuesto.nombre).all()
    return render_template('ordenes/form.html', accion='Agregar', orden=None, motos=motos, mecanicos=mecanicos, estados=OrdenServicio.ESTADOS, horas=OrdenServicio.HORAS, repuestos_disponibles=repuestos)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    orden = OrdenServicio.query.get_or_404(id)
    motos = Moto.query.order_by(Moto.placa).all()
    mecanicos = Mecanico.query.order_by(Mecanico.nombre).all()
    if request.method == 'POST':
        orden.id_moto = int(request.form['id_moto'])
        id_mec = request.form.get('id_mecanico') or None
        orden.id_mecanico = int(id_mec) if id_mec else None
        orden.fecha = date.fromisoformat(request.form['fecha'])
        orden.hora = request.form.get('hora', '').strip() or None
        orden.estado = request.form['estado']
        valor = request.form.get('valor', '').strip()
        orden.valor = float(valor) if valor else None
        orden.descripcion = request.form.get('descripcion', '').strip() or None
        
        # Manejar factura si está completado
        factura = Factura.query.filter_by(id_servicio=orden.id_servicio).first()
        
        if orden.estado == 'completado' and not factura:
            # Generar factura nueva
            factura = Factura(
                id_cliente=orden.moto.id_cliente,
                id_servicio=orden.id_servicio,
                fecha=date.today(),
                total=0
            )
            db.session.add(factura)
            db.session.flush()
            flash('Orden completada y factura generada.', 'success')
            
        # Manejar repuestos desde el formulario
        # Limpiar repuestos actuales y re-agregarlos (simplificado para el form)
        for r_old in list(orden.repuestos):
            db.session.delete(r_old)
        db.session.flush()

        for rep in Repuesto.query.all():
            cant = request.form.get(f'repuesto_{rep.id_repuesto}', '0')
            if cant and cant.isdigit() and int(cant) > 0:
                cantidad = int(cant)
                item = OrdenRepuesto(
                    id_servicio=orden.id_servicio,
                    id_repuesto=rep.id_repuesto,
                    cantidad=cantidad,
                    valor=float(rep.valor) * cantidad
                )
                db.session.add(item)
        
        db.session.flush() # Para que orden.repuestos se actualice
        
        if factura:
            total_repuestos = sum(float(r.valor or 0) for r in orden.repuestos)
            if orden.valor:
                total_repuestos += float(orden.valor)
            factura.total = total_repuestos
            
        db.session.commit()
        flash('Orden y lista de productos actualizados.', 'success')
        return redirect(url_for('orden.index'))
    repuestos = Repuesto.query.order_by(Repuesto.nombre).all()
    # Mapear cantidades actuales para el form
    cantidades_actuales = {r.id_repuesto: r.cantidad for r in orden.repuestos}
    return render_template('ordenes/form.html', accion='Editar', orden=orden, motos=motos, mecanicos=mecanicos, estados=OrdenServicio.ESTADOS, horas=OrdenServicio.HORAS, repuestos_disponibles=repuestos, cantidades=cantidades_actuales)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    orden = OrdenServicio.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    flash('Orden eliminada.', 'info')
    return redirect(url_for('orden.index'))

@bp.route('/detalle/<int:id>')
@login_required
@admin_required
def detalle(id):
    orden = OrdenServicio.query.get_or_404(id)
    repuestos_disponibles = Repuesto.query.order_by(Repuesto.nombre).all()
    return render_template('ordenes/detalle.html', orden=orden, repuestos_disponibles=repuestos_disponibles)

@bp.route('/detalle/<int:id>/agregar_repuesto', methods=['POST'])
@login_required
@admin_required
def agregar_repuesto(id):
    orden = OrdenServicio.query.get_or_404(id)
    id_repuesto = int(request.form['id_repuesto'])
    cantidad = int(request.form['cantidad'])
    repuesto = Repuesto.query.get_or_404(id_repuesto)
    valor_total = repuesto.valor * cantidad
    item = OrdenRepuesto(id_servicio=orden.id_servicio, id_repuesto=id_repuesto, cantidad=cantidad, valor=valor_total)
    db.session.add(item)
    db.session.flush() # Guardar temporalmente para que aparezca en orden.repuestos
    
    # Actualizar total de factura si existe
    factura = Factura.query.filter_by(id_servicio=orden.id_servicio).first()
    if factura:
        total = sum(float(r.valor or 0) for r in orden.repuestos)
        if orden.valor:
            total += float(orden.valor)
        factura.total = total
        
    db.session.commit()
    flash('Repuesto agregado a la orden.', 'success')
    return redirect(url_for('orden.detalle', id=id))

@bp.route('/detalle/<int:id>/quitar_repuesto/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def quitar_repuesto(id, item_id):
    item = OrdenRepuesto.query.get_or_404(item_id)
    orden_id = item.id_servicio
    db.session.delete(item)
    db.session.flush() # Aplicar borrado para que no aparezca en orden.repuestos
    
    # Actualizar total de factura si existe
    orden = OrdenServicio.query.get(orden_id)
    factura = Factura.query.filter_by(id_servicio=orden_id).first()
    if factura:
        total = sum(float(r.valor or 0) for r in orden.repuestos)
        if orden.valor:
            total += float(orden.valor)
        factura.total = total
        
    db.session.commit()
    flash('Repuesto quitado.', 'info')
    return redirect(url_for('orden.detalle', id=id))
