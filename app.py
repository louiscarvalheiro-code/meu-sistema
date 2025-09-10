
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','uma-chave-secreta-local')

# DB config: use DATABASE_URL (Postgres) if present, else SQLite
db_url = os.getenv('DATABASE_URL')
if db_url:
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://','postgresql://',1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    custo = db.Column(db.Float, nullable=False, default=0.0)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    custo = db.Column(db.Float, nullable=False, default=0.0)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False, default=0.0)
    transporte = db.Column(db.Float, nullable=False, default=0.0)

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False, default=0.0)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    baridade = db.Column(db.Float, nullable=False, default=1.0)

class MisturaMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey('mistura.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    percentagem = db.Column(db.Float, nullable=False, default=0.0)
    mistura = db.relationship('Mistura', backref=db.backref('componentes', cascade='all, delete-orphan'))
    material = db.relationship('Material')

# Ensure tables exist
@app.before_request
def create_tables():
    db.create_all()

# Utils
def total_percentagem_mistura(mistura_id):
    total = db.session.query(func.coalesce(func.sum(MisturaMaterial.percentagem), 0.0)).filter_by(mistura_id=mistura_id).scalar()
    return float(total or 0.0)

def custo_mistura_por_ton(mistura_id):
    custo = 0.0
    comps = MisturaMaterial.query.filter_by(mistura_id=mistura_id).all()
    for c in comps:
        mat = c.material
        if mat:
            custo += (c.percentagem/100.0) * ((mat.preco or 0.0) + (mat.transporte or 0.0))
    return round(custo,6)

# Routes - Calculo
@app.route('/', methods=['GET','POST'])
@app.route('/calculo', methods=['GET','POST'])
def calculo():
    misturas = Mistura.query.order_by(Mistura.nome).all()
    resultado = None
    detalhe = None
    if request.method == 'POST':
        try:
            mistura_id = int(request.form.get('mistura_id') or 0)
            espessura = float(request.form.get('espessura') or 0)
            producao = float(request.form.get('producao') or 1)
            nc = float(request.form.get('nc') or 5)
            dificuldade = int(request.form.get('dificuldade') or 1)
            lucro = float(request.form.get('lucro') or 0)

            # Cc = Custo Central diário (Diverso named 'Custo Central')
            cc_row = Diverso.query.filter_by(nome='Custo Central').first()
            Cc = cc_row.valor if cc_row else 0.0

            # Cf = Custo de fabrico por tonelada (Diverso named 'Custo Fabrico')
            cf_row = Diverso.query.filter_by(nome='Custo Fabrico').first()
            Cf = cf_row.valor if cf_row else 0.0

            soma_equip = db.session.query(func.coalesce(func.sum(Equipamento.custo * Equipamento.quantidade),0)).scalar()
            soma_humanos = db.session.query(func.coalesce(func.sum(Humano.custo * Humano.quantidade),0)).scalar()

            custo_mistura = custo_mistura_por_ton(mistura_id) if mistura_id else 0.0

            # Custo transporte total from Diverso named 'Custo Transporte' if exists
            ct_row = Diverso.query.filter_by(nome='Custo Transporte').first()
            CustoTransporte = ct_row.valor if ct_row else 0.0

            fixa_por_ton = (Cc + soma_equip + soma_humanos) / (producao if producao>0 else 1)
            variavel_por_ton = Cf + custo_mistura + (CustoTransporte / (30.0 * nc if nc>0 else 5.0))

            mistura = Mistura.query.get(mistura_id) if mistura_id else None
            bar = mistura.baridade if mistura else 1.0

            custo_unitario_por_ton = (fixa_por_ton + variavel_por_ton) * bar
            # multiply by espessura as requested
            custo_unitario_final = custo_unitario_por_ton * espessura
            preco_final = custo_unitario_final * (1 + lucro/100.0)

            resultado = round(preco_final,2)
            detalhe = {
                'espessura': espessura,
                'producao': producao,
                'nc': nc,
                'lucro': lucro,
                'fixa_por_ton': round(fixa_por_ton,3),
                'variavel_por_ton': round(variavel_por_ton,3),
                'custo_mistura': round(custo_mistura,3),
                'baridade': bar,
                'soma_equip': round(soma_equip,3),
                'soma_humanos': round(soma_humanos,3)
            }

        except Exception as e:
            flash(f'Erro no cálculo: {e}', 'danger')

    return render_template('calculo.html', misturas=misturas, resultado=resultado, detalhe=detalhe)

# Routes - Equipamentos
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

# Routes - Humanos
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

# Routes - Materiais
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

# Routes - Misturas & composição
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
        new_total = total_percentagem_mistura(mistura_id) + percent
        if new_total > 100.0001:
            flash(f'A soma das percentagens excede 100% (total atual: {new_total}%).', 'danger')
            return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
        comp = MisturaMaterial(mistura_id=mistura_id, material_id=material_id, percentagem=percent)
        db.session.add(comp)
        db.session.commit()
        flash('Componente adicionado.', 'success')
        return redirect(url_for('misturas_composicao', mistura_id=mistura_id))
    total_pct = total_percentagem_mistura(mistura_id)
    custo_mist = custo_mistura_por_ton(mistura_id)
    return render_template('misturas_composicao.html', mistura=mistura, materiais=materiais, componentes=componentes, total_pct=total_pct, custo_mist=custo_mist)

@app.route('/misturas/<int:mistura_id>/composicao/edit/<int:comp_id>', methods=['POST'])
def misturas_composicao_edit(mistura_id, comp_id):
    comp = MisturaMaterial.query.get_or_404(comp_id)
    nova = float(request.form.get('percentagem') or 0.0)
    soma_outras = total_percentagem_mistura(mistura_id) - comp.percentagem
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

# Routes - Diversos
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

@app.route('/diversos/delete/<int:id>', methods=['POST'])
def diversos_delete(id):
    item = Diverso.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Diverso removido.', 'warning')
    return redirect(url_for('diversos'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)), debug=True)
