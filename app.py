from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Base de dados
db_url = os.environ.get("DATABASE_URL", "sqlite:///data.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
db = SQLAlchemy(app)

# Modelos
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    ativo = db.Column(db.Boolean, default=True)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
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
    mistura_id = db.Column(db.Integer, db.ForeignKey("mistura.id"))
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"))
    percentual = db.Column(db.Float, nullable=False)

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)

@app.before_request
def init_db():
    db.create_all()
    if not Diverso.query.first():
        db.session.add(Diverso(nome="Custo Central", valor=880.88))
        db.session.add(Diverso(nome="Custo Fabrico", valor=11.01))
        db.session.add(Diverso(nome="Custo Camiao", valor=48.56))
        db.session.commit()

# Rotas principais
@app.route("/")
def index():
    return redirect(url_for("calculo"))

@app.route("/calculo", methods=["GET", "POST"])
def calculo():
    misturas = Mistura.query.all()
    resultado = None
    resumo = None
    if request.method == "POST":
        mistura_id = int(request.form["mistura"])
        espessura = float(request.form["espessura"])
        producao = float(request.form["producao"])
        ciclos = int(request.form["ciclos"])
        dificuldade = int(request.form["dificuldade"])
        lucro = float(request.form["lucro"]) / 100.0

        # Custos fixos
        Cc = Diverso.query.filter_by(nome="Custo Central").first().valor
        Cf = Diverso.query.filter_by(nome="Custo Fabrico").first().valor
        Ct = Diverso.query.filter_by(nome="Custo Camiao").first().valor

        Ce = sum(e.preco * e.quantidade for e in Equipamento.query.filter_by(ativo=True).all()) * 8
        Ch = sum(h.preco * h.quantidade for h in Humano.query.all()) * 8

        mistura = Mistura.query.get(mistura_id)
        Cmix = 0
        for mm in MisturaMaterial.query.filter_by(mistura_id=mistura_id).all():
            mat = Material.query.get(mm.material_id)
            Cmix += (mat.preco + mat.transporte) * (mm.percentual / 100)

        custo_base = ((Cc + Ce + Ch) / producao) + ((Cf + Cmix + (Ct / ciclos)) * mistura.baridade)
        resultado = custo_base * (1 + lucro) * espessura

        resumo = {
            "mistura": mistura.nome,
            "espessura": espessura,
            "producao": producao,
            "ciclos": ciclos,
            "lucro": lucro * 100,
            "resultado": resultado
        }
    return render_template("calculo.html", misturas=misturas, resultado=resultado, resumo=resumo)

@app.route("/equipamentos", methods=["GET", "POST"])
def equipamentos():
    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        quantidade = int(request.form.get("quantidade", 1))
        ativo = "ativo" in request.form
        eq = Equipamento(nome=nome, preco=preco, quantidade=quantidade, ativo=ativo)
        db.session.add(eq)
        db.session.commit()
    equipamentos = Equipamento.query.all()
    return render_template("equipamentos.html", equipamentos=equipamentos)

@app.route("/humanos", methods=["GET", "POST"])
def humanos():
    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        quantidade = int(request.form.get("quantidade", 1))
        h = Humano(nome=nome, preco=preco, quantidade=quantidade)
        db.session.add(h)
        db.session.commit()
    humanos = Humano.query.all()
    return render_template("humanos.html", humanos=humanos)

@app.route("/materiais", methods=["GET", "POST"])
def materiais():
    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        transporte = float(request.form.get("transporte", 0))
        m = Material(nome=nome, preco=preco, transporte=transporte)
        db.session.add(m)
        db.session.commit()
    materiais = Material.query.all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/misturas", methods=["GET", "POST"])
def misturas():
    materiais = Material.query.all()
    if request.method == "POST":
        nome = request.form["nome"]
        baridade = float(request.form["baridade"])
        mistura = Mistura(nome=nome, baridade=baridade)
        db.session.add(mistura)
        db.session.commit()
    misturas = Mistura.query.all()
    return render_template("misturas.html", misturas=misturas, materiais=materiais)

@app.route("/diversos", methods=["GET", "POST"])
def diversos():
    if request.method == "POST":
        for d in Diverso.query.all():
            valor = float(request.form.get(str(d.id), d.valor))
            d.valor = valor
        db.session.commit()
    diversos = Diverso.query.all()
    return render_template("diversos.html", diversos=diversos)

@app.route("/relatorios")
def relatorios():
    equipamentos = Equipamento.query.all()
    humanos = Humano.query.all()
    materiais = Material.query.all()
    misturas = Mistura.query.all()
    diversos = Diverso.query.all()
    return render_template("relatorios.html", equipamentos=equipamentos, humanos=humanos,
                           materiais=materiais, misturas=misturas, diversos=diversos)

if __name__ == "__main__":
    app.run(debug=True)
