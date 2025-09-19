from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Mistura, Material, Composicao  # importa os modelos

# ✅ Listar todas as misturas
@app.route("/misturas")
def misturas():
    misturas = Mistura.query.all()
    return render_template("misturas.html", misturas=misturas)

# ✅ Adicionar nova mistura
@app.route("/misturas/adicionar", methods=["GET", "POST"])
def adicionar_mistura():
    if request.method == "POST":
        nome = request.form["nome"]
        baridade = request.form["baridade"]

        if not nome or not baridade:
            flash("Preencha todos os campos", "danger")
            return redirect(url_for("adicionar_mistura"))

        nova = Mistura(nome=nome, baridade=float(baridade))
        db.session.add(nova)
        db.session.commit()

        flash("Mistura criada com sucesso!", "success")
        return redirect(url_for("misturas"))

    return render_template("adicionar_mistura.html")

# ✅ Editar mistura (apenas nome e baridade)
@app.route("/misturas/editar/<int:id>", methods=["GET", "POST"])
def editar_mistura(id):
    mistura = Mistura.query.get_or_404(id)

    if request.method == "POST":
        mistura.nome = request.form["nome"]
        mistura.baridade = request.form["baridade"]

        db.session.commit()
        flash("Mistura atualizada!", "success")
        return redirect(url_for("misturas"))

    return render_template("adicionar_mistura.html", mistura=mistura)

# ✅ Apagar mistura
@app.route("/misturas/apagar/<int:id>")
def apagar_mistura(id):
    mistura = Mistura.query.get_or_404(id)
    db.session.delete(mistura)
    db.session.commit()
    flash("Mistura removida!", "warning")
    return redirect(url_for("misturas"))

# ✅ Definir composição da mistura
@app.route("/misturas/composicao/<int:id>", methods=["GET", "POST"])
def composicao_mistura(id):
    mistura = Mistura.query.get_or_404(id)
    materiais = Material.query.all()

    # dicionário material_id -> percentagem
    composicao = {c.material_id: c.percentagem for c in mistura.composicoes}

    if request.method == "POST":
        for m in materiais:
            campo = f"material_{m.id}"
            if campo in request.form:
                perc = float(request.form[campo]) if request.form[campo] else 0

                comp = Composicao.query.filter_by(
                    mistura_id=id, material_id=m.id
                ).first()

                if comp:
                    comp.percentagem = perc
                else:
                    comp = Composicao(
                        mistura_id=id,
                        material_id=m.id,
                        percentagem=perc
                    )
                    db.session.add(comp)

        db.session.commit()
        flash("Composição atualizada!", "success")
        return redirect(url_for("composicao_mistura", id=id))

    return render_template(
        "composicao_mistura.html",
        mistura=mistura,
        materiais=materiais,
        composicao=composicao
    )
