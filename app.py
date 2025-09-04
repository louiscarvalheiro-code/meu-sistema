from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "senha-super-secreta"

# Função para inicializar banco
def init_db():
    conn = sqlite3.connect("dados.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS valores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    valor REAL
                )""")
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario == "admin" and senha == "1234":
            session["logado"] = True
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("dados.db")
    c = conn.cursor()

    if request.method == "POST":
        valor = float(request.form["valor"])
        c.execute("INSERT INTO valores (valor) VALUES (?)", (valor,))
        conn.commit()

    c.execute("SELECT valor FROM valores ORDER BY id DESC LIMIT 1")
    ultimo = c.fetchone()
    conn.close()

    if ultimo:
        valor = ultimo[0]
        resultado = valor * 2
    else:
        valor = None
        resultado = None

    return render_template("dashboard.html", valor=valor, resultado=resultado)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
