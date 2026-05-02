from flask import Flask, render_template, redirect, url_for, request, session
from Modelo.Dao import db, Equipo, Reserva, Usuario, Cancha, Pago, Evento, InscripcionEvento, Arbitro
from datetime import datetime, timedelta
import uuid
import os
from werkzeug.utils import secure_filename
from flask import session, redirect, url_for

app = Flask(__name__)

# config de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Pandemioyduki123@localhost/MARACANA_WEB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'claveparasesiones'  # Clave secreta para las sesiones

# carpeta donde se guardan los escudos
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'escudos')

# extensiones permitidas para escudos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    # revisa si el archivo tiene extension valida
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =================== paginas base ===================
@app.route('/')
def home():
    return redirect(url_for('menu'))  # Redirige a la página principal

@app.route('/menu')
@app.route('/index')
def menu():
    canchas = Cancha.query.all()   # leer canchas de la bd
    return render_template('index.html', canchas=canchas)


@app.route('/menuPrincipal')
def menuPrincipal():
    return redirect(url_for('menu'))

# =================== login ===================
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        
        # Buscar usuario por correo en la base de datos
        usuario = Usuario.query.filter_by(correo=correo).first()
        
        if usuario and usuario.contrasena == contraseña:  # Compara la contraseña en texto plano
            session['usuario_id'] = usuario.idUsuario  # Guardar el ID del usuario en la sesión
            session['usuario_rol'] = usuario.rol  # Guardar el rol del usuario

            if usuario.rol == 'administrador':
                return redirect(url_for('admin_dashboard'))  # Redirigir a opciones de administrador 
            else:
                return redirect(url_for('menu'))  # Redirigir al área de cliente 
        else:
            msg = 'Usuario o contraseña incorrectos'
    return render_template('login.html', msg=msg)

# =================== registro ===================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    msg = ''
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        rol = request.form['rol']  # Obtener el rol (cliente o administrador)
        
        # Verificar si el correo ya está registrado
        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        
        if usuario_existente:
            msg = 'Este correo ya está registrado. Por favor usa otro.'
        else:
            # Crear un nuevo usuario con el rol seleccionado
            nuevo_usuario = Usuario(nombre=nombre, correo=correo, contrasena=contraseña, rol=rol)
            db.session.add(nuevo_usuario)
            db.session.commit()
            return redirect(url_for('login'))  # Redirige al login después de registrar el usuario

    return render_template('registro.html', msg=msg)


# =================== cerrar sesión  ===================
@app.route('/logout')
def logout():
    session.clear()  # Limpiar la sesión
    return redirect(url_for('login'))  # Redirigir al login después de cerrar sesión

# =================== errores ===================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('505.html'), 500


# =================== torneos / equipos ===================
# equipos listado
@app.route('/db/Equipos')
@app.route('/Equipos')
def listarTorneo():
    equipos = Equipo().consultaGeneral()
    return render_template('db/Equipos.html', equipos=equipos)

@app.route('/db/registrarTorneo', methods=['GET', 'POST'])
@app.route('/registrarTorneo', methods=['GET', 'POST'])
def registrarTorneo():
    msg = ''
    if request.method == 'POST':
        # datos del formulario
        nombreEquipo = request.form['nombreEquipo']
        nombre = request.form['nombre']
        cantidadJugadores = request.form['cantidadJugadores']
        telefono = request.form['telefono']

        # archivo del escudo
        file = request.files.get('escudo')

        # validar que venga archivo
        if not file or file.filename == '':
            msg = 'el escudo del equipo es obligatorio'
            return render_template('db/registrarTorneo.html', msg=msg)

        # validar extension
        if not allowed_file(file.filename):
            msg = 'formato de imagen no valido (usa png, jpg, jpeg o gif)'
            return render_template('db/registrarTorneo.html', msg=msg)

        # guardar archivo
        filename = secure_filename(file.filename)
        carpeta = app.config['UPLOAD_FOLDER']
        os.makedirs(carpeta, exist_ok=True)
        file.save(os.path.join(carpeta, filename))

        # crear equipo y guardar nombre del archivo del escudo
        e = Equipo()
        e.nombreEquipo = nombreEquipo
        e.nombre = nombre
        e.cantidadJugadores = cantidadJugadores
        e.telefono = telefono
        e.escudo = filename
        e.status = 'Activo'
        e.agregar()

        return redirect(url_for('listarTorneo'))

    return render_template('db/registrarTorneo.html', msg=msg)



