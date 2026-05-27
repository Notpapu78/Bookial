from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import os

# Inicializar la aplicación
app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = 'bookial-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookial.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión'

# ============ MODELOS DE BASE DE DATOS ============
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(12), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    curso = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Libro(db.Model):
    __tablename__ = 'libros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True)
    editorial = db.Column(db.String(100))
    año = db.Column(db.Integer)
    categoria = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    portada = db.Column(db.String(200))
    disponibles = db.Column(db.Integer, default=1)
    total = db.Column(db.Integer, default=1)

class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    fecha_prestamo = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devolucion = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default='activo')
    
    usuario = db.relationship('Usuario', backref='prestamos')
    libro = db.relationship('Libro', backref='prestamos')

class ProgresoLectura(db.Model):
    __tablename__ = 'progreso_lectura'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    pagina = db.Column(db.Integer, default=0)
    ultima_lectura = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ============ RUTAS DE LA APLICACIÓN ============
@app.route('/')
def index():
    libros_destacados = Libro.query.limit(6).all()
    return render_template('index.html', libros=libros_destacados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'¡Bienvenido {user.nombre}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        rut = request.form.get('rut')
        email = request.form.get('email')
        curso = request.form.get('curso')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('register'))
        
        existing_user = Usuario.query.filter((Usuario.email == email) | (Usuario.rut == rut)).first()
        if existing_user:
            flash('El usuario ya existe', 'danger')
            return redirect(url_for('register'))
        
        new_user = Usuario(
            nombre=nombre, 
            apellido=apellido, 
            rut=rut, 
            email=email,
            curso=curso
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    prestamos_activos = Prestamo.query.filter_by(
        usuario_id=current_user.id, 
        estado='activo'
    ).all()
    
    libros_recomendados = Libro.query.limit(4).all()
    
    total_leidos = Prestamo.query.filter_by(
        usuario_id=current_user.id, 
        estado='devuelto'
    ).count()
    
    return render_template('dashboard.html', 
                         prestamos=prestamos_activos,
                         recomendados=libros_recomendados,
                         total_leidos=total_leidos,
                         now=datetime.utcnow())

@app.route('/library')
@login_required
def library():
    categoria = request.args.get('categoria', '')
    search = request.args.get('search', '')
    
    query = Libro.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    if search:
        query = query.filter(
            (Libro.titulo.contains(search)) | 
            (Libro.autor.contains(search))
        )
    
    libros = query.all()
    categorias = db.session.query(Libro.categoria).distinct().all()
    
    return render_template('library.html', libros=libros, categorias=categorias, search=search)

@app.route('/book/<int:book_id>')
@login_required
def book_detail(book_id):
    libro = Libro.query.get_or_404(book_id)
    prestado = Prestamo.query.filter_by(
        libro_id=book_id, 
        usuario_id=current_user.id,
        estado='activo'
    ).first()
    
    progreso = ProgresoLectura.query.filter_by(
        usuario_id=current_user.id,
        libro_id=book_id
    ).first()
    
    disponible = libro.disponibles > 0
    
    return render_template('book_detail.html', 
                         libro=libro, 
                         prestado=prestado,
                         disponible=disponible,
                         progreso=progreso)

@app.route('/borrow/<int:book_id>')
@login_required
def borrow_book(book_id):
    libro = Libro.query.get_or_404(book_id)
    
    if libro.disponibles <= 0:
        flash('No hay ejemplares disponibles', 'warning')
        return redirect(url_for('book_detail', book_id=book_id))
    
    prestamo_activo = Prestamo.query.filter_by(
        usuario_id=current_user.id,
        libro_id=book_id,
        estado='activo'
    ).first()
    
    if prestamo_activo:
        flash('Ya tienes este libro prestado', 'warning')
        return redirect(url_for('book_detail', book_id=book_id))
    
    prestamos_actuales = Prestamo.query.filter_by(
        usuario_id=current_user.id,
        estado='activo'
    ).count()
    
    if prestamos_actuales >= 3:
        flash('Has alcanzado el límite de 3 libros prestados', 'warning')
        return redirect(url_for('dashboard'))
    
    nuevo_prestamo = Prestamo(
        usuario_id=current_user.id,
        libro_id=book_id,
        fecha_devolucion=datetime.utcnow() + timedelta(days=14)
    )
    
    libro.disponibles -= 1
    db.session.add(nuevo_prestamo)
    db.session.commit()
    
    flash(f'Has tomado prestado "{libro.titulo}"', 'success')
    return redirect(url_for('dashboard'))

@app.route('/return/<int:prestamo_id>')
@login_required
def return_book(prestamo_id):
    prestamo = Prestamo.query.get_or_404(prestamo_id)
    
    if prestamo.usuario_id != current_user.id:
        flash('No autorizado', 'danger')
        return redirect(url_for('dashboard'))
    
    prestamo.estado = 'devuelto'
    prestamo.libro.disponibles += 1
    db.session.commit()
    
    flash('Libro devuelto exitosamente', 'success')
    return redirect(url_for('dashboard'))

@app.route('/calendar')
@login_required
def calendar_display():
    return render_template('calendar.html')

@app.route('/api/calendar')
@login_required
def api_calendar():
    prestamos = Prestamo.query.filter_by(
        usuario_id=current_user.id,
        estado='activo'
    ).all()
    
    eventos = []
    for prestamo in prestamos:
        color = '#dc3545' if prestamo.fecha_devolucion < datetime.utcnow() else '#28a745'
        eventos.append({
            'id': prestamo.id,
            'title': f'Devolver: {prestamo.libro.titulo}',
            'start': prestamo.fecha_devolucion.strftime('%Y-%m-%d'),
            'color': color,
            'textColor': 'white'
        })
    
    return jsonify(eventos)

@app.route('/read/<int:book_id>')
@login_required
def read_book(book_id):
    libro = Libro.query.get_or_404(book_id)
    prestamo = Prestamo.query.filter_by(
        libro_id=book_id,
        usuario_id=current_user.id,
        estado='activo'
    ).first()
    
    if not prestamo:
        flash('No tienes acceso a este libro', 'danger')
        return redirect(url_for('library'))
    
    progreso = ProgresoLectura.query.filter_by(
        usuario_id=current_user.id,
        libro_id=book_id
    ).first()
    
    if not progreso:
        progreso = ProgresoLectura(
            usuario_id=current_user.id,
            libro_id=book_id,
            pagina=0
        )
        db.session.add(progreso)
        db.session.commit()
    
    return render_template('reader.html', libro=libro, progreso=progreso)

@app.route('/api/save_progress/<int:book_id>', methods=['POST'])
@login_required
def save_progress(book_id):
    data = request.get_json()
    pagina = data.get('page', 0)
    
    progreso = ProgresoLectura.query.filter_by(
        usuario_id=current_user.id,
        libro_id=book_id
    ).first()
    
    if progreso:
        progreso.pagina = pagina
        progreso.ultima_lectura = datetime.utcnow()
    else:
        progreso = ProgresoLectura(
            usuario_id=current_user.id,
            libro_id=book_id,
            pagina=pagina
        )
        db.session.add(progreso)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))

