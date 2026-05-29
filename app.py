import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Cargar variables de entorno (para desarrollo local)
load_dotenv()

# --- Configuración de Flask ---
app = Flask(__name__)

# Configuración de la DB usando la variable de entorno DATABASE_URL
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    # SQLAlchemy requiere la modificación del esquema 'postgres://' a 'postgresql://'
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-debe-estar-en-el-env')

# SSL inteligente: Solo lo exige si NO estás conectado al contenedor local 'db' de Swarm
if db_url and "@db:" not in db_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'sslmode': 'require'}
    }

db = SQLAlchemy(app)

# --- Modelos de Base de Datos ---

class Marca(db.Model):
    __tablename__ = 'marcas' 
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    motos = db.relationship('Motocicleta', backref='marca', lazy=True)

    def __repr__(self):
        return f'<Marca {self.nombre}>'

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

@app.route('/motos')
def listar_motos():
    """Muestra una lista de todas las motos en el inventario."""
    try:
        motos = Motocicleta.query.all()
    except Exception:
        # Si las tablas no existen en la primera consulta, las creamos en caliente
        with app.app_context():
            db.create_all()
        motos = Motocicleta.query.all()
    return render_template('lista_motos_cards.html', motos=motos, title="Inventario Principal")

@app.route('/motos/nueva', methods=['GET', 'POST'])
def crear_moto():
    marcas = Marca.query.order_by(Marca.nombre).all()
    
    if request.method == 'POST':
        try:
            nueva_moto = Motocicleta(
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
            
    return render_template('formulario_moto.html', accion='Crear', marcas=marcas, title="Crear Nueva Moto")

@app.route('/motos/editar/<int:id>', methods=['GET', 'POST'])
def editar_moto(id):
    moto = Motocicleta.query.get_or_404(id)
    marcas = Marca.query.order_by(Marca.nombre).all()

    if request.method == 'POST':
        try:
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

    return render_template('formulario_moto.html', accion='Editar', moto=moto, marcas=marcas, title=f"Editar {moto.modelo}")

@app.route('/motos/eliminar/<int:id>', methods=['POST'])
def eliminar_moto(id):
    moto = Motocicleta.query.get_or_404(id)
    try:
        db.session.delete(moto)
        db.session.commit()
        flash(f'Motocicleta "{moto.modelo}" eliminada exitosamente.', 'warning')
    except Exception as e:
        flash(f'Error al eliminar la moto: {e}', 'danger')

    return redirect(url_for('listar_motos'))


if __name__ == '__main__':
    # Creación automática de tablas solo en entorno local de desarrollo
    with app.app_context():
        db.create_all()
    app.run(debug=True)