@app.route('/db/editarEquipo/<int:id>', methods=['GET', 'POST'])
@app.route('/editarEquipo/<int:id>', methods=['GET', 'POST'])
def editarEquipo(id):
    # id aqui es la pk, sqlalchemy usa la pk aunque se llame id_equipos_torneo en el modelo
    equipo = Equipo.query.get(id)
    if not equipo:
        return render_template('404.html'), 404

    msg = ''
    if request.method == 'POST':
        equipo.nombreEquipo = request.form['nombreEquipo']
        equipo.nombre = request.form['nombre']
        equipo.cantidadJugadores = request.form['cantidadJugadores']
        equipo.telefono = request.form['telefono']

        # si el usuario sube un nuevo escudo lo actualizamos
        file = request.files.get('escudo')
        if file and file.filename != '':
            if not allowed_file(file.filename):
                msg = 'formato de imagen no valido (usa png, jpg, jpeg o gif)'
                return render_template('db/editarEquipo.html', equipo=equipo, msg=msg)

            filename = secure_filename(file.filename)
            carpeta = app.config['UPLOAD_FOLDER']
            os.makedirs(carpeta, exist_ok=True)
            file.save(os.path.join(carpeta, filename))
            equipo.escudo = filename

        db.session.commit()
        return redirect(url_for('listarTorneo'))

    return render_template('db/editarEquipo.html', equipo=equipo, msg=msg)


@app.route('/db/eliminarEquipo/<int:id>', methods=['GET', 'POST'])
@app.route('/eliminarEquipo/<int:id>', methods=['GET', 'POST'])
def eliminarEquipo(id):
    equipo = Equipo.query.get(id)
    if not equipo:
        return render_template('404.html'), 404

    if request.method == 'POST':
        db.session.delete(equipo)
        db.session.commit()
        return redirect(url_for('listarTorneo'))

    return render_template('db/eliminarEquipo.html', equipo=equipo)


# =================== instalaciones ===================
@app.route('/instalaciones')
def instalaciones():
    canchas = Cancha.query.all()      # leer todas las canchas de la BD
    return render_template('instalaciones.html', canchas=canchas)

# =================== editar cancha ===================

@app.route('/canchas/<int:id>/editar', methods=['GET', 'POST'])
def editarCancha(id):
    cancha = Cancha.query.get(id)
    if not cancha:
        return render_template('404.html'), 404

    msg = ''
    if request.method == 'POST':
        try:
            nuevo_precio = request.form['precio_hora']
            cancha.precio_hora = float(nuevo_precio)
            db.session.commit()
            return redirect(url_for('instalaciones'))
        except Exception as ex:
            msg = f'Error al actualizar el precio: {ex}'

    return render_template('db/editarCanchas.html', cancha=cancha, msg=msg)



# =================== reservas ===================
@app.route('/reserva', methods=['GET', 'POST'])
def reserva():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # redirige al login si no está logueado

    # usuario logueado (lo usamos en GET y en POST)
    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        # datos del form
        id_cancha = int(request.form['id_cancha'])
        fecha_str = request.form['fecha']      # '2025-11-30'
        hora_str = request.form['hora']        # '18:00'

        nombre = request.form.get('nombre', '')
        telefono = request.form.get('telefono', '')
        duracion_horas = int(request.form.get('duracion_horas', 1))
        metodo_pago = request.form.get('metodo_pago', 'efectivo')

        id_usuario = session.get('usuario_id')

        # convertir a objetos datetime para validar empalmes
        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_dt = datetime.strptime(hora_str, '%H:%M').time()
        inicio_nuevo = datetime.combine(fecha_dt, hora_dt)
        fin_nuevo = inicio_nuevo + timedelta(hours=duracion_horas)

        # buscar reservas de esa cancha en esa fecha
        reservas_existentes = Reserva.query.filter_by(
            id_cancha=id_cancha,
            fecha=fecha_dt,
            status='Activo'
        ).all()

        # validar empalme
        for res in reservas_existentes:
            inicio_exist = datetime.combine(res.fecha, res.hora)
            fin_exist = inicio_exist + timedelta(hours=res.duracion_horas)

            # se empalman si NO se cumple (nuevo termina antes de que empiece la otra
            # o empieza después de que termina la otra)
            if not (fin_nuevo <= inicio_exist or inicio_nuevo >= fin_exist):
                # hay choque de horario
                canchas = Cancha.query.all()
                msg = 'Ya existe una reserva para esa cancha en ese horario.'
                return render_template(
                    'db/reserva.html',
                    canchas=canchas,
                    id_cancha_sel=id_cancha,
                    fecha_sel=fecha_str,
                    hora_sel=hora_str,
                    usuario=usuario,   
                    msg=msg
                )

        # al llegar aqui se verificó que no empalmen las reservas
        r = Reserva()
        r.nombre = nombre
        r.fecha = fecha_dt
        r.hora = hora_dt
        r.telefono = telefono
        r.status = 'Activo'
        r.id_cancha = id_cancha
        r.duracion_horas = duracion_horas
        r.idUsuario = id_usuario
        r.agregar()

        # obtener la cancha para saber el precio
        cancha = Cancha.query.get(id_cancha)
        total = float(cancha.precio_hora) * duracion_horas

        # crear pago asociado a la reserva
        p = Pago()
        p.id_reservas_cancha = r.id_reservas_cancha
        p.monto = total
        p.metodo_pago = metodo_pago
        p.estatus_pago = 'pendiente'
        p.referencia_segura = str(uuid.uuid4())
        p.fecha_pago = datetime.now()
        db.session.add(p)
        db.session.commit()

        # redirigir según el rol
        if 'usuario_rol' in session and session['usuario_rol'] == 'administrador':
            return redirect(url_for('listarReserva'))
        else:
            return redirect(url_for('reserva_exitosa'))

    # GET: solo mostrar formulario
    id_cancha = request.args.get('id_cancha', type=int)
    fecha = request.args.get('fecha', '')
    hora = request.args.get('hora', '')

    canchas = Cancha.query.all()

    return render_template(
        'db/reserva.html',
        canchas=canchas,
        id_cancha_sel=id_cancha,
        fecha_sel=fecha,
        hora_sel=hora,
        usuario=usuario,
        msg=None
    )


