from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Mistura, Material, Composicao

# -------------------------------------------------
# 🔧 Configuração da App Flask
# -------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"  # ⚠️ se no Render usa PostgreSQL, troca aqui
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecretkey"

db.init_app(app)

# -------------------------------------------------
# 🔧 Rotas
# -------------------------------------------------

# ✅ Página inicial → redireciona para Cálculo
@app.route("/")
def index():
    return redirect(url_for("calculo"))

# ✅ Aba Misturas
@app.route("/misturas")
def misturas():
    misturas = Mistura.query.all()
    return render_template("misturas.html", misturas=misturas)

@app.route("/misturas/adicionar", methods=["GET", "POST"])
def adicionar_mistura():
    if request.method == "POST":
        nome = request.form.get("nome")
        baridade = request.form.get("baridade")
        if not nome or not baridade:
            flash("Preencha todos os campos!", "danger")
        else:
            mistura = Mistura(nome=nome, baridade=float(baridade))
            db.session.add(mistura)
            db.session.commit()
            flash("Mistura adicionada com sucesso!", "success")
            return redirect(url_for("misturas"))
    return render_template("adicionar_mistura.html")

@app.route("/misturas/<int:mistura_id>/composicao", methods=["GET", "POST"])
def composicao_mistura(mistura_id):
    mistura = Mistura.query.get_or_404(mistura_id)
    materiais = Material.query.all()

    if request.method == "POST":
        # Limpar composição antiga
        Composicao.query.filter_by(mistura_id=mistura.id).delete()
        db.session.commit()

        # Guardar nova composição
        for m in materiais:
            perc = request.form.get(f"material_{m.id}")
            if perc:
                comp = Composicao(
                    mistura_id=mistura.id,
                    material_id=m.id,
                    percentagem=float(perc)
                )
                db.session.add(comp)
        db.session.commit()
        flash("Composição atualizada!", "success")
        return redirect(url_for("misturas"))

    composicao = {c.material_id: c.percentagem for c in mistura.composicoes}
    return render_template("composicao_mistura.html", mistura=mistura, materiais=materiais, composicao=composicao)

# ✅ Aba Cálculo (placeholder por enquanto)
@app.route("/calculo")
def calculo():
    misturas = Mistura.query.all()
    return render_template("calculo.html", misturas=misturas)

# -------------------------------------------------
# 🔧 Inicializar BD no primeiro arranque
# -------------------------------------------------
@app.before_request
def criar_bd():
    db.create_all()

# -------------------------------------------------
# 🔧 Início da App
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)