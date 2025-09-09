from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuração dinâmica do banco de dados
db_url = os.getenv("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---- MODELOS ----
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    custo = db.Column(db.Float, nullable=False)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    custo = db.Column(db.Float, nullable=False)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    transporte = db.Column(db.Float, nullable=False)

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    custo = db.Column(db.Float, nullable=False)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, nullable=False)

class MisturaMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey("mistura.id"))
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"))
    percentagem = db.Column(db.Float, nullable=False)

    mistura = db.relationship("Mistura", backref="materiais")
    material = db.relationship("Material")

# ---- ROTAS ----
@app.route("/")
def index():
    return redirect(url_for("calculo"))

@app.route("/calculo", methods=["GET", "POST"])
def calculo():
    resultado = None
    if request.method == "POST":
        try:
            espessura = float(request.form["espessura"])
            producao = float(request.form["producao"])
            distancia = float(request.form["distancia"])
            dificuldade = int(request.form["dificuldade"])
            lucro = float(request.form["lucro"]) / 100
            mistura_id = int(request.form["mistura_id"])

            # Custos base
            custo_central = sum(d.custo for d in Diverso.query.all())
            custo_equip = sum(e.custo for e in Equipamento.query.all())
            custo_humano = sum(h.custo for h in Humano.query.all())

            # Mistura escolhida
            mistura = Mistura.query.get(mistura_id)
            custo_mistura = 0
            for mm in mistura.materiais:
                custo_mistura += (mm.percentagem/100) * (mm.material.preco + mm.material.transporte)

            custo_fabrico = custo_mistura * espessura

            custo_unitario = ((custo_central + custo_equip + custo_humano) / producao) + custo_fabrico
            custo_unitario *= mistura.baridade
            custo_unitario *= (1 + lucro)

            resultado = round(custo_unitario, 2)
        except Exception as e:
            resultado = f"Erro: {e}"

    misturas = Mistura.query.all()
    return render_template("calculo.html", misturas=misturas, resultado=resultado)

@app.route("/materiais")
def materiais():
    materiais = Material.query.all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/misturas")
def misturas():
    misturas = Mistura.query.all()
    return render_template("misturas.html", misturas=misturas)

@app.route("/misturas/<int:id>/composicao", methods=["GET", "POST"])
def composicao(id):
    mistura = Mistura.query.get_or_404(id)
    materiais = Material.query.all()
    if request.method == "POST":
        material_id = int(request.form["material_id"])
        percentagem = float(request.form["percentagem"])
        mm = MisturaMaterial(mistura_id=id, material_id=material_id, percentagem=percentagem)
        db.session.add(mm)
        db.session.commit()
        return redirect(url_for("composicao", id=id))
    return render_template("composicao.html", mistura=mistura, materiais=materiais)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
