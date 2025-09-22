from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Mistura, Material, Composicao

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configuração da base de dados (Render/PostgreSQL ou local)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:password@host:5432/database"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# 🔑 Garantir criação automática das tabelas no arranque
with app.app_context():
    db.create_all()

# ---------------- ROTAS ---------------- #

@app.route("/")
def index():
    return redirect(url_for("calculo"))

# ---------- EQUIPAMENTOS ----------
@app.route("/equipamentos")
def equipamentos():
    return render_template("equipamentos.html")

# ---------- HUMANOS ----------
@app.route("/humanos")
def humanos():
    return render_template("humanos.html")

# ---------- MATERIAIS ----------
@app.route("/materiais")
def materiais():
    materiais = Material.query.all()
    return render_template("materiais.html", materiais=materiais)

@app.route("/materiais/add", methods=["POST"])
def add_material():
    nome = request.form.get("nome")
    custo = request.form.get("custo")
    if nome and custo:
        novo = Material(nome=nome, custo=float(custo))
        db.session.add(novo)
        db.session.commit()
        flash("✅ Material adicionado com sucesso", "success")
    else:
        flash("⚠️ Preencha todos os campos", "danger")
    return redirect(url_for("materiais"))

# ---------- MISTURAS ----------
@app.route("/misturas")
def misturas():
    misturas = Mistura.query.all()
    return render_template("misturas.html", misturas=misturas)

@app.route("/misturas/<int:id>")
def ver_mistura(id):
    mistura = Mistura.query.get_or_404(id)
    return render_template("ver_mistura.html", mistura=mistura)

@app.route("/misturas/add", methods=["POST"])
def add_mistura():
    nome = request.form.get("nome")
    if nome:
        nova = Mistura(nome=nome)
        db.session.add(nova)
        db.session.commit()
        flash("✅ Mistura criada com sucesso", "success")
    else:
        flash("⚠️ Informe o nome da mistura", "danger")
    return redirect(url_for("misturas"))

@app.route("/misturas/<int:id>/add_material", methods=["POST"])
def add_material_mistura(id):
    mistura = Mistura.query.get_or_404(id)
    material_id = request.form.get("material_id")
    percentagem = request.form.get("percentagem")

    if material_id and percentagem:
        comp = Composicao(mistura_id=id, material_id=material_id, percentagem=float(percentagem))
        db.session.add(comp)
        db.session.commit()
        flash("✅ Material adicionado à mistura", "success")
    else:
        flash("⚠️ Preencha todos os campos", "danger")

    return redirect(url_for("ver_mistura", id=id))

# ---------- DIVERSOS ----------
@app.route("/diversos")
def diversos():
    return render_template("diversos.html")

# ---------- CALCULO ----------
@app.route("/calculo")
def calculo():
    misturas = Mistura.query.all()
    return render_template("calculo.html", misturas=misturas)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