# =================== reserva exitosa (cliente)===================
@app.route('/reserva_exitosa')
def reserva_exitosa():
    return render_template('reserva_exitosa.html')


# =================== mis reservas ===================
@app.route('/mis_reservas')
def mis_reservas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    id_usuario = session['usuario_id']

    reservas = Reserva.query.filter_by(idUsuario=id_usuario).order_by(
        Reserva.fecha.desc(), Reserva.hora.desc()
    ).all()

    reservas_usuario = []
    for r in reservas:
        cancha = Cancha.query.get(r.id_cancha)
        pago = Pago.query.filter_by(id_reservas_cancha=r.id_reservas_cancha).first()
        reservas_usuario.append({
            'reserva': r,
            'cancha': cancha,
            'pago': pago
        })

    return render_template('db/mis_reservas.html', reservas_usuario=reservas_usuario)



# listado
@app.route('/db/listarReserva')
@app.route('/listarReserva')
def listarReserva():
    clientes = Reserva().consultaGeneral()
    return render_template('db/listarReserva.html', clientes=clientes)

# ====================EDITAR reserva===================
@app.route('/db/editarReserva/<int:id>', methods=['GET', 'POST'])
@app.route('/editarReserva/<int:id>', methods=['GET', 'POST'])
def editarReserva(id):
    reserva = Reserva.query.get(id)
    if not reserva:
        return render_template('404.html'), 404

    # primer pago asociado (normalmente solo hay uno)
    pago = Pago.query.filter_by(id_reservas_cancha=reserva.id_reservas_cancha).first()
    canchas = Cancha.query.all()

    if request.method == 'POST':
        reserva.nombre = request.form['nombre']
        reserva.fecha = request.form['fecha']
        reserva.hora = request.form['hora']
        reserva.telefono = request.form['telefono']
        reserva.duracion_horas = int(request.form['duracion_horas'])
        reserva.id_cancha = int(request.form['id_cancha'])

        # recalcular monto según cancha y horas
        cancha = Cancha.query.get(reserva.id_cancha)
        total = float(cancha.precio_hora) * reserva.duracion_horas

        # si no había pago (por reservas viejas), lo creamos
        if pago is None:
            pago = Pago()
            pago.id_reservas_cancha = reserva.id_reservas_cancha
            db.session.add(pago)

        pago.monto = total
        pago.metodo_pago = request.form['metodo_pago']      # 'efectivo','tarjeta','transferencia'
        pago.estatus_pago = request.form['estatus_pago']    # 'pagado','pendiente','fallido'
        # referencia_segura y fecha_pago los dejamos como están

        db.session.commit()
        return redirect(url_for('listarReserva'))

    # GET
    return render_template('db/editarReserva.html',
    reserva=reserva,
    pago=pago,
    canchas=canchas)

