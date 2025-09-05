from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def calculo():
    resultado = None

    if request.method == "POST":
        # Ler os valores do formulário
        mistura = request.form["mistura"]
        espessura = float(request.form["espessura"])
        producao = float(request.form["producao"])
        distancia = float(request.form["distancia"])
        dificuldade = int(request.form["dificuldade"])
        lucro = float(request.form["lucro"])

        # Valores fictícios só para exemplo (estes virão da BD futuramente)
        custo_central = 1000
        custo_equipamentos = 2000
        custo_humanos = 1500
        custo_fabrico = 20
        custo_mistura = 80
        custo_transporte = 300
        n_ciclos = 5
        baridade = 2.4

        # Fórmula simplificada
        fixo_por_ton = (custo_central + custo_equipamentos + custo_humanos) / producao
        variavel_por_ton = custo_fabrico + custo_mistura + (custo_transporte / (30 * n_ciclos))
        custo_base = (fixo_por_ton + variavel_por_ton) * baridade
        preco_final = custo_base * (1 + lucro / 100)

        resultado = round(preco_final, 2)

    return render_template("calculo.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
