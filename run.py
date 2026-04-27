import os
from app import create_app, db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.mecanico import Mecanico
from app.models.moto import Moto
from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto, OrdenRepuesto
from app.models.factura import Factura
from app.models.compra import Compra, CompraRepuesto
from app.models.config import Config
from datetime import date, timedelta

app = create_app()

with app.app_context():
    db.create_all()

    if not Config.query.filter_by(key='app_name').first():
        db.session.add(Config(key='app_name', value='MotoTaller Pro'))
        db.session.add(Config(key='app_logo', value=None))
        db.session.add(Config(key='app_instagram', value=''))
        db.session.add(Config(key='app_whatsapp', value=''))
        db.session.commit()
        print("✅ Configuración por defecto creada")

    if not Usuario.query.filter_by(nombre_usuario='admin').first():
        admin = Usuario(nombre_usuario='admin', rol='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin creado: usuario=admin, contraseña=admin123")

    if Cliente.query.count() == 0:
        print("📦 Creando datos de prueba...")

        repuestos_data = [
            ('Filtro de aceite', 18000),
            ('Aceite motor 4T 10W40', 35000),
            ('Pastillas de freno delanteras', 45000),
            ('Pastillas de freno traseras', 38000),
            ('Bujía NGK', 12000),
            ('Cadena de transmisión', 85000),
            ('Llanta delantera 90/90-21', 120000),
            ('Llanta trasera 110/90-18', 135000),
            ('Cable de embrague', 22000),
            ('Líquido de frenos DOT4', 15000),
            ('Filtro de aire', 28000),
            ('Kit de carburación', 65000),
        ]
        repuestos = []
        for nombre, valor in repuestos_data:
            r = Repuesto(nombre=nombre, valor=valor)
            db.session.add(r)
            repuestos.append(r)
        db.session.flush()

        mecas_data = [
            ('Carlos Mendoza', '3101234567', 'Motor y transmisión'),
            ('Jorge Ríos', '3209876543', 'Sistema eléctrico'),
            ('Andrés Castillo', '3156789012', 'Frenos y suspensión'),
        ]
        mecas = []
        for nombre, tel, esp in mecas_data:
            m = Mecanico(nombre=nombre, telefono=tel, especialidad=esp)
            db.session.add(m)
            mecas.append(m)
        db.session.flush()

        clientes_data = [
            ('Santiago Gómez',   '3001112233', 'Cra 15 #45-20, Bogotá',   'BMW F800GS',   'BMW',       2019, 'BWX001'),
            ('Valentina Torres', '3112223344', 'Cl 80 #12-05, Medellín',  'Honda CB500',  'Honda',     2021, 'HCB002'),
            ('Sebastián Ruiz',   '3223334455', 'Av 68 #30-15, Bogotá',    'Yamaha MT07',  'Yamaha',    2020, 'YMT003'),
            ('Camila Vargas',    '3334445566', 'Cra 7 #100-22, Bogotá',   'Kawasaki Z400','Kawasaki', 2022, 'KZX004'),
            ('Andrés Moreno',    '3445556677', 'Cl 50 #8-30, Cali',       'Suzuki GN125', 'Suzuki',    2018, 'SGN005'),
            ('Laura Jiménez',    '3556667788', 'Av 30 #15-40, Barranquilla','Honda Wave 110','Honda',   2020, 'HWV006'),
            ('Felipe Castro',    '3667778899', 'Cra 20 #60-10, Manizales','Yamaha XTZ125','Yamaha',    2021, 'YXZ007'),
            ('Daniela Herrera',  '3778889900', 'Cl 10 #22-55, Pereira',   'AKT TT 125',  'AKT',       2019, 'AKT008'),
            ('Miguel Sánchez',   '3889990011', 'Av 1 #5-20, Cúcuta',      'Royal Enfield Meteor','Royal Enfield',2022,'REM009'),
            ('Isabella Pérez',   '3990001122', 'Cl 100 #45-30, Bogotá',   'KTM Duke 200', 'KTM',      2023, 'KTD010'),
        ]

        hoy = date.today()
        clientes = []
        for i, (nombre, tel, dir_, tipo_moto, marca, anio, placa) in enumerate(clientes_data):
            if not Usuario.query.filter_by(nombre_usuario=nombre.split()[0].lower()).first():
                u = Usuario(nombre_usuario=nombre.split()[0].lower(), rol='cliente')
                u.set_password('cliente123')
                db.session.add(u)

            c = Cliente(nombre=nombre, telefono=tel, direccion=dir_)
            db.session.add(c)
            db.session.flush()
            clientes.append(c)

            moto = Moto(placa=placa, tipo=tipo_moto, modelo=anio, id_cliente=c.id_cliente)
            db.session.add(moto)
            db.session.flush()

            fecha_orden = hoy - timedelta(days=i*5)
            meca = mecas[i % len(mecas)]
            hora = OrdenServicio.HORAS[i % len(OrdenServicio.HORAS)]
            estado = 'completado' if i < 5 else ('en_proceso' if i < 8 else 'pendiente')
            valor_base = 80000 + (i * 15000)

            orden = OrdenServicio(
                id_moto=moto.id_moto,
                id_mecanico=meca.id_mecanico,
                fecha=fecha_orden,
                hora=hora,
                estado=estado,
                valor=valor_base,
                es_cita_cliente=(i % 3 == 0),
                descripcion=f'Mantenimiento preventivo y revisión general — {tipo_moto}'
            )
            db.session.add(orden)
            db.session.flush()

            rep1 = repuestos[i % len(repuestos)]
            rep2 = repuestos[(i+1) % len(repuestos)]
            item1 = OrdenRepuesto(id_servicio=orden.id_servicio, id_repuesto=rep1.id_repuesto, cantidad=1, valor=rep1.valor)
            item2 = OrdenRepuesto(id_servicio=orden.id_servicio, id_repuesto=rep2.id_repuesto, cantidad=1, valor=rep2.valor)
            db.session.add(item1)
            db.session.add(item2)
            db.session.flush()

            total_factura = float(valor_base) + float(rep1.valor) + float(rep2.valor)

            factura = Factura(
                id_cliente=c.id_cliente,
                id_servicio=orden.id_servicio,
                fecha=fecha_orden,
                total=total_factura
            )
            db.session.add(factura)

        db.session.commit()
        print(f"✅ Datos de prueba creados: 10 clientes, motos, órdenes, repuestos y facturas")

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=81)
           