# =================ELIMINAR reserva=======================
@app.route('/db/eliminarReserva/<int:id>', methods=['GET', 'POST'])
@app.route('/eliminarReserva/<int:id>', methods=['GET', 'POST'])
def eliminarReserva(id):
    reserva = Reserva.query.get(id)
    if not reserva:
        return render_template('404.html'), 404

    # pagos asociados a esta reserva
    pagos = Pago.query.filter_by(id_reservas_cancha=reserva.id_reservas_cancha).all()

    if request.method == 'POST':
        # primero borramos los pagos (por la FK)
        for p in pagos:
            db.session.delete(p)

        # luego borramos la reserva
        db.session.delete(reserva)
        db.session.commit()
        return redirect(url_for('listarReserva'))

    # GET: mostrar pantalla de confirmación
    # tomamos el primer pago (si existe)
    pago = pagos[0] if pagos else None
    return render_template('db/eliminarReserva.html', reserva=reserva, pago=pago)


# =================== Crear Tablas ===================
@app.route('/creartablas')
def crear_tablas():
    db.create_all()  # Esto asegura que las tablas de la base de datos se creen si no existen
    return 'Tablas creadas correctamente'



# =================== pagos ===================
@app.route('/pagos')
def listarPagos():
    pagos = Pago.query.all()
    return render_template('db/listarPagos.html', pagos=pagos)

# =================== TORNEOS / EVENTOS ===================
@app.route('/torneos')
def listar_torneos():
    eventos = Evento.query.all()
    return render_template('db/torneos.html', eventos=eventos)


# =================== Crear torneo ==================
@app.route('/torneos/nuevo', methods=['GET', 'POST'])
def crear_torneo():
    canchas = Cancha.query.all()
    msg = ''
    if request.method == 'POST':
        try:
            nombre_evento = request.form['nombre_evento']
            descripcion = request.form['descripcion']
            fecha_inicio_str = request.form['fecha_inicio']  # formato datetime-local
            fecha_fin_str = request.form['fecha_fin']
            organizador = request.form['organizador']
            id_cancha = int(request.form['id_cancha'])

            fecha_inicio = datetime.fromisoformat(fecha_inicio_str)
            fecha_fin = datetime.fromisoformat(fecha_fin_str)

            e = Evento()
            e.nombre_evento = nombre_evento
            e.descripcion = descripcion
            e.fecha_inicio = fecha_inicio
            e.fecha_fin = fecha_fin
            e.organizador = organizador
            e.id_cancha = id_cancha
            e.agregar()

            return redirect(url_for('listar_torneos'))
        except Exception as ex:
            msg = f'Error al crear el torneo: {ex}'

    return render_template('db/torneo_form.html', canchas=canchas, msg=msg, modo='nuevo')

# =================== Editar torneo ==================
@app.route('/torneos/<int:id_evento>/editar', methods=['GET', 'POST'])
def editar_torneo(id_evento):
    evento = Evento.query.get(id_evento)
    if not evento:
        return render_template('404.html'), 404

    canchas = Cancha.query.all()
    msg = ''

    if request.method == 'POST':
        try:
            evento.nombre_evento = request.form['nombre_evento']
            evento.descripcion = request.form['descripcion']
            fecha_inicio_str = request.form['fecha_inicio']
            fecha_fin_str = request.form['fecha_fin']
            evento.organizador = request.form['organizador']
            evento.id_cancha = int(request.form['id_cancha'])

            evento.fecha_inicio = datetime.fromisoformat(fecha_inicio_str)
            evento.fecha_fin = datetime.fromisoformat(fecha_fin_str)

            evento.editar()
            return redirect(url_for('listar_torneos'))
        except Exception as ex:
            msg = f'Error al editar el torneo: {ex}'

    return render_template('db/torneo_form.html', canchas=canchas, evento=evento, msg=msg, modo='editar')

# =================== Eliminar torneo ==================
@app.route('/torneos/<int:id_evento>/eliminar', methods=['GET', 'POST'])
def eliminar_torneo(id_evento):
    evento = Evento.query.get(id_evento)
    if not evento:
        return render_template('404.html'), 404

    # inscripciones asociadas
    inscripciones = InscripcionEvento.query.filter_by(id_evento=id_evento).all()

    if request.method == 'POST':
        # primero borrar inscripciones
        for ins in inscripciones:
            db.session.delete(ins)

        # luego borrar evento
        db.session.delete(evento)
        db.session.commit()
        return redirect(url_for('listar_torneos'))

    return render_template('db/torneo_eliminar.html', evento=evento, inscripciones=inscripciones)

