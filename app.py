
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'uma-chave-secreta-local')

db_url = os.getenv('DATABASE_URL')
if db_url:
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False)
    custo = db.Column(db.Float, nullable=False, default=0.0)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

class Humano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False)
    custo = db.Column(db.Float, nullable=False, default=0.0)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    preco = db.Column(db.Float, nullable=False, default=0.0)
    transporte = db.Column(db.Float, nullable=False, default=0.0)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False)
    baridade = db.Column(db.Float, nullable=False, default=1.0)

class MisturaMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey('mistura.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    percentagem = db.Column(db.Float, nullable=False, default=0.0)
    mistura = db.relationship('Mistura', backref=db.backref('componentes', cascade='all, delete-orphan'))
    material = db.relationship('Material')

class Diverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(140), nullable=False, unique=True)
    valor = db.Column(db.Float, nullable=False, default=0.0)

@app.before_request
def create_tables():
    db.create_all()
    # Diversos com valores fornecidos
    defaults = {
        'Custo Central': 880.88,
        'Custo Fabrico': 11.0,
        'Custo Camião Hora': 48.56,
        'Nciclos': 5.0
    }
    for name, val in defaults.items():
        if not Diverso.query.filter_by(nome=name).first():
            db.session.add(Diverso(nome=name, valor=val))

    # Misturas padrão
    default_mixes = [
        ('Desgaste', 1.0),
        ('Binder', 1.0),
        ('Macadame', 1.0),
        ('Argamassa', 1.0),
        ('Desgaste Subjacente', 1.0)
    ]
    for name, bar in default_mixes:
        if not Mistura.query.filter_by(nome=name).first():
            db.session.add(Mistura(nome=name, baridade=bar))
    db.session.commit()

    # Materiais pré-carregados
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

    # Composição exemplo de cada mistura
    mistura_exemplos = {
        'Desgaste': [('Brita 1 Calcário',40),('Brita 2 Calcário',40),('Areia',10),('Betume',10)],
        'Binder': [('Brita 1 Calcário',30),('Brita 2 Calcário',50),('Areia',10),('Betume',10)],
        'Macadame': [('Brita 2 Granito',60),('Pó de pedra Granito',30),('Betume',10)],
        'Argamassa': [('Areia',50),('Pó de pedra Calcário',40),('Betume',10)],
        'Desgaste Subjacente': [('Brita 1 Granito',35),('Brita 2 Granito',35),('Areia',20),('Betume',10)]
    }
    for mistura_nome, comps in mistura_exemplos.items():
        mistura = Mistura.query.filter_by(nome=mistura_nome).first()
        if mistura:
            for mat_nome, pct in comps:
                mat = Material.query.filter_by(nome=mat_nome).first()
                if mat and not MisturaMaterial.query.filter_by(mistura_id=mistura.id, material_id=mat.id).first():
                    db.session.add(MisturaMaterial(mistura_id=mistura.id, material_id=mat.id, percentagem=pct))
    db.session.commit()
