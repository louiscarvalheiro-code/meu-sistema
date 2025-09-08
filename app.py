
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'uma-chave-secreta-123'
db = SQLAlchemy(app)

class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    custo = db.Column(db.Float, nullable=False)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    custo = db.Column(db.Float, nullable=False)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False, default=0.0)
    transporte = db.Column(db.Float, nullable=False, default=0.0)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    baridade = db.Column(db.Float, nullable=False, default=1.0)

class MisturaComponente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey('mistura.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    percentagem = db.Column(db.Float, nullable=False, default=0.0)
    mistura = db.relationship('Mistura', backref=db.backref('componentes', cascade='all, delete-orphan'))
    material = db.relationship('Material')

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False)

@app.before_first_request
def create_tables():
    db.create_all()
    if Mistura.query.count() == 0:
        m1 = Mistura(nome='Desgaste', baridade=2.4)
        m2 = Mistura(nome='Binder', baridade=2.0)
        m3 = Mistura(nome='Macadame', baridade=1.8)
        m4 = Mistura(nome='Argamassa', baridade=1.6)
        m5 = Mistura(nome='Desgaste Subjacente', baridade=2.2)
        db.session.add_all([m1,m2,m3,m4,m5])
        db.session.commit()

@app.route('/', methods=['GET','POST'])
def calculo():
    resultado = None
    misturas = Mistura.query.order_by(Mistura.nome).all()
    if request.method == 'POST':
        mistura_id = int(request.form.get('mistura_id') or 0)
        espessura = float(request.form.get('espessura') or 0)
        producao = float(request.form.get('producao') or 1)
        distancia = float(request.form.get('distancia') or 0)
        dificuldade = int(request.form.get('dificuldade') or 1)
        lucro = float(request.form.get('lucro') or 0)

        custo_central_row = Diverso.query.filter_by(nome='Custo Central').first()
        custo_fabrico_row = Diverso.query.filter_by(nome='Custo Fabrico').first()
        custo_central = custo_central_row.valor if custo_central_row else 0.0
        custo_fabrico = custo_fabrico_row.valor if custo_fabrico_row else 0.0

        soma_equip = db.session.query(func.coalesce(func.sum(Equipamento.custo),0)).scalar()
        soma_humanos = db.session.query(func.coalesce(func.sum(Humano.custo),0)).scalar()
        custo_mistura = 0.0
        custo_transporte = 0.0
        baridade = 1.0
        if mistura_id:
            mistura = Mistura.query.get(mistura_id)
            if mistura:
                baridade = mistura.baridade or 1.0
                for comp in mistura.componentes:
                    mat = comp.material
                    pct = (comp.percentagem or 0.0)/100.0
                    preco_material = (mat.preco or 0.0)
                    preco_transp = (mat.transporte or 0.0)
                    custo_mistura += preco_material * pct
                    custo_transporte += preco_transp * pct

        N = 5
        producao = producao if producao>0 else 1

        fixo_por_ton = (custo_central + soma_equip + soma_humanos) / producao
        variavel_por_ton = custo_fabrico + custo_mistura + (custo_transporte / (30 * N))
        custo_base = (fixo_por_ton + variavel_por_ton) * baridade
        preco_final = custo_base * (1 + lucro/100.0)

        resultado = {
            'preco_final': round(preco_final,2),
            'fixo_por_ton': round(fixo_por_ton,3),
            'variavel_por_ton': round(variavel_por_ton,3),
            'baridade': baridade,
            'custo_mistura': round(custo_mistura,3),
            'custo_transporte': round(custo_transporte,3),
            'soma_equip': round(soma_equip,3),
            'soma_humanos': round(soma_humanos,3)
        }

    return render_template('calculo.html', resultado=resultado, misturas=misturas)

@app.route('/equipamentos', methods=['GET','POST'])
def equipamentos():
    if request.method == 'POST':
        nome = request.form.get('nome')
        custo = float(request.form.get('custo') or 0)
        if nome:
            db.session.add(Equipamento(nome=nome, custo=custo))
            db.session.commit()
            flash('Equipamento adicionado.', 'success')
        return redirect(url_for('equipamentos'))
    lista = Equipamento.query.order_by(Equipamento.nome).all()
    return render_template('equipamentos.html', lista=lista)

@app.route('/equipamentos/edit/<int:id>', methods=['GET','POST'])
def equipamentos_edit(id):
    item = Equipamento.query.get_or_404(id)
    if request.method == 'POST':
        item.nome = request.form.get('nome')
        item.custo = float(request.form.get('custo') or 0)
        db.session.commit()
        flash('Equipamento atualizado.', 'success')
        return redirect(url_for('equipamentos'))
    return render_template('equipamentos_edit.html', item=item)

@app.route('/equipamentos/delete/<int:id>', methods=['POST'])
def equipamentos_delete(id):
    item = Equipamento.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Equipamento removido.', 'warning')
    return redirect(url_for('equipamentos'))

@app.route('/humanos', methods=['GET','POST'])
def humanos():
    if request.method == 'POST':
        nome = request.form.get('nome')
        custo = float(request.form.get('custo') or 0)
        if nome:
            db.session.add(Humano(nome=nome, custo=custo))
            db.session.commit()
            flash('Humano adicionado.', 'success')
        return redirect(url_for('humanos'))
    lista = Humano.query.order_by(Humano.nome).all()
    return render_template('humanos.html', lista=lista)

