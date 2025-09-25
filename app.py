from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "supersecret"

# Config DB
db_url = os.getenv("DATABASE_URL", "sqlite:///local.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODELOS
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    transporte = db.Column(db.Float, nullable=False)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    baridade = db.Column(db.Float, nullable=False)

class Composicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey("mistura.id"))
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"))
    percentagem = db.Column(db.Float, nullable=False)
    mistura = db.relationship("Mistura", backref="componentes")
    material = db.relationship("Material")

class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    custo = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    custo = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False)

# Criar tabelas
with app.app_context():
    db.create_all()
    # Valores pré-preenchidos Diversos
    defaults = [
        ("Custo Central", 1500),
        ("Custo Fabrico", 11),
        ("Custo Camiao Hora", 50),
        ("Nciclos", 5),
    ]
    for nome, valor in defaults:
        if not Diverso.query.filter_by(nome=nome).first():
            db.session.add(Diverso(nome=nome, valor=valor))
    db.session.commit()

# ROTAS PRINCIPAIS
@app.route("/")
def index():
    return redirect(url_for("calculo"))

@app.route("/materiais", methods=["GET", "POST"])
def materiais():
    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        transporte = float(request.form["transporte"])
        db.session.add(Material(nome=nome, preco=preco, transporte=transporte))
        db.session.commit()
        flash("Material adicionado!", "success")
        return redirect(url_for("materiais"))
    lista = Material.query.all()
    return render_template("materiais.html", lista=lista)

@app.route("/materiais/delete/<int:id>", methods=["POST"])
def materiais_delete(id):
    it = Material.query.get_or_404(id)
    db.session.delete(it)
    db.session.commit()
    flash("Material removido", "warning")
    return redirect(url_for("materiais"))

@app.route("/equipamentos", methods=["GET", "POST"])
def equipamentos():
    if request.method == "POST":
        nome = request.form["nome"]
        custo = float(request.form["custo"])
        qtd = int(request.form["quantidade"])
        db.session.add(Equipamento(nome=nome, custo=custo, quantidade=qtd))
        db.session.commit()
        flash("Equipamento adicionado", "success")
        return redirect(url_for("equipamentos"))
    lista = Equipamento.query.all()
    return render_template("equipamentos.html", lista=lista)

@app.route("/equipamentos/delete/<int:id>", methods=["POST"])
def equipamentos_delete(id):
    it = Equipamento.query.get_or_404(id)
    db.session.delete(it)
    db.session.commit()
    return redirect(url_for("equipamentos"))

@app.route("/humanos", methods=["GET", "POST"])
def humanos():
    if request.method == "POST":
        nome = request.form["nome"]
        custo = float(request.form["custo"])
        qtd = int(request.form["quantidade"])
        db.session.add(Humano(nome=nome, custo=custo, quantidade=qtd))
        db.session.commit()
        flash("Meio humano adicionado", "success")
        return redirect(url_for("humanos"))
    lista = Humano.query.all()
    return render_template("humanos.html", lista=lista)

@app.route("/humanos/delete/<int:id>", methods=["POST"])
def humanos_delete(id):
    it = Humano.query.get_or_404(id)
    db.session.delete(it)
    db.session.commit()
    return redirect(url_for("humanos"))

@app.route("/diversos", methods=["GET", "POST"])
def diversos():
    if request.method == "POST":
        nome = request.form["nome"]
        valor = float(request.form["valor"])
        db.session.add(Diverso(nome=nome, valor=valor))
        db.session.commit()
        return redirect(url_for("diversos"))
    lista = Diverso.query.all()
    return render_template("diversos.html", lista=lista)

@app.route("/diversos/delete/<int:id>", methods=["POST"])
def diversos_delete(id):
    it = Diverso.query.get_or_404(id)
    db.session.delete(it)
    db.session.commit()
    return redirect(url_for("diversos"))

@app.route("/diversos/edit/<int:id>", methods=["GET","POST"])
def diversos_edit(id):
    item = Diverso.query.get_or_404(id)
    if request.method == "POST":
        item.valor = float(request.form["valor"])
        db.session.commit()
        return redirect(url_for("diversos"))
    return render_template("diversos_edit.html", item=item)

