import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuración de la URL de la base de datos para Kubernetes
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:admin1234@dbpostgres:5432/motos')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave-secreta-para-sesiones-de-motos'

db = SQLAlchemy(app)

# --- Modelos del Inventario de Motos ---

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


# --- 🛠️ RUTA DE EMERGENCIA PARA CREAR TABLAS EN KUBERNETES ---
@app.route('/init-db')
def inicializar_base_datos():
    try:
        db.create_all()
        return "<h1>✅ ¡Tablas 'motos' y 'marcas' creadas exitosamente en Postgres!</h1><br><a href='/motos'>👉 Ir al Inventario de Motos</a>"
    except Exception as e:
        return f"<h1>❌ Error al intentar crear las tablas:</h1><p>{str(e)}</p>"


# --- Rutas del Controlador CRUD ---

@app.route('/')
def index():
    return redirect(url_for('listar_motos'))

@app.route('/motos')
def listar_motos():
    try:
        motos = Motocicleta.query.all()
        return render_template('lista_motos_cards.html', motos=motos, title="Inventario de Motocicletas")
    except Exception as error_ejecucion:
        # Si la tabla no existe o falla, muestra el botón de diagnóstico en pantalla
        return f"""
        <h2>⚠️ Error de Comunicación con Postgres (La tabla podría no existir):</h2>
        <p>{str(error_ejecucion)}</p>
        <br>
        <a href='/init-db' style='padding:10px 20px; background-color:#28a745; color:white; text-decoration:none; border-radius:5px;'>
            Presiona aquí para intentar Inicializar la Base de Datos (/init-db)
        </a>
        """, 500

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
            flash('Motocicleta agregada con éxito.', 'success')
            return redirect(url_for('listar_motos'))
        except Exception as e:
            flash(f'Error al procesar el formulario: {e}', 'danger')
            
    return render_template('formulario_moto.html', accion='Crear', marcas=marcas, title="Agregar Moto")

@app.route('/motos/editar/<int:id>', methods=['GET', 'POST'])
def edit_moto(id):
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
def delete_moto(id):
    moto = Motocicleta.query.get_or_404(id)
    try:
        db.session.delete(moto)
        db.session.commit()
    except Exception:
        pass
    return redirect(url_for('listar_motos'))

if __name__ == '__main__':
    app.run(debug=True)