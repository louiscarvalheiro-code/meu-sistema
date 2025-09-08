from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    custo = db.Column(db.Float)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    custo = db.Column(db.Float)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    preco = db.Column(db.Float)
    transporte = db.Column(db.Float)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    baridade = db.Column(db.Float)

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    valor = db.Column(db.Float)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    misturas = Mistura.query.all()
    return render_template("index.html", misturas=misturas)

@app.route("/calcular", methods=["POST"])
def calcular():
    mistura_id = int(request.form["mistura"])
    espessura = float(request.form["espessura"])
    producao = float(request.form["producao"])
    distancia = float(request.form["distancia"])
    dificuldade = int(request.form["dificuldade"])
    lucro = float(request.form["lucro"])

    custo_central = sum([d.valor for d in Diverso.query.filter(Diverso.nome=="Central").all()])
    custo_fabrico = sum([d.valor for d in Diverso.query.filter(Diverso.nome=="Fabrico").all()])
    custo_equip = sum([e.custo for e in Equipamento.query.all()])
    custo_humanos = sum([h.custo for h in Humano.query.all()])
    custo_materiais = sum([m.preco for m in Material.query.all()])
    custo_transporte = sum([m.transporte for m in Material.query.all()])

    mistura = Mistura.query.get(mistura_id)
    baridade = mistura.baridade if mistura else 1.0

    Nciclos = 5
    custo = (((custo_central + custo_equip + custo_humanos) / producao) +
             (custo_fabrico + custo_materiais + (custo_transporte / (30 * Nciclos))))
    custo_final = custo * baridade * (1 + lucro/100)

    return render_template("index.html", misturas=Mistura.query.all(),
                           resultado=round(custo_final,2))

@app.route("/equipamentos", methods=["GET","POST"])
def equipamentos():
    if request.method == "POST":
        nome = request.form["nome"]
        custo = float(request.form["custo"])
        db.session.add(Equipamento(nome=nome, custo=custo))
        db.session.commit()
        return redirect(url_for("equipamentos"))
    return render_template("equipamentos.html", equipamentos=Equipamento.query.all())

@app.route("/equipamentos/delete/<int:id>")
def delete_equip(id):
    e = Equipamento.query.get(id)
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for("equipamentos"))

@app.route("/humanos", methods=["GET","POST"])
def humanos():
    if request.method == "POST":
        nome = request.form["nome"]
        custo = float(request.form["custo"])
        db.session.add(Humano(nome=nome, custo=custo))
        db.session.commit()
        return redirect(url_for("humanos"))
    return render_template("humanos.html", humanos=Humano.query.all())

@app.route("/humanos/delete/<int:id>")
def delete_humano(id):
    h = Humano.query.get(id)
    db.session.delete(h)
    db.session.commit()
    return redirect(url_for("humanos"))

@app.route("/materiais", methods=["GET","POST"])
def materiais():
    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        transporte = float(request.form["transporte"])
        db.session.add(Material(nome=nome, preco=preco, transporte=transporte))
        db.session.commit()
        return redirect(url_for("materiais"))
    return render_template("materiais.html", materiais=Material.query.all())

@app.route("/materiais/delete/<int:id>")
def delete_material(id):
    m = Material.query.get(id)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("materiais"))

@app.route("/misturas", methods=["GET","POST"])
def misturas():
    if request.method == "POST":
        nome = request.form["nome"]
        baridade = float(request.form["baridade"])
        db.session.add(Mistura(nome=nome, baridade=baridade))
        db.session.commit()
        return redirect(url_for("misturas"))
    return render_template("misturas.html", misturas=Mistura.query.all())

@app.route("/misturas/delete/<int:id>")
def delete_mistura(id):
    m = Mistura.query.get(id)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("misturas"))

@app.route("/diversos", methods=["GET","POST"])
def diversos():
    if request.method == "POST":
        nome = request.form["nome"]
        valor = float(request.form["valor"])
        db.session.add(Diverso(nome=nome, valor=valor))
        db.session.commit()
        return redirect(url_for("diversos"))
    return render_template("diversos.html", diversos=Diverso.query.all())

@app.route("/diversos/delete/<int:id>")
def delete_diverso(id):
    d = Diverso.query.get(id)
    db.session.delete(d)
    db.session.commit()
    return redirect(url_for("diversos"))

if __name__ == "__main__":
    app.run(debug=True, port=10000)
