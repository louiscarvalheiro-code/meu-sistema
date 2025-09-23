from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "secret-key"

# Configuração da base de dados para Render (PostgreSQL) ou SQLite local
db_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODELOS
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    transporte = db.Column(db.Float, nullable=True, default=0.0)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, nullable=False)

class Composicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey("mistura.id"))
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"))
    percentagem = db.Column(db.Float, nullable=False)
    mistura = db.relationship("Mistura", backref=db.backref("composicoes", lazy=True))
    material = db.relationship("Material")

class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_hora = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_hora = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=1)

class Diversos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custo_central = db.Column(db.Float, default=880.88)
    custo_fabrico = db.Column(db.Float, default=11.0)
    camiao_hora = db.Column(db.Float, default=48.56)
    nciclos = db.Column(db.Integer, default=5)

# Criar tabelas automaticamente
with app.app_context():
    db.create_all()
    if Diversos.query.first() is None:
        db.session.add(Diversos())
        db.session.commit()

# ROTAS
@app.route("/")
def index():
    return redirect(url_for("calculo"))

@app.route("/materiais")
def materiais():
    materiais = Material.query.all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/misturas")
def misturas():
    misturas = Mistura.query.all()
    return render_template("misturas.html", misturas=misturas)

@app.route("/equipamentos")
def equipamentos():
    equipamentos = Equipamento.query.all()
    return render_template("equipamentos.html", equipamentos=equipamentos)

@app.route("/humanos")
def humanos():
    humanos = Humano.query.all()
    return render_template("humanos.html", humanos=humanos)

@app.route("/diversos")
def diversos():
    diversos = Diversos.query.first()
    return render_template("diversos.html", diversos=diversos)

@app.route("/calculo")
def calculo():
    misturas = Mistura.query.all()
    return render_template("calculo.html", misturas=misturas)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