@app.route('/humanos/edit/<int:id>', methods=['GET','POST'])
def humanos_edit(id):
    item = Humano.query.get_or_404(id)
    if request.method == 'POST':
        item.nome = request.form.get('nome')
        item.custo = float(request.form.get('custo') or 0)
        db.session.commit()
        flash('Humano atualizado.', 'success')
        return redirect(url_for('humanos'))
    return render_template('humanos_edit.html', item=item)

@app.route('/humanos/delete/<int:id>', methods=['POST'])
def humanos_delete(id):
    item = Humano.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Humano removido.', 'warning')
    return redirect(url_for('humanos'))

@app.route('/materiais', methods=['GET','POST'])
def materiais():
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = float(request.form.get('preco') or 0)
        transporte = float(request.form.get('transporte') or 0)
        if nome:
            db.session.add(Material(nome=nome, preco=preco, transporte=transporte))
            db.session.commit()
            flash('Material adicionado.', 'success')
        return redirect(url_for('materiais'))
    lista = Material.query.order_by(Material.nome).all()
    return render_template('materiais.html', lista=lista)

@app.route('/materiais/edit/<int:id>', methods=['GET','POST'])
def materiais_edit(id):
    item = Material.query.get_or_404(id)
    if request.method == 'POST':
        item.nome = request.form.get('nome')
        item.preco = float(request.form.get('preco') or 0)
        item.transporte = float(request.form.get('transporte') or 0)
        db.session.commit()
        flash('Material atualizado.', 'success')
        return redirect(url_for('materiais'))
    return render_template('materiais_edit.html', item=item)

@app.route('/materiais/delete/<int:id>', methods=['POST'])
def materiais_delete(id):
    item = Material.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Material removido.', 'warning')
    return redirect(url_for('materiais'))

@app.route('/misturas', methods=['GET','POST'])
def misturas():
    if request.method == 'POST':
        nome = request.form.get('nome')
        bar = float(request.form.get('baridade') or 1.0)
        if nome:
            db.session.add(Mistura(nome=nome, baridade=bar))
            db.session.commit()
            flash('Mistura adicionada.', 'success')
        return redirect(url_for('misturas'))
    lista = Mistura.query.order_by(Mistura.nome).all()
    materiais = Material.query.order_by(Material.nome).all()
    return render_template('misturas.html', lista=lista, materiais=materiais)

@app.route('/misturas/edit/<int:id>', methods=['GET','POST'])
def misturas_edit(id):
    item = Mistura.query.get_or_404(id)
    if request.method == 'POST':
        item.nome = request.form.get('nome')
        item.baridade = float(request.form.get('baridade') or 1.0)
        db.session.commit()
        flash('Mistura atualizada.', 'success')
        return redirect(url_for('misturas'))
    materiais = Material.query.order_by(Material.nome).all()
    return render_template('misturas_edit.html', item=item, materiais=materiais)

@app.route('/misturas/delete/<int:id>', methods=['POST'])
def misturas_delete(id):
    item = Mistura.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Mistura removida.', 'warning')
    return redirect(url_for('misturas'))

@app.route('/mistura_component/add', methods=['POST'])
def mistura_component_add():
    mistura_id = int(request.form.get('mistura_id') or 0)
    material_id = int(request.form.get('material_id') or 0)
    percent = float(request.form.get('percentagem') or 0)
    if mistura_id and material_id:
        db.session.add(MisturaComponente(mistura_id=mistura_id, material_id=material_id, percentagem=percent))
        db.session.commit()
        flash('Componente adicionado.', 'success')
    return redirect(url_for('misturas_edit', id=mistura_id))

@app.route('/mistura_component/delete/<int:id>', methods=['POST'])
def mistura_component_delete(id):
    comp = MisturaComponente.query.get_or_404(id)
    mid = comp.mistura_id
    db.session.delete(comp)
    db.session.commit()
    flash('Componente removido.', 'warning')
    return redirect(url_for('misturas_edit', id=mid))

@app.route('/diversos', methods=['GET','POST'])
def diversos():
    if request.method == 'POST':
        nome = request.form.get('nome')
        valor = float(request.form.get('valor') or 0)
        if nome:
            db.session.add(Diverso(nome=nome, valor=valor))
            db.session.commit()
            flash('Diverso adicionado.', 'success')
        return redirect(url_for('diversos'))
    lista = Diverso.query.order_by(Diverso.nome).all()
    return render_template('diversos.html', lista=lista)

@app.route('/diversos/edit/<int:id>', methods=['GET','POST'])
def diversos_edit(id):
    item = Diverso.query.get_or_404(id)
    if request.method == 'POST':
        item.nome = request.form.get('nome')
        item.valor = float(request.form.get('valor') or 0)
        db.session.commit()
        flash('Diverso atualizado.', 'success')
        return redirect(url_for('diversos'))
    return render_template('diversos_edit.html', item=item)

@app.route('/diversos/delete/<int:id>', methods=['POST'])
def diversos_delete(id):
    item = Diverso.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Diverso removido.', 'warning')
    return redirect(url_for('diversos'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
