import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Cargar variables de entorno (para desarrollo local)
load_dotenv()

# --- Configuración de Flask ---
app = Flask(__name__)

# Configuración de la DB usando la variable de entorno DATABASE_URL (Render/Local)
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    # SQLAlchemy requiere la modificación del esquema 'postgres://' a 'postgresql://'
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-debe-estar-en-el-env')

# Configuración para forzar SSL: Esta es la corrección clave para evitar el OperationalError
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'sslmode': 'require'}
}

db = SQLAlchemy(app)

# --- Modelos de Base de Datos ---

# Modelo para la tabla 'marcas'
class Marca(db.Model):
    __tablename__ = 'marcas' 
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    motos = db.relationship('Motocicleta', backref='marca', lazy=True)

    def __repr__(self):
        return f'<Marca {self.nombre}>'

# Modelo para la tabla 'motos'
class Motocicleta(db.Model):
    __tablename__ = 'motos' 
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(150), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    marca_id = db.Column(db.Integer, db.ForeignKey('marcas.id', ondelete='SET NULL'), nullable=True)

    def __repr__(self):
        return f'<Motocicleta {self.modelo} ({self.anio})>'


# --- Rutas CRUD ---

@app.route('/')
def index():
    """Ruta de inicio que redirige a la lista de motocicletas."""
    return redirect(url_for('listar_motos'))

# [R] READ: Listar todas las motocicletas
@app.route('/motos')
def listar_motos():
    """Muestra una lista de todas las motos en el inventario, usando la vista de tarjetas."""
    motos = Motocicleta.query.all()
    # Renderiza la plantilla de tarjetas (lista_motos_cards.html)
    return render_template('lista_motos_cards.html', motos=motos, title="Inventario Principal")

# [C] CREATE: Agregar una nueva motocicleta
@app.route('/motos/nueva', methods=['GET', 'POST'])
def crear_moto():
    """Maneja la creación de una nueva moto."""
    marcas = Marca.query.order_by(Marca.nombre).all()
    
    if request.method == 'POST':
        try:
            # Aquí asumimos que los datos del formulario son correctos (Marca, Modelo, Año, Precio)
            nueva_moto = Motocicleta(
                # Manejamos el caso de que marca_id sea None/vacío
                marca_id=request.form.get('marca_id') if request.form.get('marca_id') else None,
                modelo=request.form['modelo'],
                anio=int(request.form['anio']),
                precio=float(request.form['precio'])
            )
            db.session.add(nueva_moto)
            db.session.commit()
            flash('Motocicleta creada exitosamente.', 'success')
            return redirect(url_for('listar_motos'))
        except ValueError:
            flash('Error en el formato de Año o Precio. Asegúrate de usar números válidos.', 'danger')
        except Exception as e:
            flash(f'Error al guardar la moto: {e}', 'danger')
            
    # CORRECCIÓN CLAVE: Llama al archivo renombrado 'formulario_moto.html'
    return render_template('formulario_moto.html', 
                           accion='Crear', 
                           marcas=marcas,
                           title="Crear Nueva Moto")

# [U] UPDATE: Editar una motocicleta existente
@app.route('/motos/editar/<int:id>', methods=['GET', 'POST'])
def editar_moto(id):
    """Maneja la edición de una moto existente por ID."""
    moto = Motocicleta.query.get_or_404(id)
    marcas = Marca.query.order_by(Marca.nombre).all()

    if request.method == 'POST':
        try:
            # Aquí asumimos que los datos del formulario son correctos
            # Manejamos el caso de que marca_id sea None/vacío
            moto.marca_id = request.form.get('marca_id') if request.form.get('marca_id') else None
            moto.modelo = request.form['modelo']
            moto.anio = int(request.form['anio'])
            moto.precio = float(request.form['precio'])
            
            db.session.commit()
            flash('Motocicleta actualizada exitosamente.', 'success')
            return redirect(url_for('listar_motos'))
        except ValueError:
            flash('Error en el formato de Año o Precio. Asegúrate de usar números válidos.', 'danger')
        except Exception as e:
            flash(f'Error al actualizar la moto: {e}', 'danger')

    # CORRECCIÓN CLAVE: Llama al archivo renombrado 'formulario_moto.html'
    return render_template('formulario_moto.html', 
                           accion='Editar', 
                           moto=moto, 
                           marcas=marcas,
                           title=f"Editar {moto.modelo}")

# [D] DELETE: Eliminar una motocicleta
@app.route('/motos/eliminar/<int:id>', methods=['POST'])
def eliminar_moto(id):
    """Maneja la eliminación de una moto por ID."""
    moto = Motocicleta.query.get_or_404(id)
    
    try:
        db.session.delete(moto)
        db.session.commit()
        flash(f'Motocicleta "{moto.modelo}" eliminada exitosamente.', 'warning')
    except Exception as e:
        flash(f'Error al eliminar la moto: {e}', 'danger')

    return redirect(url_for('listar_motos'))


if __name__ == '__main__':
    with app.app_context():
        # Crea las tablas si no existen.
        db.create_all() 
    
    app.run(debug=True)