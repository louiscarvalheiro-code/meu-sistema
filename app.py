from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------
# MODELOS
# -------------------------
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    custo_hora = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    custo_hora = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    transporte = db.Column(db.Float, default=0.0)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, default=1.0)

class MisturaMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey('mistura.id'))
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    percentagem = db.Column(db.Float, nullable=False)

class Diversos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custo_central = db.Column(db.Float, default=880.88)
    custo_fabrico = db.Column(db.Float, default=11.01)
    custo_camião = db.Column(db.Float, default=48.56)
    n_ciclos = db.Column(db.Integer, default=5)

# -------------------------
# ROTAS
# -------------------------
@app.route('/')
def index():
    return redirect(url_for('calculo'))

@app.route('/calculo', methods=['GET','POST'])
def calculo():
    misturas = Mistura.query.all()
    diversos = Diversos.query.first()
    resultado = None
    if request.method == 'POST':
        mistura_id = int(request.form['mistura'])
        espessura = float(request.form['espessura'])
        producao_diaria = float(request.form['producao'])
        n_ciclos = int(request.form['ciclos'])
        lucro = float(request.form['lucro'])/100

        mistura = Mistura.query.get(mistura_id)

        Ce = sum([e.custo_hora * e.quantidade for e in Equipamento.query.all()]) * 8
        Ch = sum([h.custo_hora * h.quantidade for h in Humano.query.all()]) * 8

        Cc = diversos.custo_central
        Cf = diversos.custo_fabrico
        Ct = diversos.custo_camião

        comps = MisturaMaterial.query.filter_by(mistura_id=mistura_id).all()
        Cm = 0
        for c in comps:
            mat = Material.query.get(c.material_id)
            if mat:
                Cm += (mat.preco + mat.transporte) * (c.percentagem/100)

        custo_total = ((Cc + Ce + Ch) / producao_diaria) + ((Cf + Cm + (Ct/n_ciclos)))
        custo_total = custo_total * mistura.baridade
        custo_total = custo_total * espessura
        custo_total = custo_total * (1 + lucro)

        resultado = {
            'mistura': mistura.nome,
            'espessura': espessura,
            'producao': producao_diaria,
            'ciclos': n_ciclos,
            'lucro': lucro*100,
            'valor': round(custo_total,2)
        }

    return render_template('calculo.html', misturas=misturas, diversos=diversos, resultado=resultado)

# -------------------------
# INIT DB
# -------------------------
def seed_data():
    if not Diversos.query.first():
        d = Diversos(custo_central=880.88, custo_fabrico=11.01, custo_camião=48.56, n_ciclos=5)
        db.session.add(d)
    if not Mistura.query.first():
        misturas = ['Desgaste','Binder','Macadame','Argamassa','Desgaste Subjacente']
        for m in misturas:
            db.session.add(Mistura(nome=m, baridade=1.0))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
