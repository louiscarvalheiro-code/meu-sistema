
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from models import db, Material, Mistura, MisturaMaterial, Equipamento, Humano, Diverso

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'uma-chave-local')

# DB config
db_url = os.getenv('DATABASE_URL', 'sqlite:///local.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def seed_data():
    defaults = {
        'Custo Central': 880.88,
        'Custo Fabrico': 11.0,
        'Custo Camião Hora': 48.56,
        'Nciclos': 5.0
    }
    for name, val in defaults.items():
        if not Diverso.query.filter_by(nome=name).first():
            db.session.add(Diverso(nome=name, valor=val))

    default_materials = [
        ('Pó de pedra Calcário', 5.0, 2.0),
        ('Brita 1 Calcário', 6.0, 2.5),
        ('Brita 2 Calcário', 7.0, 3.0),
        ('Pó de pedra Granito', 6.5, 2.0),
        ('Brita 1 Granito', 7.5, 2.5),
        ('Brita 2 Granito', 8.0, 3.0),
        ('Filler Comercial', 3.0, 1.0),
        ('Filler Recuperado', 2.5, 1.0),
        ('Fresado', 2.0, 1.0),
        ('Areia', 4.0, 0.5),
        ('Betume', 100.0, 0.0)
    ]
    for nome, preco, transp in default_materials:
        if not Material.query.filter_by(nome=nome).first():
            db.session.add(Material(nome=nome, preco=preco, transporte=transp))
    db.session.commit()

    mistura_exemplos = {
        'Desgaste': [('Brita 1 Calcário',40),('Brita 2 Calcário',40),('Areia',10),('Betume',10)],
        'Binder': [('Brita 1 Calcário',30),('Brita 2 Calcário',50),('Areia',10),('Betume',10)],
        'Macadame': [('Brita 2 Granito',60),('Pó de pedra Granito',30),('Betume',10)],
        'Argamassa': [('Areia',50),('Pó de pedra Calcário',40),('Betume',10)],
        'Desgaste Subjacente': [('Brita 1 Granito',35),('Brita 2 Granito',35),('Areia',20),('Betume',10)]
    }
    for mistura_nome, comps in mistura_exemplos.items():
        mistura = Mistura.query.filter_by(nome=mistura_nome).first()
        if not mistura:
            mistura = Mistura(nome=mistura_nome, baridade=1.0)
            db.session.add(mistura)
            db.session.commit()
        for mat_nome, pct in comps:
            mat = Material.query.filter_by(nome=mat_nome).first()
            if mat and not MisturaMaterial.query.filter_by(mistura_id=mistura.id, material_id=mat.id).first():
                db.session.add(MisturaMaterial(mistura_id=mistura.id, material_id=mat.id, percentagem=pct))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

def custo_mistura_por_ton(mistura_id):
    custo = 0.0
    comps = MisturaMaterial.query.filter_by(mistura_id=mistura_id).all()
    for c in comps:
        mat = Material.query.get(c.material_id)
        if mat:
            custo += (c.percentagem / 100.0) * (mat.preco + mat.transporte)
    return round(custo, 6)

@app.route('/')
def index():
    return redirect(url_for('calculo'))

@app.route('/calculo', methods=['GET','POST'])
def calculo():
    misturas = Mistura.query.order_by(Mistura.nome).all()
    resultado = None
    detalhe = None
    if request.method == 'POST':
        mistura_id = int(request.form.get('mistura_id') or 0)
        espessura = float(request.form.get('espessura') or 0)
        producao = float(request.form.get('producao') or 1)
        nc = float(request.form.get('nc') or 5)
        lucro = float(request.form.get('lucro') or 0)

        cc = Diverso.query.filter_by(nome='Custo Central').first().valor
        cf = Diverso.query.filter_by(nome='Custo Fabrico').first().valor
        ct = Diverso.query.filter_by(nome='Custo Camião Hora').first().valor

        ce_hourly = db.session.query(func.coalesce(func.sum(Equipamento.custo * Equipamento.quantidade), 0)).scalar() or 0.0
        ch_hourly = db.session.query(func.coalesce(func.sum(Humano.custo * Humano.quantidade), 0)).scalar() or 0.0

        ce_daily = ce_hourly * 8.0
        ch_daily = ch_hourly * 8.0

        custo_mistura = custo_mistura_por_ton(mistura_id) if mistura_id else 0.0

        fixa_por_ton = (cc + ce_daily + ch_daily) / (producao if producao>0 else 1)
        variavel_por_ton = cf + custo_mistura + (ct / (30.0 * nc if nc>0 else 5.0))

        mistura = Mistura.query.get(mistura_id) if mistura_id else None
        bar = mistura.baridade if mistura else 1.0

        custo_unitario_por_ton = (fixa_por_ton + variavel_por_ton) * bar
        custo_unitario_final = custo_unitario_por_ton * espessura
        preco_final = custo_unitario_final * (1 + lucro / 100.0)

        resultado = round(preco_final, 4)
        detalhe = {
            'espessura': espessura,
            'producao': producao,
            'nc': nc,
            'lucro': lucro,
            'fixa_por_ton': round(fixa_por_ton,4),
            'variavel_por_ton': round(variavel_por_ton,4),
            'custo_mistura': round(custo_mistura,4),
            'baridade': bar,
            'ce_hourly': round(ce_hourly,4),
            'ch_hourly': round(ch_hourly,4),
            'ce_daily': round(ce_daily,4),
            'ch_daily': round(ch_daily,4)
        }
    return render_template('calculo.html', misturas=misturas, resultado=resultado, detalhe=detalhe)

# ... routes for other tabs simplified to keep file compact - reuse earlier code pattern ...
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
    return render_template('misturas.html', lista=lista)

@app.route('/misturas/delete/<int:id>', methods=['POST'])
def misturas_delete(id):
    item = Mistura.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Mistura removida.', 'warning')
    return redirect(url_for('misturas'))

@app.route('/misturas/<int:mistura_id>/composicao', methods=['GET','POST'])
def misturas_composicao(mistura_id):
    mistura = Mistura.query.get_or_404(mistura_id)
    materiais = Material.query.order_by(Material.nome).all()
    componentes = MisturaMaterial.query.filter_by(mistura_id=mistura_id).all()
    if request.method == 'POST':
        material_id = int(request.form.get('material_id') or 0)
        percent = float(request.form.get('percentagem') or 0)
        if material_id == 0:
            flash('Selecione um material.', 'danger')
            return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
        existing = MisturaMaterial.query.filter_by(mistura_id=mistura_id, material_id=material_id).first()
        if existing:
            flash('Material já existe na mistura. Edite a percentagem.', 'warning')
            return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
        new_total = db.session.query(func.coalesce(func.sum(MisturaMaterial.percentagem), 0.0)).filter_by(mistura_id=mistura_id).scalar() or 0.0
        new_total += percent
        if new_total > 100.0001:
            flash(f'A soma das percentagens excede 100% (total atual: {new_total}%).', 'danger')
            return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
        comp = MisturaMaterial(mistura_id=mistura_id, material_id=material_id, percentagem=percent)
        db.session.add(comp)
        db.session.commit()
        flash('Componente adicionado.', 'success')
        return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
    total_pct = db.session.query(func.coalesce(func.sum(MisturaMaterial.percentagem), 0.0)).filter_by(mistura_id=mistura_id).scalar() or 0.0
    custo_mist = custo_mistura_por_ton(mistura_id)
    return render_template('misturas_composicao.html', mistura=mistura, materiais=materiais, componentes=componentes, total_pct=total_pct, custo_mist=custo_mist)

@app.route('/misturas/<int:mistura_id>/composicao/edit/<int:comp_id>', methods=['POST'])
def misturas_composicao_edit(mistura_id, comp_id):
    comp = MisturaMaterial.query.get_or_404(comp_id)
    nova = float(request.form.get('percentagem') or 0.0)
    soma_outras = db.session.query(func.coalesce(func.sum(MisturaMaterial.percentagem), 0.0)).filter_by(mistura_id=mistura_id).scalar() - comp.percentagem
    new_total = soma_outras + nova
    if new_total > 100.0001:
        flash(f'Não é possível definir {nova}%. Soma total = {new_total}% > 100%.', 'danger')
        return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
    comp.percentagem = nova
    db.session.commit()
    flash('Percentagem atualizada.', 'success')
    return redirect(url_for('misturas_composicao', mistura_id=mistura_id))

@app.route('/misturas/<int:mistura_id>/composicao/delete/<int:comp_id>', methods=['POST'])
def misturas_composicao_delete(mistura_id, comp_id):
    comp = MisturaMaterial.query.get_or_404(comp_id)
    db.session.delete(comp)
    db.session.commit()
    flash('Componente removido.', 'warning')
    return redirect(url_for('misturas_composicao', mistura_id=mistura_id))

@app.route('/equipamentos', methods=['GET','POST'])
def equipamentos():
    if request.method == 'POST':
        nome = request.form.get('nome')
        custo = float(request.form.get('custo') or 0)
        quantidade = int(request.form.get('quantidade') or 1)
        if nome:
            db.session.add(Equipamento(nome=nome, custo=custo, quantidade=quantidade))
            db.session.commit()
            flash('Equipamento adicionado.', 'success')
        return redirect(url_for('equipamentos'))
    lista = Equipamento.query.order_by(Equipamento.nome).all()
    return render_template('equipamentos.html', lista=lista)

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
        quantidade = int(request.form.get('quantidade') or 1)
        if nome:
            db.session.add(Humano(nome=nome, custo=custo, quantidade=quantidade))
            db.session.commit()
            flash('Humano adicionado.', 'success')
        return redirect(url_for('humanos'))
    lista = Humano.query.order_by(Humano.nome).all()
    return render_template('humanos.html', lista=lista)

@app.route('/humanos/delete/<int:id>', methods=['POST'])
def humanos_delete(id):
    item = Humano.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Humano removido.', 'warning')
    return redirect(url_for('humanos'))

@app.route('/diversos', methods=['GET','POST'])
def diversos():
    if request.method == 'POST':
        nome = request.form.get('nome')
        valor = float(request.form.get('valor') or 0)
        if nome:
            item = Diverso(nome=nome, valor=valor)
            db.session.add(item)
            db.session.commit()
            flash('Diverso adicionado.', 'success')
        return redirect(url_for('diversos'))
    lista = Diverso.query.order_by(Diverso.nome).all()
    return render_template('diversos.html', lista=lista)

@app.route('/diversos/edit/<int:id>', methods=['GET','POST'])
def diversos_edit(id):
    item = Diverso.query.get_or_404(id)
    if request.method == 'POST':
        item.valor = float(request.form.get('valor') or 0)
        db.session.commit()
        flash('Valor atualizado.', 'success')
        return redirect(url_for('diversos'))
    return render_template('diversos_edit.html', item=item)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)), debug=True)
