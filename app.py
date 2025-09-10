from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Base de dados: PostgreSQL no Render ou SQLite local
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
db = SQLAlchemy(app)

@app.before_request
def create_tables():
    db.create_all()

# MODELOS
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    custo = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    custo = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, nullable=False)

class Diversos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custo_central = db.Column(db.Float, default=1500.0)
    custo_fabrico = db.Column(db.Float, default=11.0)
    custo_camiao = db.Column(db.Float, default=50.0)

# Rotas Diversos
@app.route('/diversos', methods=['GET', 'POST'])
def diversos():
    d = Diversos.query.first()
    if not d:
        d = Diversos()
        db.session.add(d)
        db.session.commit()
    if request.method == 'POST':
        d.custo_central = float(request.form['custo_central'])
        d.custo_fabrico = float(request.form['custo_fabrico'])
        d.custo_camiao = float(request.form['custo_camiao'])
        db.session.commit()
        return redirect(url_for('diversos'))
    return render_template('diversos.html', d=d)

# Rota Cálculo
@app.route('/calculo', methods=['GET', 'POST'])
def calculo():
    misturas = Mistura.query.all()
    d = Diversos.query.first()
    if request.method == 'POST':
        mistura_id = int(request.form['mistura'])
        mistura = Mistura.query.get(mistura_id)
        espessura = float(request.form['espessura'])
        producao = float(request.form['producao'])
        ciclos = int(request.form['ciclos'])
        lucro = float(request.form['lucro'])

        # custos equipamentos e humanos
        ce = sum(e.custo * e.quantidade for e in Equipamento.query.all())
        ch = sum(h.custo * h.quantidade for h in Humano.query.all())

        cc = d.custo_central
        cf = d.custo_fabrico
        ct = d.custo_camiao

        custo_mistura = 0.0  # placeholder até implementar composição real

        custo_final = (((cc + ce + ch) / producao) + (cf + custo_mistura + (ct / (30 * ciclos)))) * mistura.baridade * espessura
        preco_final = custo_final * (1 + lucro / 100)

        return render_template('resultado.html', resultado=preco_final,
                               espessura=espessura, producao=producao, ciclos=ciclos, lucro=lucro)
    return render_template('calculo.html', misturas=misturas)

@app.route('/')
def index():
    return redirect(url_for('calculo'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
