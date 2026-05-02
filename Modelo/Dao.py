from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date, Time, Float, ForeignKey, DateTime, Text
import datetime
from sqlalchemy.orm import relationship

# inicializar la bd
db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    idUsuario = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    correo = Column(String(100), unique=True)
    contrasena = Column(String(100))  # Contraseña en texto plano
    status = Column(String(15), default='Activo')
    rol = Column(String(20), default='cliente')
    
    # consultar un usuario
    def consultaIndividual(self, id):
        return Usuario.query.get(id)

    # consultar todos
    def consultaGeneral(self):
        return self.query.all()

    # solo activos
    def consultaActivos(self):
        return self.query.filter_by(status='Activo').all()

    # agregar
    def agregar(self):
        db.session.add(self)
        db.session.commit()

    # editar
    def editar(self):
        db.session.merge(self)
        db.session.commit()

    # baja logica
    def eliminacionLogica(self, id):
        u = self.consultaIndividual(id)
        u.status = 'Inactivo'
        u.editar()

    # borrar definitivo
    def eliminar(self, id):
        u = self.consultaIndividual(id)
        db.session.delete(u)
        db.session.commit()


class Equipo(db.Model):
    __tablename__ = 'equipos_torneo'

    id_equipos_torneo = Column(Integer, primary_key=True) 
    nombreEquipo = Column(String(100))
    nombre = Column(String(100))          # responsable
    cantidadJugadores = Column(Integer)
    telefono = Column(String(30))
    status = Column(String(15), default='Activo')
    escudo = Column(String(255), nullable=False)

    def consultaIndividual(self, id):
        return Equipo.query.get(id)

    def consultaGeneral(self):
        return self.query.all()

    def consultaActivos(self):
        return self.query.filter_by(status='Activo').all()

    def agregar(self):
        db.session.add(self)
        db.session.commit()

    def editar(self):
        db.session.merge(self)
        db.session.commit()

    def eliminacionLogica(self, id):
        e = self.consultaIndividual(id)
        e.status = 'Inactivo'
        e.editar()

    def eliminar(self, id):
        e = self.consultaIndividual(id)
        db.session.delete(e)
        db.session.commit()



class Reserva(db.Model):
    __tablename__ = 'reservas_cancha'

    id_reservas_cancha = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    fecha = Column(Date)                    # tipo DATE
    hora = Column(Time)                     # tipo TIME
    duracion_horas = Column(Integer)      # duracion en horas
    telefono = Column(String(30))
    status = Column(String(15), default='Activo')

    # relaciones (FK)
    idUsuario = Column(Integer, db.ForeignKey('usuarios.idUsuario'))
    id_cancha = Column(Integer, db.ForeignKey('canchas.id_cancha'))

    # opcional: relaciones ORM (para acceder al usuario o cancha directamente)
    usuario = db.relationship('Usuario', backref='reservas')
    cancha = db.relationship('Cancha', backref='reservas')


    # obtener una reserva
    def consultaIndividual(self, id):
        return Reserva.query.get(id)

    # obtener todas
    def consultaGeneral(self):
        return self.query.all()

    # obtener solo activas
    def consultaActivos(self):
        return self.query.filter_by(status='Activo').all()

    # agregar reserva
    def agregar(self):
        db.session.add(self)
        db.session.commit()

    # editar reserva
    def editar(self):
        db.session.merge(self)
        db.session.commit()

    # baja logica
    def eliminacionLogica(self, id):
        r = self.consultaIndividual(id)
        r.status = 'Inactivo'
        r.editar()

    # eliminar definitiva
    def eliminar(self, id):
        r = self.consultaIndividual(id)
        db.session.delete(r)
        db.session.commit()


#  cancha
class Cancha(db.Model):
    __tablename__ = 'canchas'
    id_cancha = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    precio_hora = Column(Float, nullable=False)


#  pagos
class Pago(db.Model):
    __tablename__ = 'pagos'

    id_pago = Column(Integer, primary_key=True)
    id_reservas_cancha = Column(Integer, ForeignKey('reservas_cancha.id_reservas_cancha'), nullable=False)
    monto = Column(Float, nullable=False)
    metodo_pago = Column(String(20), nullable=False)      # 'efectivo','tarjeta','transferencia'
    estatus_pago = Column(String(20), nullable=False)     # 'pagado','pendiente','fallido'
    referencia_segura = Column(String(100))
    fecha_pago = Column(DateTime, default=datetime.datetime.now)

    reserva = db.relationship('Reserva', backref='pagos')

    # helpers opcionales
    def agregar(self):
        db.session.add(self)
        db.session.commit()



# ============Torneos=================

# listar torneos disponibles
class Evento(db.Model):
    __tablename__ = 'eventos'

    id_evento = Column(Integer, primary_key=True)
    nombre_evento = Column(String(100), nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    organizador = Column(String(100))
    id_cancha = Column(Integer, ForeignKey('canchas.id_cancha'))

    cancha = db.relationship('Cancha', backref='eventos')

    # helpers
    def agregar(self):
        db.session.add(self)
        db.session.commit()

    def editar(self):
        db.session.merge(self)
        db.session.commit()

    def eliminar(self):
        db.session.delete(self)
        db.session.commit()


# inscripcion de equipos a torneos
class InscripcionEvento(db.Model):
    __tablename__ = 'inscripciones_eventos'

    id_inscripcion = Column(Integer, primary_key=True)
    id_evento = Column(Integer, ForeignKey('eventos.id_evento'), nullable=False)
    id_equipos_torneo = Column(Integer, ForeignKey('equipos_torneo.id_equipos_torneo'), nullable=False)
    fecha_inscripcion = Column(DateTime, default=datetime.datetime.now)

    evento = db.relationship('Evento', backref='inscripciones')
    equipo = db.relationship('Equipo', backref='inscripciones_evento')

    def agregar(self):
        db.session.add(self)
        db.session.commit()
        
class Arbitro(db.Model):
    __tablename__ = 'arbitros'  

    idArbitro = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(30))
    correo = Column(String(100))
    categoria = Column(String(50), nullable=False)        # 'Local','Regional','Nacional','Internacional'
    disponibilidad = Column(String(20), default='Disponible')  # 'Disponible','Ocupado'
    status = Column(String(15), default='Activo')

    #  relación muchos-a-muchos con eventos
    eventos = db.relationship(
        'Evento',
        secondary='arbitros_eventos',   # nombre de la tabla intermedia
        backref='arbitros'
    )

    # ====== MÉTODOS TIPO DAO ======

    def consultaIndividual(self, id):
        return Arbitro.query.get(id)

    def consultaGeneral(self):
        return self.query.all()

    def consultaActivos(self):
        return self.query.filter_by(status='Activo').all()

    def agregar(self):
        db.session.add(self)
        db.session.commit()

    def editar(self):
        db.session.merge(self)
        db.session.commit()

    def eliminacionLogica(self, id):
        a = self.consultaIndividual(id)
        a.status = 'Inactivo'
        a.editar()

    def eliminar(self, id):
        a = self.consultaIndividual(id)
        db.session.delete(a)
        db.session.commit()


class ArbitroEvento(db.Model):
    __tablename__ = 'arbitros_eventos'

    id = db.Column(db.Integer, primary_key=True)
    id_arbitro = db.Column(db.Integer, db.ForeignKey('arbitros.idArbitro'), nullable=False)
    id_evento = db.Column(db.Integer, db.ForeignKey('eventos.id_evento'), nullable=False)