# ============ DATOS DE EJEMPLO ============
def create_sample_data():
    if Libro.query.count() == 0:
        libros_muestra = [
            Libro(titulo="Cien Años de Soledad", autor="Gabriel García Márquez", categoria="Novela", descripcion="Una obra maestra de la literatura latinoamericana", disponibles=3, total=3),
            Libro(titulo="Don Quijote de la Mancha", autor="Miguel de Cervantes", categoria="Clásico", descripcion="La obra más importante de la literatura española", disponibles=2, total=2),
            Libro(titulo="El Principito", autor="Antoine de Saint-Exupéry", categoria="Infantil", descripcion="Un cuento poético y filosófico", disponibles=5, total=5),
            Libro(titulo="1984", autor="George Orwell", categoria="Ciencia Ficción", descripcion="Una distopía sobre el control social", disponibles=2, total=2),
            Libro(titulo="Orgullo y Prejuicio", autor="Jane Austen", categoria="Romance", descripcion="Un clásico del romance inglés", disponibles=3, total=3),
            Libro(titulo="Fahrenheit 451", autor="Ray Bradbury", categoria="Ciencia Ficción", descripcion="Una sociedad donde los libros están prohibidos", disponibles=2, total=2),
            Libro(titulo="El Hobbit", autor="J.R.R. Tolkien", categoria="Fantasía", descripcion="La aventura de Bilbo Bolsón", disponibles=4, total=4)
        ]
        for libro in libros_muestra:
            db.session.add(libro)
        db.session.commit()
        print("📚 Libros de ejemplo creados exitosamente")

# ============ EJECUTAR APLICACIÓN ============
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_data()
    print("\n" + "="*50)
    print("🚀 SERVIDOR INICIADO CORRECTAMENTE")
    print("📖 Bookial - Biblioteca Digital")
    print("🌐 Accede en: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
