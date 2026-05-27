from app import app, db, Usuario, Libro, Prestamo, Reserva
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta

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
            flash('¡Bienvenido!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
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
        password = request.form.get('password')
        
        existing_user = Usuario.query.filter((Usuario.email == email) | (Usuario.rut == rut)).first()
        if existing_user:
            flash('El usuario ya existe', 'danger')
            return redirect(url_for('register'))
        
        new_user = Usuario(nombre=nombre, apellido=apellido, rut=rut, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro exitoso, ahora puedes iniciar sesión', 'success')
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
    
    return render_template('dashboard.html', 
                         prestamos=prestamos_activos,
                         recomendados=libros_recomendados)

@app.route('/library')
@login_required
def library():
    categoria = request.args.get('categoria', '')
    search = request.args.get('search', '')
    
    query = Libro.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    if search:
        query = query.filter(Libro.titulo.contains(search) | Libro.autor.contains(search))
    
    libros = query.all()
    categorias = db.session.query(Libro.categoria).distinct().all()
    
    return render_template('library.html', libros=libros, categorias=categorias)

@app.route('/book/<int:book_id>')
@login_required
def book_detail(book_id):
    libro = Libro.query.get_or_404(book_id)
    prestado = Prestamo.query.filter_by(
        libro_id=book_id, 
        usuario_id=current_user.id,
        estado='activo'
    ).first()
    
    disponible = libro.disponibles > 0
    
    return render_template('book_detail.html', 
                         libro=libro, 
                         prestado=prestado,
                         disponible=disponible)

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
        flash('Ya tienes prestado este libro', 'warning')
        return redirect(url_for('book_detail', book_id=book_id))
    
    nuevo_prestamo = Prestamo(
        usuario_id=current_user.id,
        libro_id=book_id,
        fecha_devolucion=datetime.utcnow() + timedelta(days=14)
    )
    
    libro.disponibles -= 1
    db.session.add(nuevo_prestamo)
    db.session.commit()
    
    flash('Libro prestado exitosamente', 'success')
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
    
    flash('Libro devuelto', 'success')
    return redirect(url_for('dashboard'))

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
    
    return render_template('reader.html', libro=libro)

@app.route('/api/calendar')
@login_required
def api_calendar():
    prestamos = Prestamo.query.filter_by(usuario_id=current_user.id).all()
    eventos = []
    
    for prestamo in prestamos:
        eventos.append({
            'title': f'Devolver: {prestamo.libro.titulo}',
            'start': prestamo.fecha_devolucion.strftime('%Y-%m-%d'),
            'color': 'red' if prestamo.fecha_devolucion < datetime.utcnow() else 'green'
        })
    
    return jsonify(eventos)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))