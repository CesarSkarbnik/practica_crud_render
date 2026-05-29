import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuración directa y limpia para Docker Swarm
db_url = os.environ.get('DATABASE_URL', 'postgresql://cesar:tu_password_seguro@db:5432/db_motos')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'una-clave-secreta-debe-estar-en-el-env'

# Quitamos cualquier configuración extra de SSL que pueda bloquear el clúster
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}

db = SQLAlchemy(app)

# --- Modelos de Base de Datos ---
class Marca(db.Model):
    __tablename__ = 'marcas' 
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    motos = db.relationship('Motocicleta', backref='marca', lazy=True)

class Motocicleta(db.Model):
    __tablename__ = 'motos' 
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(150), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    marca_id = db.Column(db.Integer, db.ForeignKey('marcas.id', ondelete='SET NULL'), nullable=True)

# --- CREACIÓN FORZADA DE TABLAS AL ARRANCAR ---
# Como no tenemos SSH, obligamos a Flask a crear todo antes de recibir peticiones
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error inicial: {e}")

# --- Rutas CRUD ---
@app.route('/')
def index():
    return redirect(url_for('listar_motos'))

@app.route('/motos')
def listar_motos():
    # CAPTURA DE ERRORES EN PANTALLA: Si falla, te dirá exactamente por qué
    try:
        motos = Motocicleta.query.all()
        return render_template('lista_motos_cards.html', motos=motos, title="Inventario Principal")
    except Exception as e:
        return f"<h1>⚠️ Error de Diagnóstico en la Base de Datos:</h1><p>{str(e)}</p><br><small>Revisa que las credenciales del compose coincidan.</small>", 500

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
        except Exception as e:
            flash(f'Error: {e}', 'danger')
            
    return render_template('formulario_moto.html', accion='Crear', marcas=marcas, title="Crear Nueva Moto")

# Mantener las rutas de editar y eliminar simples
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
            return redirect(url_for('listar_motos'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('formulario_moto.html', accion='Editar', moto=moto, marcas=marcas, title=f"Editar {moto.modelo}")

@app.route('/motos/eliminar/<int:id>', methods=['POST'])
def eliminar_moto(id):
    moto = Motocicleta.query.get_or_404(id)
    try:
        db.session.delete(moto)
        db.session.commit()
    except Exception:
        pass
    return redirect(url_for('listar_motos'))

if __name__ == '__main__':
    app.run(debug=True)