# =================== Inscribir equipo ===================
@app.route('/torneos/<int:id_evento>/inscribir', methods=['GET', 'POST'])
def inscribir_equipo_torneo(id_evento):
    evento = Evento.query.get(id_evento)
    if not evento:
        return render_template('404.html'), 404

    equipos = Equipo.query.all()
    msg = ''

    if request.method == 'POST':
        id_equipo = int(request.form['id_equipos_torneo'])

        # evitar inscribir dos veces el mismo equipo al mismo evento
        existe = InscripcionEvento.query.filter_by(
            id_evento=id_evento,
            id_equipos_torneo=id_equipo
        ).first()

        if existe:
            msg = 'Este equipo ya está inscrito en este torneo.'
        else:
            ins = InscripcionEvento()
            ins.id_evento = id_evento
            ins.id_equipos_torneo = id_equipo
            ins.agregar()
            return redirect(url_for('listar_torneos'))

    return render_template('db/torneo_inscribir.html', evento=evento, equipos=equipos, msg=msg)

# =================== ÁRBITROS ===================

@app.route('/arbitros')
@app.route('/db/listarArbitros')
def listarArbitros():
    # solo activos
    arbitros = Arbitro().consultaGeneral()
    return render_template('db/listarArbitros.html', arbitros=arbitros)

@app.route('/arbitros/nuevo', methods=['GET', 'POST'])
@app.route('/db/registrarArbitro', methods=['GET', 'POST'])
def registrarArbitro():
    msg = ''
    eventos = Evento.query.all()   # necesitamos los eventos para el form siempre

    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            telefono = request.form['telefono']
            correo = request.form['correo']
            categoria = request.form['categoria']
            disponibilidad = request.form['disponibilidad']

            # puede venir 0, 1 o varios eventos seleccionados
            ids_eventos = request.form.getlist('id_evento')   # <<< OJO: getlist

            # crear arbitro
            a = Arbitro()
            a.nombre = nombre
            a.apellido = apellido
            a.telefono = telefono
            a.correo = correo
            a.categoria = categoria
            a.disponibilidad = disponibilidad
            a.status = 'Activo'

            db.session.add(a)
            db.session.flush()   # genera idArbitro sin hacer commit todavía

            # vincular eventos en la tabla intermedia (arbitro.eventos es una lista)
            for id_ev in ids_eventos:
                if not id_ev:   # por si viene la opción vacía
                    continue
                ev = Evento.query.get(int(id_ev))
                if ev:
                    a.eventos.append(ev)

            db.session.commit()
            return redirect(url_for('listarArbitros'))

        except Exception as ex:
            db.session.rollback()
            msg = f'Error al registrar árbitro: {ex}'

    return render_template('db/registrarArbitro.html', msg=msg, eventos=eventos)


@app.route('/arbitros/<int:id>/editar', methods=['GET', 'POST'])
def editarArbitro(id):
    arbitro = Arbitro.query.get(id)
    if not arbitro:
        return render_template('404.html'), 404

    msg = ''
    eventos = Evento.query.all()

    if request.method == 'POST':
        try:
            arbitro.nombre = request.form['nombre']
            arbitro.apellido = request.form['apellido']
            arbitro.telefono = request.form['telefono']
            arbitro.correo = request.form['correo']
            arbitro.categoria = request.form['categoria']
            arbitro.disponibilidad = request.form['disponibilidad']
            id_evento = request.form.get('id_evento')
            arbitro.id_evento = int(id_evento) if id_evento else None

            db.session.commit()
            return redirect(url_for('listarArbitros'))
        except Exception as ex:
            msg = f'Error al editar árbitro: {ex}'

    return render_template('db/editarArbitro.html', arbitro=arbitro, eventos=eventos, msg=msg)


@app.route('/arbitros/<int:id>/eliminar', methods=['GET', 'POST'])
def eliminarArbitro(id):
    arbitro = Arbitro.query.get(id)
    if not arbitro:
        return render_template('404.html'), 404

    if request.method == 'POST':
        db.session.delete(arbitro)
        db.session.commit()
        return redirect(url_for('listarArbitros'))

    return render_template('db/eliminarArbitro.html', arbitro=arbitro)

# ver arbitro
@app.route('/arbitros/<int:id>')
def verArbitro(id):
    arbitro = Arbitro.query.get_or_404(id)
    return render_template('db/detalleArbitro.html', arbitro=arbitro)



# =================== Reglamento ===================
@app.route('/reglamento')
def reglamento():
    return render_template('reglamento.html')

# =================== Admin ===================
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'usuario_rol' not in session or session['usuario_rol'] != 'administrador':
        return redirect(url_for('login'))  # Redirigir al login si no es administrador
    return render_template('admin_dashboard.html')





# =================== main ===================

if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=True)