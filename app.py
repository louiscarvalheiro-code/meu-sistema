from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Base de dados: PostgreSQL no Render ou SQLite local
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
db = SQLAlchemy(app)

@app.before_request
def create_tables():
    db.create_all()

# MODELOS DE EXEMPLO
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    return redirect(url_for('calculo'))

@app.route('/calculo')
def calculo():
    misturas = Mistura.query.all()
    return render_template('calculo.html', misturas=misturas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
