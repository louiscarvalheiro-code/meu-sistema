from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELOS ------------------
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_hora = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    ativo = db.Column(db.Boolean, default=True)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_hora = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    transporte = db.Column(db.Float, nullable=True)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, default=1.0)

class Diversos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custo_central = db.Column(db.Float, default=880.88)
    custo_fabrico = db.Column(db.Float, default=11.01)
    custo_camiao = db.Column(db.Float, default=48.56)

# ------------------ ROTAS ------------------
@app.before_request
def init_db():
    db.create_all()
    if Diversos.query.first() is None:
        d = Diversos()
        db.session.add(d)
        db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('calculo'))

@app.route('/equipamentos', methods=['GET','POST'])
def equipamentos():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        qtd = int(request.form['quantidade'])
        eq = Equipamento(nome=nome, preco_hora=preco, quantidade=qtd)
        db.session.add(eq)
        db.session.commit()
        return redirect(url_for('equipamentos'))
    lista = Equipamento.query.all()
    return render_template('equipamentos.html', lista=lista)

@app.route('/humanos', methods=['GET','POST'])
def humanos():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        qtd = int(request.form['quantidade'])
        h = Humano(nome=nome, preco_hora=preco, quantidade=qtd)
        db.session.add(h)
        db.session.commit()
        return redirect(url_for('humanos'))
    lista = Humano.query.all()
    return render_template('humanos.html', lista=lista)

@app.route('/materiais', methods=['GET','POST'])
def materiais():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        transporte = float(request.form.get('transporte',0))
        m = Material(nome=nome, preco=preco, transporte=transporte)
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('materiais'))
    lista = Material.query.all()
    return render_template('materiais.html', lista=lista)

@app.route('/misturas', methods=['GET','POST'])
def misturas():
    if request.method == 'POST':
        nome = request.form['nome']
        baridade = float(request.form.get('baridade',1))
        m = Mistura(nome=nome, baridade=baridade)
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('misturas'))
    lista = Mistura.query.all()
    return render_template('misturas.html', lista=lista)

@app.route('/diversos', methods=['GET','POST'])
def diversos():
    d = Diversos.query.first()
    if request.method == 'POST':
        d.custo_central = float(request.form['custo_central'])
        d.custo_fabrico = float(request.form['custo_fabrico'])
        d.custo_camiao = float(request.form['custo_camiao'])
        db.session.commit()
        return redirect(url_for('diversos'))
    return render_template('diversos.html', d=d)

@app.route('/calculo', methods=['GET','POST'])
def calculo():
    misturas = Mistura.query.all()
    d = Diversos.query.first()
    resultado = None
    dados = None
    if request.method == 'POST':
        mistura_id = int(request.form['mistura'])
        espessura = float(request.form['espessura'])
        producao = float(request.form['producao'])
        ciclos = float(request.form['ciclos'])
        dificuldade = int(request.form['dificuldade'])
        lucro = float(request.form['lucro'])/100

        mistura = Mistura.query.get(mistura_id)

        Ce = sum(eq.preco_hora * 8 * eq.quantidade for eq in Equipamento.query.filter_by(ativo=True).all())
        Ch = sum(h.preco_hora * 8 * h.quantidade for h in Humano.query.all())

        custo_total = ((d.custo_central + Ce + Ch) / producao) + (
            (d.custo_fabrico + 0 + (d.custo_camiao/30)/ciclos)
        )
        custo_total = custo_total * mistura.baridade
        custo_total = custo_total * (1+lucro)
        custo_total = custo_total * espessura

        resultado = round(custo_total,2)
        dados = {
            'mistura': mistura.nome,
            'espessura': espessura,
            'producao': producao,
            'ciclos': ciclos,
            'lucro': lucro*100
        }

    return render_template('calculo.html', misturas=misturas, d=d, resultado=resultado, dados=dados)

@app.route('/relatorios')
def relatorios():
    eqs = Equipamento.query.all()
    hs = Humano.query.all()
    mats = Material.query.all()
    mis = Mistura.query.all()
    d = Diversos.query.first()
    return render_template('relatorios.html', eqs=eqs, hs=hs, mats=mats, mis=mis, d=d)

if __name__ == '__main__':
    app.run(debug=True)
