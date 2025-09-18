from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Mistura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, nullable=False, default=1.0)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('calculo'))

@app.route('/calculo')
def calculo():
    return render_template('calculo.html')

@app.route('/misturas', methods=['GET', 'POST'])
def misturas():
    if request.method == 'POST':
        nome = request.form.get('nome')
        baridade = float(request.form.get('baridade', 1.0))
        if nome:
            nova = Mistura(nome=nome, baridade=baridade)
            db.session.add(nova)
            db.session.commit()
        return redirect(url_for('misturas'))
    misturas = Mistura.query.all()
    return render_template('misturas.html', misturas=misturas)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