@app.route("/misturas", methods=["GET","POST"])
def misturas():
    if request.method == "POST":
        nome = request.form["nome"]
        baridade = float(request.form["baridade"])
        db.session.add(Mistura(nome=nome, baridade=baridade))
        db.session.commit()
        return redirect(url_for("misturas"))
    lista = Mistura.query.all()
    return render_template("misturas.html", lista=lista)

@app.route("/misturas/delete/<int:id>", methods=["POST"])
def misturas_delete(id):
    it = Mistura.query.get_or_404(id)
    db.session.delete(it)
    db.session.commit()
    return redirect(url_for("misturas"))

@app.route("/misturas/<int:mistura_id>", methods=["GET","POST"])
def misturas_composicao(mistura_id):
    mistura = Mistura.query.get_or_404(mistura_id)
    materiais = Material.query.all()
    if request.method == "POST":
        mid = int(request.form["material_id"])
        pct = float(request.form["percentagem"])
        comp = Composicao(mistura_id=mistura_id, material_id=mid, percentagem=pct)
        db.session.add(comp)
        db.session.commit()
        return redirect(url_for("misturas_composicao", mistura_id=mistura_id))
    componentes = Composicao.query.filter_by(mistura_id=mistura_id).all()
    total_pct = sum(c.percentagem for c in componentes)
    custo_mist = sum((c.material.preco + c.material.transporte) * (c.percentagem/100) for c in componentes)
    return render_template("misturas_composicao.html", mistura=mistura, materiais=materiais, componentes=componentes, total_pct=total_pct, custo_mist=custo_mist)

@app.route("/misturas/<int:mistura_id>/delete/<int:comp_id>", methods=["POST"])
def misturas_composicao_delete(mistura_id, comp_id):
    c = Composicao.query.get_or_404(comp_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("misturas_composicao", mistura_id=mistura_id))

@app.route("/calculo", methods=["GET","POST"])
def calculo():
    misturas = Mistura.query.all()
    resultado = None
    detalhe = {}
    if request.method == "POST":
        mistura_id = int(request.form["mistura_id"])
        mistura = Mistura.query.get_or_404(mistura_id)
        esp = float(request.form["espessura"])
        prod = float(request.form["producao"])
        nc = int(request.form["nc"])
        dif = float(request.form["dificuldade"])
        lucro = float(request.form["lucro"])

        soma_equip = sum(e.custo*e.quantidade*8 for e in Equipamento.query.all())
        soma_humanos = sum(h.custo*h.quantidade*8 for h in Humano.query.all())

        Cc = Diverso.query.filter_by(nome="Custo Central").first().valor
        Cf = Diverso.query.filter_by(nome="Custo Fabrico").first().valor
        Ccami = Diverso.query.filter_by(nome="Custo Camiao Hora").first().valor

        comps = Composicao.query.filter_by(mistura_id=mistura.id).all()
        custo_mistura = sum((c.material.preco+c.material.transporte)*(c.percentagem/100) for c in comps)

        fixa_por_ton = (Cc + soma_equip + soma_humanos)/prod
        variavel_por_ton = Cf + custo_mistura + (Ccami/30/nc)

        custo = (fixa_por_ton + variavel_por_ton) * mistura.baridade
        custo = custo * (1+lucro/100)
        custo = custo * esp

        resultado = round(custo,2)
        detalhe = dict(espessura=esp,producao=prod,nc=nc,lucro=lucro,
                       fixa_por_ton=round(fixa_por_ton,2),
                       variavel_por_ton=round(variavel_por_ton,2),
                       baridade=mistura.baridade,
                       soma_equip=round(soma_equip,2),
                       soma_humanos=round(soma_humanos,2),
                       custo_mistura=round(custo_mistura,2))

    return render_template("calculo.html", misturas=misturas, resultado=resultado, detalhe=detalhe)

if __name__ == "__main__":
    app.run(debug=True)
