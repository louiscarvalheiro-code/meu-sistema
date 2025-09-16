from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'uma-chave-secreta-local')

# DATABASE: use DATABASE_URL (Postgres) in production, else use local SQLite
db_url = os.getenv('DATABASE_URL')
if db_url:
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----- MODELS -----
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False)
    custo = db.Column(db.Float, nullable=False, default=0.0)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False)
    custo = db.Column(db.Float, nullable=False, default=0.0)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    preco = db.Column(db.Float, nullable=False, default=0.0)
    transporte = db.Column(db.Float, nullable=False, default=0.0)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False)
    baridade = db.Column(db.Float, nullable=False, default=1.0)

class MisturaMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey('mistura.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    percentagem = db.Column(db.Float, nullable=False, default=0.0)
    mistura = db.relationship('Mistura', backref=db.backref('componentes', cascade='all, delete-orphan'))
    material = db.relationship('Material')

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False, unique=True)
    valor = db.Column(db.Float, nullable=False, default=0.0)

# Ensure tables exist (simple approach)
@app.before_request
def create_tables():
    db.create_all()
    # ensure default Diversos exist
    defaults = {
        'Custo Central': 1500.0,
        'Custo Fabrico': 11.0,
        'Custo Camiao Hora': 50.0,
        'Nciclos': 5.0
    }
    for name, val in defaults.items():
        if not Diverso.query.filter_by(nome=name).first():
            db.session.add(Diverso(nome=name, valor=val))
    db.session.commit()

# ----- UTILITIES -----
def total_percentagem_mistura(mistura_id):
    total = db.session.query(func.coalesce(func.sum(MisturaMaterial.percentagem), 0.0)).filter_by(mistura_id=mistura_id).scalar()
    return float(total or 0.0)

def custo_mistura_por_ton(mistura_id):
    custo = 0.0
    comps = MisturaMaterial.query.filter_by(mistura_id=mistura_id).all()
    for c in comps:
        mat = c.material
        if mat:
            custo += (c.percentagem / 100.0) * (mat.preco + mat.transporte)
    return round(custo, 6)

# ----- ROUTES: CALCULO -----
@app.route('/')
@app.route('/calculo', methods=['GET', 'POST'])
def calculo():
    misturas = Mistura.query.order_by(Mistura.nome).all()
    resultado = None
    detalhe = None
    if request.method == 'POST':
        try:
            mistura_id = int(request.form.get('mistura_id') or 0)
            espessura = float(request.form.get('espessura') or 0)
            producao = float(request.form.get('producao') or 1)
            nc = float(request.form.get('nc') or 5)
            dificuldade = int(request.form.get('dificuldade') or 1)
            lucro = float(request.form.get('lucro') or 0)

            # custos base
            cc = Diverso.query.filter_by(nome='Custo Central').first().valor
            cf = Diverso.query.filter_by(nome='Custo Fabrico').first().valor
            ct = Diverso.query.filter_by(nome='Custo Camiao Hora').first().valor

            # equipamentos e humanos multiplicados por 8
            soma_equip = (db.session.query(func.coalesce(func.sum(Equipamento.custo * Equipamento.quantidade), 0)).scalar() or 0.0) * 8
            soma_humanos = (db.session.query(func.coalesce(func.sum(Humano.custo * Humano.quantidade), 0)).scalar() or 0.0) * 8

            custo_mistura = custo_mistura_por_ton(mistura_id) if mistura_id else 0.0

            # fórmula
            fixa_por_ton = (cc + soma_equip + soma_humanos) / (producao if producao > 0 else 1)
            variavel_por_ton = cf + custo_mistura + (ct / (30.0 * (nc if nc > 0 else 5.0)))

            mistura = Mistura.query.get(mistura_id) if mistura_id else None
            bar = mistura.baridade if mistura else 1.0

            custo_unitario_por_ton = (fixa_por_ton + variavel_por_ton) * bar
            custo_unitario_final = custo_unitario_por_ton * espessura
            preco_final = custo_unitario_final * (1 + lucro / 100.0)

            resultado = round(preco_final, 4)
            detalhe = {
                'espessura': espessura,
                'producao': producao,
                'nc': nc,
                'lucro': lucro,
                'fixa_por_ton': round(fixa_por_ton, 4),
                'variavel_por_ton': round(variavel_por_ton, 4),
                'custo_mistura': round(custo_mistura, 4),
                'baridade': bar,
                'soma_equip': round(soma_equip, 4),
                'soma_humanos': round(soma_humanos, 4)
            }
        except Exception as e:
            flash(f'Erro no cálculo: {e}', 'danger')
    return render_template('calculo.html', misturas=misturas, resultado=resultado, detalhe=detalhe)

# ----- ROUTES: RELATORIO -----
@app.route('/relatorio')
def relatorio():
    equipamentos = Equipamento.query.all()
    humanos = Humano.query.all()
    materiais = Material.query.all()
    misturas = Mistura.query.all()
    diversos = Diverso.query.all()
    return render_template(
        'relatorio.html',
        equipamentos=equipamentos,
        humanos=humanos,
        materiais=materiais,
        misturas=misturas,
        diversos=diversos
    )

# ----- OUTRAS ROTAS (equipamentos, humanos, materiais, misturas, diversos) -----
# ... (igual à versão anterior, não modifiquei estas partes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)), debug=True)
